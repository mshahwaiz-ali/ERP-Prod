# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.6 — SRSUBMIT (reverse Sales Invoice)

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.bardana_gl import append_bardana_gl
from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import SALES_RETURN
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.invoice_calc import line_weight_qty, recalc_invoice_lines
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import apply_stock_in, apply_stock_out, mark_posted, mark_unposted
from millitrix.utils.trading_stock_keys import sales_bardana_key, trading_grain_key


def sync_sales_return_header_from_invoice(doc, si) -> None:
	"""Denormalize SI header for premium list + Oracle POST-QUERY parity."""
	for field in (
		"itemcode",
		"customerid",
		"brokerid",
		"sub_partyid",
		"kantatype",
		"amntby",
		"borrow",
		"brokery",
		"mundtype",
		"brokery_auto_calc",
	):
		if hasattr(doc, field) and hasattr(si, field):
			setattr(doc, field, getattr(si, field))


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = SALES_RETURN
	validate_fiscal_period(doc.retdate)
	if not doc.salesinvno:
		frappe.throw(_("Select a Sales Invoice"))
	si = frappe.get_doc("Sales Invoice", doc.salesinvno)
	if si.docstatus != 1:
		frappe.throw(_("Sales Invoice must be submitted"))
	sync_sales_return_header_from_invoice(doc, si)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows

	strip_blank_child_rows(doc, "details", "Sales Return Detail")
	if not doc.details:
		frappe.throw(_("Add return lines"))
	recalc_invoice_lines(doc, is_purchase=False)
	_validate_return_lines(doc, si)


def _returned_qty_for_line(
	salesinvno: str, sidetlno: int, *, exclude: str | None = None
) -> float:
	total = 0.0
	names = frappe.get_all(
		"Sales Return",
		filters={"docstatus": 1, "salesinvno": salesinvno},
		pluck="name",
	)
	for name in names:
		if exclude and name == exclude:
			continue
		sr = frappe.get_doc("Sales Return", name)
		for line in sr.details or []:
			if int(line.sidetlno or 0) == int(sidetlno):
				total += line_weight_qty(
					line, sr.kantatype, is_purchase=False, header=sr
				)
	return total


def _validate_return_lines(doc, si) -> None:
	si_lines = {int(line.sidetlno or 0): line for line in si.details or [] if line.sidetlno}
	seen_sidetlno: set[int] = set()
	exclude = doc.name if not doc.is_new() else None

	for idx, line in enumerate(doc.details or [], start=1):
		ref = int(line.sidetlno or 0)
		if not ref:
			frappe.throw(_("Row {0}: invoice line reference is required").format(idx))
		if ref in seen_sidetlno:
			frappe.throw(_("Row {0}: duplicate invoice line {1}").format(idx, ref))
		seen_sidetlno.add(ref)

		si_line = si_lines.get(ref)
		if not si_line:
			frappe.throw(
				_("Row {0}: invoice line {1} not found on {2}").format(idx, ref, doc.salesinvno)
			)

		orig_qty = line_weight_qty(si_line, doc.kantatype, is_purchase=False, header=si)
		ret_qty = line_weight_qty(line, doc.kantatype, is_purchase=False, header=doc)
		if ret_qty > orig_qty + 1e-9:
			frappe.throw(_("Row {0}: return qty exceeds invoice line qty").format(idx))

		prior = _returned_qty_for_line(doc.salesinvno, ref, exclude=exclude)
		if prior + ret_qty > orig_qty + 1e-9:
			frappe.throw(
				_("Row {0}: cumulative return qty exceeds invoice line balance (remaining {1})").format(
					idx, max(0, orig_qty - prior)
				)
			)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "salesretno")
	orig = frappe.get_doc("Sales Invoice", doc.salesinvno)
	_apply_stock_in(doc, orig)
	batch = _build_return_transactions(doc, orig, doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.retdate,
		narration=f"Sales Return {doc.salesretno} vs {doc.salesinvno}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _grain_key(orig, line):
	return trading_grain_key(itemcode=orig.itemcode, storeid=line.storeid)


def _bardana_key(orig, line):
	return sales_bardana_key(orig, line)


def _apply_stock_in(doc, orig):
	for line in doc.details or []:
		qty = line_weight_qty(line, doc.kantatype, is_purchase=False, header=doc)
		if qty > 0:
			apply_stock_in(
				_grain_key(orig, line),
				qty,
				rate=flt(line.rate),
				movement_date=doc.retdate,
			)
		bkey = _bardana_key(orig, line)
		if bkey:
			apply_stock_in(
				bkey,
				flt(line.bagqty),
				rate=flt(line.bagrate),
				movement_date=doc.retdate,
				bagweight=flt(line.bagweight) or None,
			)


def _reverse_stock(doc, orig):
	for line in doc.details or []:
		qty = line_weight_qty(line, doc.kantatype, is_purchase=False, header=doc)
		if qty > 0:
			apply_stock_out(
				_grain_key(orig, line),
				qty,
				movement_date=doc.retdate,
				check_reserved=False,
			)
		bkey = _bardana_key(orig, line)
		if bkey:
			apply_stock_out(bkey, flt(line.bagqty), movement_date=doc.retdate, check_reserved=False)


def _build_return_transactions(doc, orig, doc_key: str | None = None) -> DocTranBatch:
	batch = DocTranBatch(
		doc.location_id, doc.doctypeid, doc_key or resolve_document_key(doc, "salesretno")
	)
	trade_sales = get_setting_account("Trade Sales")
	brokery_exp = get_setting_account("Brokery Exp")
	cartage_exp = get_setting_account("Purchase Cartage Exp")
	labour_recv = get_setting_account("Labour Receivable")
	cash_acc = get_setting_account("Cash")
	customer_acc = get_party_accid(orig.customerid)

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
			truck_adv += flt(getattr(line, "truckadv", 0))
			detail_parts.append(f"{orig.itemcode}, truck.# {truckno} Wgt:{net} @{line.rate}")

		detail = "; ".join(detail_parts)
		bag_total = append_bardana_gl(
			batch, lines, orig, is_purchase=False, truckno=truckno, reverse=True
		)
		grain_revenue = receivable_total - bag_total

		batch.cr(customer_acc, receivable_total, partyid=orig.customerid, detail=detail)
		batch.dr(trade_sales, grain_revenue, itemcode=orig.itemcode, detail=detail)

		if labour > 0:
			batch.dr(labour_recv, labour, detail=f"Upload Labour {truckno}")
			batch.cr(trade_sales, labour, itemcode=orig.itemcode, detail="Labour offset")
		if cartage > 0:
			batch.cr(cartage_exp, cartage, detail=f"Tran Kiraya {truckno}")
			batch.dr(trade_sales, cartage, itemcode=orig.itemcode, detail="Kiraya offset")
		if brokery > 0:
			batch.cr(brokery_exp, brokery, detail=f"Tran Brokery {truckno}")
			batch.dr(trade_sales, brokery, itemcode=orig.itemcode, detail="Brokery offset")
		if truck_adv > 0:
			batch.cr(cash_acc, truck_adv, detail="Paid Adv Kiraya", bnkcash_gl=1)
			batch.dr(customer_acc, truck_adv, partyid=orig.customerid, detail="Adv Kiraya")

	return batch
