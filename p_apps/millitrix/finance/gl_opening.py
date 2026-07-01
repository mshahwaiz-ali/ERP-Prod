# Copyright (c) 2026, Millitrix and contributors
# Blueprint 9.16 — Accounts Opening

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import GL_OPENING
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.stock import mark_posted, mark_unposted
from millitrix.utils.voucher_balance import validate_dr_cr_balance


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = GL_OPENING
	validate_fiscal_period(doc.opening_date)
	if not doc.details:
		frappe.throw(_("Add opening balance lines"))
	_validate_detail_lines(doc)
	validate_dr_cr_balance(doc.details)
	doc.total_debit = sum(flt(line.debit) for line in doc.details or [])
	doc.total_credit = sum(flt(line.credit) for line in doc.details or [])

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def _validate_detail_lines(doc) -> None:
	for idx, line in enumerate(doc.details or [], start=1):
		if not line.accid:
			frappe.throw(_("Row {0}: Account is required").format(idx))


def _line_trans_id(line) -> int | None:
	raw = line.get("trans_id")
	if raw in (None, ""):
		return None
	return cint(raw)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "glopenid")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	for line in doc.details or []:
		dr = flt(line.debit)
		cr = flt(line.credit)
		kwargs = dict(
			partyid=line.partyid or None,
			itemcode=line.itemcode or None,
			empno=line.empno or None,
			trans_id=_line_trans_id(line),
		)
		if dr > 0:
			batch.dr(
				line.accid,
				dr,
				detail=f"Opening balance {doc.opening_date}",
				**kwargs,
			)
		if cr > 0:
			batch.cr(
				line.accid,
				cr,
				detail=f"Opening balance {doc.opening_date}",
				**kwargs,
			)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.opening_date,
		narration=f"Accounts Opening {doc.glopenid}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)