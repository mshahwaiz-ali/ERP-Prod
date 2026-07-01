# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.3 — PISUBMIT

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.trading.gate_pass_from_invoice import ensure_gate_pass_from_invoice, remove_gate_pass_for_invoice
from millitrix.utils.bardana_gl import append_bardana_gl
from millitrix.utils.field_normalizers import is_yes, order_status_label
from millitrix.utils.trading_stock_keys import purchase_bardana_key, trading_grain_key
from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import PURCHASE_INVOICE
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.invoice_calc import line_weight_qty, recalc_invoice_lines, grain_moving_rate
from millitrix.utils.order_balance import (
	SIDE_PURCHASE,
	open_truck_qty_for_order,
	projected_open_truck_qty,
	get_order_for_update,
)
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import apply_stock_in, mark_posted, mark_unposted


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = PURCHASE_INVOICE
	validate_fiscal_period(doc.invdate)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows

	strip_blank_child_rows(doc, "details", "Purchase Invoice Detail")
	if not doc.details:
		frappe.throw(_("Add at least one invoice line"))
	from millitrix.utils.item_price import apply_price_list_to_invoice

	apply_price_list_to_invoice(doc, is_purchase=True)
	recalc_invoice_lines(doc, is_purchase=True)
	_validate_purchase_order_balance(doc)


def _validate_purchase_order_balance(doc) -> None:
	"""Each detail line = one truck; cannot exceed PO open balance."""
	po_trucks: dict[str, int] = defaultdict(int)
	for line in doc.details or []:
		if line.ponumber:
			po_trucks[line.ponumber] += 1

	exclude = doc.name if not doc.is_new() else None
	for ponumber, truck_count in po_trucks.items():
		open_qty = open_truck_qty_for_order(
			ponumber, SIDE_PURCHASE, exclude_invoice=exclude
		)
		if truck_count > open_qty + 1e-9:
			frappe.throw(
				_("PO {0} open truck qty exceeded (remaining {1})").format(ponumber, open_qty)
			)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "purchinvno")
	_update_purchase_orders(doc)
	_apply_stock_in(doc)
	ensure_gate_pass_from_invoice(doc, gptype="IN", party_field="supplierid", is_purchase=True)
	batch = _build_doc_transactions(doc, doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.invdate,
		narration=f"Purchase Invoice {doc.purchinvno} — {doc.supplierid}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _update_purchase_orders(doc):
	po_trucks: dict[str, int] = defaultdict(int)
	po_weight: dict[str, float] = defaultdict(float)
	for line in doc.details or []:
		if not line.ponumber:
			continue
		po_trucks[line.ponumber] += 1
		po_weight[line.ponumber] += flt(line.netweight)

	for ponumber, truck_count in po_trucks.items():
		po = get_order_for_update(ponumber, SIDE_PURCHASE)
		open_qty = open_truck_qty_for_order(po, SIDE_PURCHASE, exclude_invoice=doc.name)
		if truck_count > open_qty + 1e-9:
			frappe.throw(
				_("PO {0} open truck qty exceeded (remaining {1})").format(ponumber, open_qty)
			)
		new_received = flt(po.truckreceived) + truck_count
		new_weight = flt(po.weightreceived) + po_weight[ponumber]
		new_status = order_status_label(
			"CO"
			if projected_open_truck_qty(po, SIDE_PURCHASE, fulfilled=new_received) <= 0
			else "IP"
		)
		frappe.db.set_value(
			"Purchase Order",
			ponumber,
			{
				"truckreceived": new_received,
				"weightreceived": new_weight,
				"delicompdate": doc.invdate,
				"status": new_status,
			},
			update_modified=False,
		)


def _reverse_purchase_orders(doc):
	for line in doc.details or []:
		if not line.ponumber:
			continue
		po = frappe.get_doc("Purchase Order", line.ponumber)
		new_received = max(0, flt(po.truckreceived) - 1)
		new_weight = max(0, flt(po.weightreceived) - flt(line.netweight))
		new_status = order_status_label("IP" if new_received > 0 else "IN")
		frappe.db.set_value(
			"Purchase Order",
			line.ponumber,
			{"truckreceived": new_received, "weightreceived": new_weight, "status": new_status},
			update_modified=False,
		)


def _grain_key(doc, line):
	return trading_grain_key(itemcode=doc.itemcode, storeid=line.storeid)


def _bardana_key(doc, line):
	return purchase_bardana_key(doc, line)


def _apply_stock_in(doc):
	for line in doc.details or []:
		qty = line_weight_qty(line, doc.kantatype, is_purchase=True, header=doc)
		if qty > 0:
			apply_stock_in(
				_grain_key(doc, line),
				qty,
				rate=grain_moving_rate(line, doc, is_purchase=True),
				movement_date=doc.invdate,
			)
		bkey = _bardana_key(doc, line)
		if bkey:
			apply_stock_in(
				bkey,
				flt(line.bagqty),
				rate=flt(line.bagrate),
				movement_date=doc.invdate,
				bagweight=flt(line.bagweight) or None,
			)


def _reverse_stock(doc):
	from millitrix.utils.stock import apply_stock_out

	for line in doc.details or []:
		qty = line_weight_qty(line, doc.kantatype, is_purchase=True, header=doc)
		if qty > 0:
			apply_stock_out(_grain_key(doc, line), qty, movement_date=doc.invdate, check_reserved=False)
		bkey = _bardana_key(doc, line)
		if bkey:
			apply_stock_out(bkey, flt(line.bagqty), movement_date=doc.invdate, check_reserved=False)


def _build_doc_transactions(doc, doc_key: str | None = None) -> DocTranBatch:
	batch = DocTranBatch(
		doc.location_id, doc.doctypeid, doc_key or resolve_document_key(doc, "purchinvno")
	)
	trade_purchase = get_setting_account("Trade Purchase")
	brokery_exp = get_setting_account("Brokery Exp")
	party_brokery = get_setting_account("Party Brokery")
	cartage_exp = get_setting_account("Purchase Cartage Exp")
	cash_acc = get_setting_account("Cash")
	supplier_acc = get_party_accid(doc.supplierid)

	trucks: dict[str, list] = defaultdict(list)
	for line in doc.details or []:
		trucks[line.truckno or str(line.idx)].append(line)

	for truckno, lines in trucks.items():
		payable_total = 0.0
		cartage = 0.0
		brokery = 0.0
		truck_adv = 0.0
		detail_parts = []

		for line in lines:
			net = flt(line.netweight)
			payable_total += flt(line.totalamnt)
			cartage += flt(line.cartage)
			brokery += flt(line.brokeramnt)
			truck_adv += flt(line.truckadv)
			detail_parts.append(f"{doc.itemcode}, truck.# {truckno} Wgt:{net} @{line.rate}")

		detail = "; ".join(detail_parts)
		bag_total = append_bardana_gl(batch, lines, doc, is_purchase=True, truckno=truckno)
		brokery_dr_supplier = is_yes(doc.brokery_dr_supplier)
		trade_dr = payable_total - bag_total
		if brokery > 0:
			trade_dr -= brokery
		supplier_cr = payable_total - brokery if brokery_dr_supplier and brokery > 0 else payable_total

		batch.dr(trade_purchase, trade_dr, itemcode=doc.itemcode, detail=detail)
		batch.cr(supplier_acc, supplier_cr, partyid=doc.supplierid, detail=detail)

		if cartage > 0:
			batch.dr(cartage_exp, cartage, detail=f"Tran Kiraya {truckno}")
			batch.cr(supplier_acc, cartage, partyid=doc.supplierid, detail="Cartage")
		if brokery > 0:
			batch.dr(brokery_exp, brokery, detail=f"Tran Brokery {truckno}")
			if brokery_dr_supplier:
				batch.cr(party_brokery, brokery, detail="Party Brokery DR Supplier")
			else:
				batch.cr(supplier_acc, brokery, partyid=doc.supplierid, detail="Brokery payable")
		if truck_adv > 0:
			batch.dr(cash_acc, truck_adv, detail="Paid Adv Kiraya", bnkcash_gl=1)
			batch.cr(supplier_acc, truck_adv, partyid=doc.supplierid, detail="Adv Kiraya")

	return batch
