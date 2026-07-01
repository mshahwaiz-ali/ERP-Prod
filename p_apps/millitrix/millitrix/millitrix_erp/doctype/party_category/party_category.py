# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import get_next_numeric_id


class PartyCategory(Document):
	def before_insert(self):
		if not self.pcat_id:
			self.pcat_id = max(get_next_numeric_id(self.doctype, "pcat_id"), 11)

	def validate(self):
		if int(self.pcat_id or 0) <= 0:
			frappe.throw("Party Category ID must be a positive number (example: 11, 12, 13)")

		if self.accid:
			level = frappe.db.get_value(
				"Chart of Accounting", self.accid, "chartlevel"
			)
			transflag = frappe.db.get_value(
				"Chart of Accounting", self.accid, "transflag"
			)
			if level and int(level) != 4:
				frappe.throw("Party Category control account must be Chart Level 4")
			if transflag and str(transflag).lower() not in ("yes", "y", "1"):
				frappe.throw("Party Category control account must allow transactions")
