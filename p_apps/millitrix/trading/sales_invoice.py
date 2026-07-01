# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.2 — SISUBMIT

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.trading.gate_pass_from_invoice import ensure_gate_pass_from_invoice, remove_gate_pass_for_invoice
from millitrix.utils.bardana_gl import append_bardana_gl, skip_bardana_stock_check
from millitrix.utils.field_normalizers import is_yes, order_status_label
from millitrix.utils.trading_stock_keys import sales_bardana_key, trading_grain_key
from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import SALES_INVOICE
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.invoice_calc import line_weight_qty, recalc_invoice_lines
from millitrix.utils.order_balance import (
	SIDE_SALES,
	open_truck_qty_for_order,
	projected_open_truck_qty,
	get_order_for_update,
)
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.reserved_stock import get_reserved_qty
from millitrix.utils.stock import (
	apply_stock_in,
	apply_stock_out,
	check_bag_stock,
	get_in_store_item_name,
	mark_posted,
	mark_unposted,
)


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = SALES_INVOICE
	validate_fiscal_period(doc.invdate)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows

	strip_blank_child_rows(doc, "details", "Sales Invoice Detail")
	if not doc.details:
		frappe.throw(_("Add at least one invoice line"))
	from millitrix.utils.item_price import apply_price_list_to_invoice

	apply_price_list_to_invoice(doc, is_purchase=False)
	recalc_invoice_lines(doc, is_purchase=False)
	_validate_out_stock(doc)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "salesinvno")
	_update_sales_orders(doc)
	_apply_stock_out(doc)
	ensure_gate_pass_from_invoice(doc, gptype="OUT", party_field="customerid", is_purchase=False)
	batch = _build_doc_transactions(doc, doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.invdate,
		narration=f"Sales Invoice {doc.salesinvno} — {doc.customerid}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _validate_out_stock(doc):
	for line in doc.details or []:
		grain_qty = line_weight_qty(line, doc.kantatype)
		if doc.itemcode and grain_qty > 0:
			key = _grain_key(doc, line)
			name = get_in_store_item_name(key)
			stock = flt(frappe.db.get_value("Stock In Hand", name, "stock_in_hand")) if name else 0
			reserved = get_reserved_qty(
				key,
				exclude_doctype=SALES_INVOICE,
				exclude_name=doc.name if doc.name else None,
			)
			if grain_qty > stock - reserved + 1e-9:
				frappe.throw(
					_("Insufficient grain stock for {0}. Available {1}, required {2}").format(
						doc.itemcode, stock - reserved, grain_qty
					)
				)
		if line.bagid and flt(line.bagqty) > 0 and not skip_bardana_stock_check(doc):
			bkey = _bardana_key(doc, line)
			if bkey:
				check_bag_stock(
					bkey,
					flt(line.bagqty),
					exclude_doctype=SALES_INVOICE,
					exclude_name=doc.name if doc.name else None,
				)


def _update_sales_orders(doc):
	so_trucks: dict[str, int] = defaultdict(int)
	so_weight: dict[str, float] = defaultdict(float)
	for line in doc.details or []:
		if not line.sonumber:
			continue
		so_trucks[line.sonumber] += 1
		so_weight[line.sonumber] += flt(line.netweight)

	for sonumber, truck_count in so_trucks.items():
		so = get_order_for_update(sonumber, SIDE_SALES)
		open_qty = open_truck_qty_for_order(so, SIDE_SALES, exclude_invoice=doc.name)
		if truck_count > open_qty + 1e-9:
			frappe.throw(
				_("Sales Order {0} open truck qty exceeded (remaining {1})").format(sonumber, open_qty)
			)
		new_issued = flt(so.truckissued) + truck_count
		new_weight = flt(so.weightissued) + so_weight[sonumber]
		new_status = order_status_label(
			"CO"
			if projected_open_truck_qty(so, SIDE_SALES, fulfilled=new_issued) <= 0
			else "IP"
		)
		frappe.db.set_value(
			"Sales Order",
			sonumber,
			{
				"truckissued": new_issued,
				"weightissued": new_weight,
				"delicompdate": doc.invdate,
				"status": new_status,
			},
			update_modified=False,
		)


def _reverse_sales_orders(doc):
	for line in doc.details or []:
		if not line.sonumber:
			continue
		so = frappe.get_doc("Sales Order", line.sonumber)
		new_issued = max(0, flt(so.truckissued) - 1)
		new_weight = max(0, flt(so.weightissued) - flt(line.netweight))
		new_status = order_status_label("IP" if new_issued > 0 else "IN")
		frappe.db.set_value(
			"Sales Order",
			line.sonumber,
			{"truckissued": new_issued, "weightissued": new_weight, "status": new_status},
			update_modified=False,
		)


def _grain_key(doc, line):
	return trading_grain_key(itemcode=doc.itemcode, storeid=line.storeid)


def _bardana_key(doc, line):
	return sales_bardana_key(doc, line)


def _apply_stock_out(doc):
	for line in doc.details or []:
		qty = line_weight_qty(line, doc.kantatype)
		if qty > 0:
			apply_stock_out(
				_grain_key(doc, line),
				qty,
				movement_date=doc.invdate,
				check_reserved=False,
			)
		bkey = _bardana_key(doc, line)
		if bkey:
			apply_stock_out(bkey, flt(line.bagqty), movement_date=doc.invdate, check_reserved=False)


def _reverse_stock(doc):
	for line in doc.details or []:
		qty = line_weight_qty(line, doc.kantatype)
		if qty > 0:
			apply_stock_in(
				_grain_key(doc, line),
				qty,
				rate=flt(line.rate),
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


def _build_doc_transactions(doc, doc_key: str | None = None) -> DocTranBatch:
	batch = DocTranBatch(
		doc.location_id, doc.doctypeid, doc_key or resolve_document_key(doc, "salesinvno")
	)
	trade_sales = get_setting_account("Trade Sales")
	brokery_exp = get_setting_account("Brokery Exp")
	cartage_exp = get_setting_account("Purchase Cartage Exp")
	labour_recv = get_setting_account("Labour Receivable")
	cash_acc = get_setting_account("Cash")
	customer_acc = get_party_accid(doc.customerid)

	trucks: dict[str, list] = defaultdict(list)
	for line in doc.details or []:
		trucks[line.truckno or str(line.idx)].append(line)

	for truckno, lines in trucks.items():
		receivable_total = 0.0
		cartage = 0.0
		brokery = 0.0
		labour = 0.0
		truck_adv = 0.0
		detail_parts = []

		for line in lines:
			net = flt(line.netweight)
			receivable_total += flt(line.totalamnt)
			cartage += flt(line.cartage)
			brokery += flt(line.brokeramnt)
			labour += flt(line.labouramnt)
			truck_adv += flt(line.truckadv)
			detail_parts.append(f"{doc.itemcode}, truck.# {truckno} Wgt:{net} @{line.rate}")

		detail = "; ".join(detail_parts)
		bag_total = append_bardana_gl(batch, lines, doc, is_purchase=False, truckno=truckno)
		grain_revenue = receivable_total - bag_total

		batch.dr(customer_acc, receivable_total, partyid=doc.customerid, detail=detail)
		batch.cr(trade_sales, grain_revenue, itemcode=doc.itemcode, detail=detail)

		if labour > 0:
			batch.cr(labour_recv, labour, detail=f"Upload Labour {truckno}")
			batch.dr(trade_sales, labour, itemcode=doc.itemcode, detail="Labour offset")
		if cartage > 0:
			batch.dr(cartage_exp, cartage, detail=f"Tran Kiraya {truckno}")
			batch.cr(trade_sales, cartage, itemcode=doc.itemcode, detail="Kiraya offset")
		if brokery > 0:
			batch.dr(brokery_exp, brokery, detail=f"Tran Brokery {truckno}")
			batch.cr(trade_sales, brokery, itemcode=doc.itemcode, detail="Brokery offset")
		if truck_adv > 0:
			batch.dr(cash_acc, truck_adv, detail="Paid Adv Kiraya", bnkcash_gl=1)
			batch.cr(customer_acc, truck_adv, partyid=doc.customerid, detail="Adv Kiraya")

	return batch
