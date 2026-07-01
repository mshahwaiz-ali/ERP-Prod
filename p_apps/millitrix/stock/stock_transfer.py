# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.6 — TNSUBMIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import STOCK_TRANSFER
from millitrix.utils.fiscal import validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.stock import (
	apply_stock_in,
	apply_stock_out,
	check_bag_stock,
	line_grain_qty,
	mark_posted,
	mark_unposted,
)
from millitrix.utils.stock_key import StockKey


def _grain_key(doc, line) -> StockKey:
	return StockKey(
		storeid=doc.fromstoreid,
		itemcode=doc.itemcode,
		partyid=None,
		bags_are="PU",
	)


def _bardana_key(doc, line) -> StockKey | None:
	if not line.bagid:
		return None
	bagitemcode = None if (line.emptybags or "").upper() in ("Y", "YES") else line.bagid
	return StockKey(
		storeid=doc.fromstoreid,
		itemcode=line.bagid,
		bagitemcode=bagitemcode,
		partyid=doc.partyid or None,
		bags_are=line.bags_are or None,
	)


def _dest_bardana_key(doc, line) -> StockKey | None:
	if not line.bagid:
		return None
	bagitemcode = None if (line.emptybags or "").upper() in ("Y", "YES") else line.bagid
	return StockKey(
		storeid=line.tostoreid,
		itemcode=line.bagid,
		bagitemcode=bagitemcode,
		partyid=doc.partyid or None,
		bags_are=line.bags_are or None,
	)


def validate(doc, method=None):
	validate_fiscal_period(doc.tdate)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows
	from millitrix.utils.stock_transfer_calc import recalc_transfer_document

	strip_blank_child_rows(doc, "details", "Stock Transfer Detail")
	if not doc.details:
		frappe.throw(_("Add at least one transfer detail line"))

	recalc_transfer_document(doc)

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)

	for line in doc.details:
		grain_qty = line_grain_qty(line)
		if doc.itemcode and grain_qty > 0:
			key = _grain_key(doc, line)
			from millitrix.utils.reserved_stock import get_reserved_qty
			from millitrix.utils.stock import get_in_store_item_name

			name = get_in_store_item_name(key)
			stock = flt(frappe.db.get_value("Stock In Hand", name, "stock_in_hand")) if name else 0
			reserved = get_reserved_qty(
				key, exclude_doctype="Stock Transfer Note", exclude_name=doc.name if doc.name else None
			)
			if grain_qty > stock - reserved + 1e-9:
				frappe.throw(
					_("Insufficient stock at from-store for {0}").format(doc.itemcode)
				)
		if line.bagid and flt(line.bagqty) > 0:
			bkey = _bardana_key(doc, line)
			if bkey:
				check_bag_stock(
					bkey,
					flt(line.bagqty),
					exclude_doctype="Stock Transfer Note",
					exclude_name=doc.name if doc.name else None,
				)


def on_submit(doc, method=None):
	for line in doc.details:
		grain_qty = line_grain_qty(line)
		dest_key = StockKey(
			storeid=line.tostoreid,
			itemcode=doc.itemcode,
			partyid=None,
			bags_are="PU",
		)
		if doc.itemcode and grain_qty > 0:
			src = _grain_key(doc, line)
			apply_stock_out(src, grain_qty, movement_date=doc.tdate, check_reserved=False)
			apply_stock_in(
				dest_key,
				grain_qty,
				rate=flt(line.rate),
				movement_date=doc.tdate,
			)

		if line.bagid and flt(line.bagqty) > 0:
			src_b = _bardana_key(doc, line)
			dst_b = _dest_bardana_key(doc, line)
			if src_b and dst_b:
				bqty = flt(line.bagqty)
				bw = flt(line.bagweight) or None
				apply_stock_out(src_b, bqty, movement_date=doc.tdate, check_reserved=False)
				apply_stock_in(
					dst_b,
					bqty,
					rate=flt(line.bagrate),
					movement_date=doc.tdate,
					bagweight=bw,
				)
	_post_cartage_gl(doc)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _cartage_total(doc) -> float:
	return sum(flt(line.cartage) for line in doc.details or [])


def _post_cartage_gl(doc) -> None:
	cartage_total = _cartage_total(doc)
	if cartage_total <= 0:
		return
	doctypeid = doc.doctypeid or STOCK_TRANSFER
	doc_key = resolve_document_key(doc, "transferno")
	batch = DocTranBatch(doc.location_id, doctypeid, doc_key)
	cartage_acc = get_setting_account("Stock Movement Cartage")
	cash_acc = get_setting_account("Cash")
	batch.dr(cartage_acc, cartage_total, detail=f"Transfer {doc.transferno} cartage")
	batch.cr(cash_acc, cartage_total, detail="Transfer cartage paid", bnkcash_gl=1)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doctypeid,
		documentid=doc_key,
		vouchdate=doc.tdate,
		narration=f"Stock Transfer Note {doc.transferno} cartage",
	)


def _reverse_cartage_gl(doc) -> None:
	if _cartage_total(doc) <= 0:
		return
	doctypeid = doc.doctypeid or STOCK_TRANSFER
	doc_key = resolve_document_key(doc, "transferno")
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": doctypeid, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, doctypeid, doc_key)
