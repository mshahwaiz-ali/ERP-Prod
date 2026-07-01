# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.6 — PRSUBMIT (reverse PI)

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.bardana_gl import append_bardana_gl, skip_bardana_stock_check
from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import PURCHASE_INVOICE, PURCHASE_RETURN
from millitrix.utils.field_normalizers import is_yes
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.invoice_calc import line_weight_qty, recalc_invoice_lines
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
from millitrix.utils.trading_stock_keys import purchase_bardana_key, trading_grain_key


def sync_purchase_return_header_from_invoice(doc, pi) -> None:
	"""Denormalize PI header for premium list + Oracle POST-QUERY parity."""
	for field in (
		"itemcode",
		"supplierid",
		"brokerid",
		"sub_partyid",
		"kantatype",
		"amntby",
		"borrow",
		"brokery",
		"mundtype",
		"brokery_auto_calc",
		"brokery_dr_supplier",
	):
		if hasattr(doc, field) and hasattr(pi, field):
			setattr(doc, field, getattr(pi, field))


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = PURCHASE_RETURN
	validate_fiscal_period(doc.retdate)
	if not doc.purchinvno:
		frappe.throw(_("Select a Purchase Invoice"))
	pi = frappe.get_doc("Purchase Invoice", doc.purchinvno)
	if pi.docstatus != 1:
		frappe.throw(_("Purchase Invoice must be submitted"))
	sync_purchase_return_header_from_invoice(doc, pi)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows

	strip_blank_child_rows(doc, "details", "Purchase Return Detail")
	if not doc.details:
		frappe.throw(_("Add return lines"))
	recalc_invoice_lines(doc, is_purchase=True)
	_validate_return_lines(doc, pi)
	_validate_out_stock(doc, pi)


def _returned_qty_for_line(
	purchinvno: str, pidetlno: int, *, exclude: str | None = None
) -> float:
	total = 0.0
	names = frappe.get_all(
		"Purchase Return",
		filters={"docstatus": 1, "purchinvno": purchinvno},
		pluck="name",
	)
	for name in names:
		if exclude and name == exclude:
			continue
		pr = frappe.get_doc("Purchase Return", name)
		for line in pr.details or []:
			if int(line.pidetlno or 0) == int(pidetlno):
				total += line_weight_qty(
					line, pr.kantatype, is_purchase=True, header=pr
				)
	return total


def _validate_return_lines(doc, pi) -> None:
	pi_lines = {int(line.pidetlno or 0): line for line in pi.details or [] if line.pidetlno}
	seen_pidetlno: set[int] = set()
	exclude = doc.name if not doc.is_new() else None

	for idx, line in enumerate(doc.details or [], start=1):
		ref = int(line.pidetlno or 0)
		if not ref:
			frappe.throw(_("Row {0}: invoice line reference is required").format(idx))
		if ref in seen_pidetlno:
			frappe.throw(_("Row {0}: duplicate invoice line {1}").format(idx, ref))
		seen_pidetlno.add(ref)

		pi_line = pi_lines.get(ref)
		if not pi_line:
			frappe.throw(
				_("Row {0}: invoice line {1} not found on {2}").format(idx, ref, doc.purchinvno)
			)

		orig_qty = line_weight_qty(pi_line, doc.kantatype, is_purchase=True, header=pi)
		ret_qty = line_weight_qty(line, doc.kantatype, is_purchase=True, header=doc)
		if ret_qty > orig_qty + 1e-9:
			frappe.throw(_("Row {0}: return qty exceeds invoice line qty").format(idx))

		prior = _returned_qty_for_line(doc.purchinvno, ref, exclude=exclude)
		if prior + ret_qty > orig_qty + 1e-9:
			frappe.throw(
				_("Row {0}: cumulative return qty exceeds invoice line balance (remaining {1})").format(
					idx, max(0, orig_qty - prior)
				)
			)


def _validate_out_stock(doc, pi) -> None:
	for line in doc.details or []:
		grain_qty = line_weight_qty(line, doc.kantatype, is_purchase=True, header=doc)
		if pi.itemcode and grain_qty > 0:
			key = trading_grain_key(itemcode=pi.itemcode, storeid=line.storeid)
			name = get_in_store_item_name(key)
			stock = flt(frappe.db.get_value("Stock In Hand", name, "stock_in_hand")) if name else 0
			reserved = get_reserved_qty(
				key,
				exclude_doctype=PURCHASE_RETURN,
				exclude_name=doc.name if doc.name else None,
			)
			if grain_qty > stock - reserved + 1e-9:
				frappe.throw(
					_("Insufficient grain stock for {0}. Available {1}, required {2}").format(
						pi.itemcode, stock - reserved, grain_qty
					)
				)
		if line.bagid and flt(line.bagqty) > 0 and not skip_bardana_stock_check(pi):
			bkey = purchase_bardana_key(pi, line)
			if bkey:
				check_bag_stock(
					bkey,
					flt(line.bagqty),
					exclude_doctype=PURCHASE_RETURN,
					exclude_name=doc.name if doc.name else None,
				)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "purchretno")
	orig = frappe.get_doc("Purchase Invoice", doc.purchinvno)
	_apply_stock_out(doc, orig)
	batch = _build_return_transactions(doc, orig, doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.retdate,
		narration=f"Purchase Return {doc.purchretno} vs PI {doc.purchinvno}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _grain_key(orig, line):
	return trading_grain_key(itemcode=orig.itemcode, storeid=line.storeid)


def _bardana_key(orig, line):
	return purchase_bardana_key(orig, line)


def _apply_stock_out(doc, orig):
	for line in doc.details or []:
		qty = line_weight_qty(line, doc.kantatype, is_purchase=True, header=doc)
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


def _reverse_stock(doc, orig):
	for line in doc.details or []:
		qty = line_weight_qty(line, doc.kantatype, is_purchase=True, header=doc)
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


def _build_return_transactions(doc, orig, doc_key: str | None = None) -> DocTranBatch:
	batch = DocTranBatch(
		doc.location_id, doc.doctypeid, doc_key or resolve_document_key(doc, "purchretno")
	)
	trade_purchase = get_setting_account("Trade Purchase")
	brokery_exp = get_setting_account("Brokery Exp")
	party_brokery = get_setting_account("Party Brokery")
	cartage_exp = get_setting_account("Purchase Cartage Exp")
	cash_acc = get_setting_account("Cash")
	supplier_acc = get_party_accid(orig.supplierid)
	brokery_dr_supplier = is_yes(orig.brokery_dr_supplier)

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
			truck_adv += flt(getattr(line, "truckadv", 0))
			detail_parts.append(f"{orig.itemcode}, truck.# {truckno} Wgt:{net} @{line.rate}")

		detail = "; ".join(detail_parts)
		bag_total = append_bardana_gl(
			batch, lines, orig, is_purchase=True, truckno=truckno, reverse=True
		)
		trade_cr = payable_total - bag_total
		if brokery > 0:
			trade_cr -= brokery
		supplier_dr = payable_total - brokery if brokery_dr_supplier and brokery > 0 else payable_total

		batch.cr(trade_purchase, trade_cr, itemcode=orig.itemcode, detail=detail)
		batch.dr(supplier_acc, supplier_dr, partyid=orig.supplierid, detail=detail)

		if cartage > 0:
			batch.cr(cartage_exp, cartage, detail=f"Tran Kiraya {truckno}")
			batch.dr(supplier_acc, cartage, partyid=orig.supplierid, detail="Cartage")
		if brokery > 0:
			batch.cr(brokery_exp, brokery, detail=f"Tran Brokery {truckno}")
			if brokery_dr_supplier:
				batch.dr(party_brokery, brokery, detail="Party Brokery DR Supplier")
			else:
				batch.dr(supplier_acc, brokery, partyid=orig.supplierid, detail="Brokery payable")
		if truck_adv > 0:
			batch.cr(cash_acc, truck_adv, detail="Paid Adv Kiraya", bnkcash_gl=1)
			batch.dr(supplier_acc, truck_adv, partyid=orig.supplierid, detail="Adv Kiraya")

	return batch
