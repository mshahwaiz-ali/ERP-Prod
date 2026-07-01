# Copyright (c) 2026, Millitrix and contributors
# Oracle Pay_PaySlip.fmb — employee line defaults and LOV.

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.employee_gl import get_employee_advance_balance


def get_employee_line_defaults(*, empno: str, location_id: str) -> dict:
	"""Oracle WHEN-VALIDATE-ITEM (EMPNO) — salary + advance balance."""
	if not empno:
		return {}
	row = frappe.db.get_value(
		"Employee Setup",
		empno,
		["ename", "salary", "location_id", "ldate"],
		as_dict=True,
	)
	if not row:
		frappe.throw(frappe._("This employee does not exist in master setup."))
	if row.ldate:
		frappe.throw(frappe._("Employee {0} is not active (left date set).").format(empno))
	if location_id and row.location_id and str(row.location_id) != str(location_id):
		frappe.throw(frappe._("Employee {0} belongs to another location.").format(empno))

	salary = flt(row.salary)
	if salary <= 0:
		frappe.throw(frappe._("Employee {0} has no salary defined.").format(empno))

	advance = get_employee_advance_balance(empno, location_id=location_id)
	return {
		"amount": salary,
		"balance": flt(min(advance, salary)),
	}


@frappe.validate_and_sanitize_search_inputs
def search_payslip_employee(doctype, txt, searchfield, start, page_len, filters):
	"""Employee LOV — active, PaySlip category, by location."""
	location_id = (filters or {}).get("location_id")
	txt = f"%{txt or ''}%"
	conditions = [
		"IFNULL(c.payslip, 0) = 1",
		"(e.ldate IS NULL OR e.ldate = '')",
		"COALESCE(e.salary, 0) > 0",
		"(CAST(e.empno AS CHAR) LIKE %(txt)s OR e.ename LIKE %(txt)s)",
	]
	params: dict = {"txt": txt, "start": start, "page_len": page_len}
	if location_id:
		conditions.append("e.location_id = %(location_id)s")
		params["location_id"] = location_id
	where = " AND ".join(conditions)
	return frappe.db.sql(
		f"""SELECT e.empno, e.ename
		FROM `tabEmployee Setup` e
		INNER JOIN `tabEmployee Category` c ON c.name = e.ecatid
		WHERE {where}
		ORDER BY e.ename
		LIMIT %(start)s, %(page_len)s""",
		params,
	)
