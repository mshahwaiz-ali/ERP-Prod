# Shared Employee Payment / Receipt Voucher logic (Oracle CNBEmpVoucher.fmx).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.finance.cnb_voucher import _build_cnb_transactions
from millitrix.utils.doc_transaction import persist_doc_transactions
from millitrix.utils.employee_gl import get_employee_category_accid
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.stock import mark_posted, mark_unposted


def validate_employee_voucher(doc, *, doctype_id: str, voucher_mode: str) -> None:
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = doctype_id
	validate_fiscal_period(doc.vouchdate)

	if not doc.documents:
		frappe.throw(_("Add at least one employee line"))

	seen_employees: set[str] = set()
	for idx, line in enumerate(doc.documents or [], start=1):
		if not line.empno:
			frappe.throw(_("Employee is required on row {0}").format(idx))
		emp_key = str(line.empno)
		if emp_key in seen_employees:
			frappe.throw(_("Row {0}: duplicate employee {1}").format(idx, line.empno))
		seen_employees.add(emp_key)

		amt = flt(line.amount)
		if amt <= 0:
			frappe.throw(_("Amount must be greater than zero on row {0}").format(idx))
		line.accid = get_employee_category_accid(line.empno)

	doc.amount = sum(flt(line.amount) for line in doc.documents or [])

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def submit_employee_voucher(doc, *, narration_prefix: str) -> None:
	doc_key = resolve_document_key(doc, "empvno")
	batch = _build_cnb_transactions(doc)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.vouchdate,
		narration=doc.narration or f"{narration_prefix} {doc.empvno}",
	)
	mark_posted(doc)


def cancel_employee_voucher(doc) -> None:
	doc_key = resolve_document_key(doc, "empvno")
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": doc.doctypeid, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, doc.doctypeid, doc_key)
	mark_unposted(doc)
