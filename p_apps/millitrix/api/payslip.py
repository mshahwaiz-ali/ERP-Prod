# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _

from millitrix.api.permissions import require_permission
from millitrix.hr.employee_payslip import (
	fetch_salary_employee_lines,
	get_posted_payslip_accounting_lines,
	preview_payslip_accounting_lines,
	resolve_payslip_location,
)
from millitrix.utils.payslip_form import get_employee_line_defaults, search_payslip_employee


@frappe.whitelist()
def generate_salary_lines(location_id: str | None = None) -> list[dict]:
	"""Populate payslip grid from active employees (category with PaySlip flag)."""
	require_permission("PaySlip", "read")
	location_id = resolve_payslip_location(location_id)
	return fetch_salary_employee_lines(location_id)


@frappe.whitelist()
def fetch_employee_line_defaults(empno: str, location_id: str | None = None) -> dict:
	require_permission("PaySlip", "read")
	if not empno:
		frappe.throw(_("Employee is required"))
	location_id = resolve_payslip_location(location_id)
	return get_employee_line_defaults(empno=empno, location_id=location_id)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def empno_query(doctype, txt, searchfield, start, page_len, filters):
	require_permission("PaySlip", "read")
	return search_payslip_employee(doctype, txt, searchfield, start, page_len, filters)


@frappe.whitelist()
def get_payslip_accounting_lines(doctype: str, name: str) -> list[dict]:
	"""Return accounting lines for PaySlip (preview or posted)."""
	if doctype != "PaySlip":
		frappe.throw(_("Accounting is not supported for {0}").format(doctype))
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	if doc.docstatus == 1:
		return get_posted_payslip_accounting_lines(doc)
	return preview_payslip_accounting_lines(doc)
