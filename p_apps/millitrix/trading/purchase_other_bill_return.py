# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import PURCHASE_OTHER_BILL_RETURN
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import mark_posted, mark_unposted


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = PURCHASE_OTHER_BILL_RETURN
	validate_fiscal_period(doc.brdate)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows

	strip_blank_child_rows(doc, "details", "Purchase Return Other Bill Detail")
	if not doc.pbillno:
		frappe.throw(_("Select the original Purchase Other Bill"))
	if not frappe.db.exists("Purchase Other Bill", doc.pbillno):
		frappe.throw(_("Purchase Other Bill {0} not found").format(doc.pbillno))
	if not doc.details:
		frappe.throw(_("Add return lines"))

	orig = frappe.get_doc("Purchase Other Bill", doc.pbillno)
	if orig.docstatus != 1:
		frappe.throw(_("Original bill must be submitted"))
	doc.partyid = orig.partyid
	_validate_return_lines(doc, orig)
	doc.amount = _calc_return_amount(doc, orig)


def _returned_qty_for_line(pbillno: str, pbdetlno: int, *, exclude: str | None = None) -> float:
	total = 0.0
	names = frappe.get_all(
		"Purchase Return Other Bill",
		filters={"docstatus": 1, "pbillno": pbillno},
		pluck="name",
	)
	for name in names:
		if exclude and name == exclude:
			continue
		ret = frappe.get_doc("Purchase Return Other Bill", name)
		for line in ret.details or []:
			if int(line.pbdetlno or 0) == int(pbdetlno):
				total += flt(line.quantity)
	return total


def _validate_return_lines(doc, orig) -> None:
	orig_lines = {int(line.pbdetlno or idx): line for idx, line in enumerate(orig.details or [], 1)}
	seen: set[int] = set()
	exclude = doc.name if not doc.is_new() else None

	for idx, line in enumerate(doc.details or [], start=1):
		key = int(line.pbdetlno or 0)
		if not key:
			frappe.throw(_("Row {0}: bill line reference is required").format(idx))
		if key in seen:
			frappe.throw(_("Row {0}: duplicate bill line {1}").format(idx, key))
		seen.add(key)

		orig_line = orig_lines.get(key)
		if not orig_line:
			frappe.throw(
				_("Row {0}: bill line {1} not found on {2}").format(idx, key, doc.pbillno)
			)

		ret_qty = flt(line.quantity)
		if ret_qty <= 0:
			frappe.throw(_("Row {0}: return quantity must be greater than zero").format(idx))

		orig_qty = flt(orig_line.quantity)
		if ret_qty > orig_qty + 1e-9:
			frappe.throw(_("Row {0}: return qty exceeds bill line qty").format(idx))

		prior = _returned_qty_for_line(doc.pbillno, key, exclude=exclude)
		if prior + ret_qty > orig_qty + 1e-9:
			frappe.throw(
				_("Row {0}: cumulative return qty exceeds bill line balance (remaining {1})").format(
					idx, max(0, orig_qty - prior)
				)
			)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "prbillno")
	orig = frappe.get_doc("Purchase Other Bill", doc.pbillno)
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	exp_acc = get_setting_account("Purchases OtherBill")
	party_acc = get_party_accid(orig.partyid)
	total = flt(doc.amount)

	orig_lines = {int(line.pbdetlno or idx): line for idx, line in enumerate(orig.details or [], 1)}
	for line in doc.details or []:
		key = int(line.pbdetlno or 0)
		orig_line = orig_lines.get(key)
		if not orig_line:
			continue
		amt = flt(line.quantity) * flt(orig_line.rate)
		if amt <= 0:
			continue
		batch.cr(exp_acc, amt, itemcode=orig_line.itemcode, detail=f"Return bill {doc.prbillno}")
	batch.dr(party_acc, total, partyid=orig.partyid, detail=f"Purchase Return Other Bill {doc.prbillno}")

	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.brdate,
		narration=f"Purchase Return Other Bill {doc.prbillno}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _calc_return_amount(doc, orig) -> float:
	orig_lines = {int(line.pbdetlno or idx): line for idx, line in enumerate(orig.details or [], 1)}
	total = 0.0
	for line in doc.details or []:
		key = int(line.pbdetlno or 0)
		orig_line = orig_lines.get(key)
		if orig_line:
			total += flt(line.quantity) * flt(orig_line.rate)
	return round(flt(total), 2)
