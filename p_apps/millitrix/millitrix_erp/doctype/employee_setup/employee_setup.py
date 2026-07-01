# Copyright (c) 2026, Millitrix and contributors
# Blueprint — Oracle EMPLOYEE / Employee.fmx

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate

from millitrix.utils.erpnext_compat import get_session_location
from millitrix.utils.naming import assign_numeric_id


class EmployeeSetup(Document):
	def before_insert(self):
		assign_numeric_id(self, "empno")

	def validate(self):
		if not self.location_id:
			location = get_session_location()
			if location:
				self.location_id = location
		if not self.location_id:
			frappe.throw(frappe._("Mill is required"))

		if not (self.ename or "").strip():
			frappe.throw(frappe._("Employee name is required"))
		if flt(self.salary) < 0:
			frappe.throw(frappe._("Salary cannot be negative"))
		if self.hiredate and self.ldate and getdate(self.ldate) < getdate(self.hiredate):
			frappe.throw(frappe._("Left Date cannot be before Hiredate"))

		for field, doctype in (
			("deptid", "Departments"),
			("desigid", "Designation"),
			("ecatid", "Employee Category"),
		):
			if self.get(field) and not frappe.db.exists(doctype, self.get(field)):
				frappe.throw(frappe._("{0} {1} not found in master setup").format(doctype, self.get(field)))

		if self.location_id and not frappe.db.exists("Location", self.location_id):
			frappe.throw(frappe._("Location {0} not found in master setup").format(self.location_id))
