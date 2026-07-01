# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.6 — CRSUBMIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import CRASHING_REFINE
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.crash_refine_form import recalc_document_lines
from millitrix.utils.production_calc import (
	input_grain_cost,
	input_grain_qty,
	input_total_weight,
	output_product_value,
	wastage_kg,
	westage_kg_per_bag,
)
from millitrix.utils.stock import (
	apply_stock_in,
	apply_stock_out,
	get_in_store_item_name,
	mark_posted,
	mark_unposted,
)
from millitrix.utils.stock_key import StockKey

_DOCTYPEID = CRASHING_REFINE


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = _DOCTYPEID
	if doc.mill_id and not doc.location_id:
		doc.location_id = doc.mill_id
	validate_fiscal_period(doc.crdate)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows

	strip_blank_child_rows(doc, "inputs", "Crash Refine Input")
	strip_blank_child_rows(doc, "outputs", "Crash Refine Output")
	if not doc.inputs:
		frappe.throw(_("Add at least one input line"))
	if not doc.outputs:
		frappe.throw(_("Add at least one output line"))
	recalc_document_lines(doc)
	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)
	for line in doc.inputs or []:
		if flt(line.bagqty) > 0 and not flt(line.dip):
			frappe.throw(_("Enter Dip on input line for item {0}").format(line.critem or ""))
	for line in doc.inputs or []:
		per = flt(line.bagweight)
		westage = westage_kg_per_bag(line)
		if per > 0 and westage > per + 1e-9:
			frappe.throw(
				_("Westage ({0} kg/bag) cannot exceed Per Bag ({1}) for item {2}").format(
					westage, per, line.critem
				)
			)
	_validate_input_stock(doc)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "crashid")
	_apply_stock_movements(doc)
	batch = _build_production_transactions(doc, doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=_DOCTYPEID,
		documentid=doc_key,
		vouchdate=doc.crdate,
		narration=f"Crashing Refine {doc.crashid}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
	doc_key = resolve_document_key(doc, "crashid")
	_reverse_stock_movements(doc)
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": _DOCTYPEID, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, _DOCTYPEID, doc_key)
	mark_unposted(doc)


def _grain_key(line) -> StockKey:
	return StockKey(storeid=line.storeid, itemcode=line.critem, bags_are="PU")


def _filled_bag_key(line) -> StockKey | None:
	if not line.crbagid or flt(line.bagqty) <= 0:
		return None
	return StockKey(
		storeid=line.storeid,
		itemcode=line.crbagid,
		bagitemcode=line.critem,
		bags_are="PU",
	)


def _empty_bag_key(line) -> StockKey | None:
	if not line.crbagid or flt(line.bagqty) <= 0:
		return None
	return StockKey(storeid=line.storeid, itemcode=line.crbagid, bags_are="PU")


def _dust_key(line) -> StockKey | None:
	if not line.dustitemid or wastage_kg(line) <= 0:
		return None
	return StockKey(storeid=line.storeid, itemcode=line.dustitemid, bags_are="PU")


def _validate_input_stock(doc):
	for line in doc.inputs or []:
		qty = input_total_weight(line)
		if qty > 0:
			name = get_in_store_item_name(_grain_key(line))
			stock = flt(frappe.db.get_value("Stock In Hand", name, "stock_in_hand")) if name else 0
			if qty > stock + 1e-9:
				frappe.throw(
					_("Insufficient grain stock for {0}. Available {1}, required {2}").format(
						line.critem, stock, qty
					)
				)
		bkey = _filled_bag_key(line)
		if bkey and flt(line.bagqty) > 0:
			name = get_in_store_item_name(bkey)
			stock = flt(frappe.db.get_value("Stock In Hand", name, "stock_in_hand")) if name else 0
			if flt(line.bagqty) > stock + 1e-9:
				frappe.throw(
					_("Insufficient bag stock for {0}. Available {1}, required {2}").format(
						line.crbagid, stock, line.bagqty
					)
				)


def _apply_stock_movements(doc):
	for line in doc.inputs or []:
		qty = input_grain_qty(line)
		if qty > 0:
			apply_stock_out(_grain_key(line), qty, movement_date=doc.crdate, check_reserved=False)
		filled_bkey = _filled_bag_key(line)
		empty_bkey = _empty_bag_key(line)
		if filled_bkey:
			apply_stock_out(filled_bkey, flt(line.bagqty), movement_date=doc.crdate, check_reserved=False)
		if empty_bkey:
			apply_stock_in(
				empty_bkey,
				flt(line.bagqty),
				rate=flt(line.bagrate),
				movement_date=doc.crdate,
			)
		dkey = _dust_key(line)
		if dkey:
			apply_stock_in(
				dkey,
				wastage_kg(line),
				rate=flt(line.dust_rate),
				movement_date=doc.crdate,
			)

	for line in doc.outputs or []:
		if flt(line.weight) > 0:
			apply_stock_in(
				StockKey(storeid=line.storeid, itemcode=line.proditem, bags_are="PU"),
				flt(line.weight),
				rate=flt(line.rate),
				movement_date=doc.crdate,
			)


def _reverse_stock_movements(doc):
	for line in doc.inputs or []:
		qty = input_grain_qty(line)
		if qty > 0:
			apply_stock_in(_grain_key(line), qty, rate=flt(line.rate), movement_date=doc.crdate)
		filled_bkey = _filled_bag_key(line)
		empty_bkey = _empty_bag_key(line)
		if filled_bkey:
			apply_stock_in(filled_bkey, flt(line.bagqty), rate=flt(line.bagrate), movement_date=doc.crdate)
		if empty_bkey:
			apply_stock_out(
				empty_bkey,
				flt(line.bagqty),
				movement_date=doc.crdate,
				check_reserved=False,
			)
		dkey = _dust_key(line)
		if dkey:
			apply_stock_out(dkey, wastage_kg(line), movement_date=doc.crdate, check_reserved=False)

	for line in doc.outputs or []:
		if flt(line.weight) > 0:
			apply_stock_out(
				StockKey(storeid=line.storeid, itemcode=line.proditem, bags_are="PU"),
				flt(line.weight),
				movement_date=doc.crdate,
				check_reserved=False,
			)


def _build_production_transactions(doc, doc_key: str | None = None) -> DocTranBatch:
	doc_key = doc_key or resolve_document_key(doc, "crashid")
	batch = DocTranBatch(doc.location_id, _DOCTYPEID, doc_key)
	item_stock_gl = get_setting_account("Item Stock GL")
	trade_purchase = get_setting_account("Trade Purchase")

	input_total = 0.0
	for line in doc.inputs or []:
		cost = input_grain_cost(line) + flt(line.bagqty) * flt(line.bagrate)
		if cost > 0:
			input_total += cost
			batch.cr(
				trade_purchase,
				cost,
				itemcode=line.critem,
				detail=f"CR input {doc.crashid} — {line.critem}",
			)

	output_total = 0.0
	for line in doc.outputs or []:
		val = output_product_value(line)
		if val > 0:
			output_total += val
			batch.dr(
				item_stock_gl,
				val,
				itemcode=line.proditem,
				detail=f"CR output {doc.crashid} — {line.proditem}",
			)

	diff = flt(output_total - input_total)
	if abs(diff) > 0.01:
		income_summary = get_setting_account("Income Summary")
		if diff > 0:
			batch.cr(income_summary, diff, detail=f"Production gain {doc.crashid}")
		else:
			batch.dr(income_summary, abs(diff), detail=f"Production loss {doc.crashid}")

	return batch
