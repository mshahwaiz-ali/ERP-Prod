# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class EmployeeCategory(Document):
	def before_insert(self):
		assign_numeric_id(self, "ecatid")

	def validate(self):
		if isinstance(self.payslip, str):
			self.payslip = 1 if self.payslip in ("Yes", "Y", "1") else 0

		if self.accid:
			level = frappe.db.get_value("Chart of Accounting", self.accid, "chartlevel")
			transflag = frappe.db.get_value("Chart of Accounting", self.accid, "transflag")
			if level and int(level) != 5:
				frappe.throw("Employee Category GL account must be Chart Level 5")
			if transflag and str(transflag).lower() not in ("yes", "y", "1"):
				frappe.throw("Employee Category GL account must allow transactions")
