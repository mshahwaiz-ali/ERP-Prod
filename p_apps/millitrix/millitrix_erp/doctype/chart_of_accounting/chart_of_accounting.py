# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.coa_accid import assign_coa_accid


class ChartofAccounting(Document):
	def before_insert(self):
		assign_coa_accid(self)

	def validate(self):
		level = int(self.chartlevel or 0)
		if level < 1 or level > 5:
			frappe.throw("Chart Level must be between 1 and 5")

		if level < 5 and (self.transflag or "No") in ("Yes", "Y"):
			frappe.throw("Only Chart Level 5 accounts can allow transactions")

		if level == 5 and (self.transflag or "No") not in ("Yes", "Y"):
			self.transflag = "Yes"
		elif self.transflag == "Y":
			self.transflag = "Yes"

		if level == 1 and self.parentid:
			frappe.throw("Chart Level 1 accounts cannot have a Parent Account")

		if level > 1 and not self.parentid:
			frappe.throw(f"Chart Level {level} accounts must have a Parent Account")

		if self.parentid:
			parent_level = frappe.db.get_value(
				"Chart of Accounting", self.parentid, "chartlevel"
			)
			if parent_level and int(parent_level) != level - 1:
				frappe.throw(
					f"Parent Account must be Chart Level {level - 1}, not {parent_level}"
				)
