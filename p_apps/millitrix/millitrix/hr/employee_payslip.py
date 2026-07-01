# Copyright (c) 2026, Millitrix and contributors
# Blueprint 9.21 — PaySlip

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import EMPLOYEE_PAYSLIP
from millitrix.utils.employee_gl import get_employee_advance_balance, get_employee_category_accid
from millitrix.utils.erpnext_compat import get_session_location
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.stock import mark_posted, mark_unposted


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = EMPLOYEE_PAYSLIP
	validate_fiscal_period(doc.pdate)
	if not doc.employees:
		frappe.throw(_("Add at least one employee line"))

	seen_employees: set[str] = set()
	for line in doc.employees or []:
		if not line.empno:
			frappe.throw(_("Employee is required on each payslip line"))
		emp_key = str(line.empno)
		if emp_key in seen_employees:
			frappe.throw(_("Duplicate employee {0} on payslip").format(line.empno))
		seen_employees.add(emp_key)

		if not frappe.db.exists("Employee Setup", emp_key):
			frappe.throw(_("Employee Setup {0} not found").format(line.empno))
		if flt(line.amount) <= 0:
			frappe.throw(_("Salary amount must be positive for employee {0}").format(line.empno))
		deduct = flt(line.balance)
		if deduct > flt(line.amount):
			frappe.throw(_("Advance deduction exceeds salary for employee {0}").format(line.empno))
		location_id = doc.location_id or get_session_location()
		advance_balance = get_employee_advance_balance(line.empno, location_id=location_id)
		if deduct > advance_balance + 0.01:
			frappe.throw(
				_("Advance deduction for employee {0} exceeds available balance {1}").format(
					line.empno, advance_balance
				)
			)
	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "pslipid")
	batch = _build_payslip_transactions(doc, doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.pdate,
		narration=doc.remarks or f"PaySlip {doc.pslipid} — {doc.paymonth}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
	doc_key = resolve_document_key(doc, "pslipid")
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": doc.doctypeid, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, doc.doctypeid, doc_key)
	mark_unposted(doc)


def _build_payslip_transactions(doc, doc_key: str | None = None) -> DocTranBatch:
	doc_key = doc_key or resolve_document_key(doc, "pslipid")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	salary_exp = get_setting_account("Salary Exp")
	total = 0.0

	for line in doc.employees or []:
		gross = flt(line.amount)
		deduct = flt(line.balance)
		if deduct > gross:
			frappe.throw(_("Advance deduction exceeds salary for employee {0}").format(line.empno))
		net = gross - deduct
		total += gross
		emp_acc = get_employee_category_accid(line.empno)
		emp_trans = int(str(line.empno))
		batch.cr(
			emp_acc,
			net,
			detail=f"Salary {doc.paymonth} — Emp {line.empno}",
			trans_id=emp_trans,
		)
		if deduct > 0:
			batch.cr(
				emp_acc,
				deduct,
				detail=f"Advance deduction — Emp {line.empno}",
				trans_id=emp_trans,
			)

	if total > 0:
		batch.dr(salary_exp, total, detail=f"Payslip {doc.pslipid}")

	return batch


def preview_payslip_accounting_lines(doc) -> list[dict]:
	batch = _build_payslip_transactions(doc)
	lines: list[dict] = []
	for row in batch.rows:
		lines.append(
			{
				"accid": row.accid,
				"account": frappe.db.get_value("Chart of Accounting", row.accid, "description")
				or row.accid,
				"debit": flt(row.debit, 2),
				"credit": flt(row.credit, 2),
				"detail": row.detail or "",
			}
		)
	return lines


def get_posted_payslip_accounting_lines(doc) -> list[dict]:
	doc_key = resolve_document_key(doc, "pslipid")
	rows = frappe.db.sql(
		"""
		SELECT
			vd.accid,
			COALESCE(coa.description, vd.accid) AS account,
			COALESCE(vd.debit, 0) AS debit,
			COALESCE(vd.credit, 0) AS credit,
			vd.detail
		FROM `tabVoucher Transaction` vt
		INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = vt.name
		LEFT JOIN `tabChart of Accounting` coa ON coa.name = vd.accid
		WHERE vt.location_id = %(location_id)s
			AND vt.doctypeid = %(doctypeid)s
			AND vt.documentid = %(documentid)s
			AND vt.docstatus = 1
		ORDER BY vd.idx
		""",
		{
			"location_id": doc.location_id,
			"doctypeid": doc.doctypeid,
			"documentid": doc_key,
		},
		as_dict=True,
	)
	return rows


def fetch_salary_employee_lines(location_id: str) -> list[dict]:
	"""Active employees in PaySlip-enabled categories for Generate Salary."""
	if not location_id:
		frappe.throw(_("Location is required"))

	rows = frappe.db.sql(
		"""
		SELECT
			e.empno,
			COALESCE(e.salary, 0) AS amount
		FROM `tabEmployee Setup` e
		INNER JOIN `tabEmployee Category` c ON c.name = e.ecatid
		WHERE e.location_id = %(location_id)s
			AND IFNULL(c.payslip, 0) = 1
			AND (e.ldate IS NULL OR e.ldate = '')
			AND COALESCE(e.salary, 0) > 0
		ORDER BY e.empno
		""",
		{"location_id": location_id},
		as_dict=True,
	)

	out: list[dict] = []
	for row in rows:
		salary = flt(row.amount, 2)
		advance = get_employee_advance_balance(row.empno, location_id=location_id)
		out.append(
			{
				"empno": str(row.empno),
				"amount": salary,
				"balance": flt(min(advance, salary), 2),
			}
		)
	return out


def resolve_payslip_location(location_id: str | None) -> str:
	location_id = (location_id or "").strip()
	if location_id:
		return location_id
	location_id = get_session_location()
	if not location_id:
		frappe.throw(_("Location is required"))
	return location_id
