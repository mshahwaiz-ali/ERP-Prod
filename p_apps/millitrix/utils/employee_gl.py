# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt


def get_employee_category_accid(empno) -> str:
	emp_name = str(empno)
	if not frappe.db.exists("Employee Setup", emp_name):
		frappe.throw(_("Employee Setup {0} not found").format(empno))
	ecatid = frappe.db.get_value("Employee Setup", emp_name, "ecatid")
	if not ecatid:
		frappe.throw(_("Employee Setup {0} has no category").format(empno))
	accid = frappe.db.get_value("Employee Category", str(ecatid), "accid")
	if not accid:
		frappe.throw(_("Employee Category {0} has no GL account").format(ecatid))
	return accid


def get_employee_advance_balance(empno, *, location_id: str) -> float:
	"""Outstanding employee advance (net debit on employee ledger sub-account)."""
	accid = get_employee_category_accid(empno)
	trans_id = cint(empno)
	row = frappe.db.sql(
		"""
		SELECT
			SUM(COALESCE(vd.debit, 0)) - SUM(COALESCE(vd.credit, 0)) AS balance
		FROM `tabVoucher Transaction` vt
		INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = vt.name
		WHERE vt.docstatus = 1
			AND vt.location_id = %(location_id)s
			AND vd.accid = %(accid)s
			AND vd.trans_id = %(trans_id)s
		""",
		{"location_id": location_id, "accid": accid, "trans_id": trans_id},
		as_dict=True,
	)
	return max(0.0, flt((row[0] or {}).get("balance")))
