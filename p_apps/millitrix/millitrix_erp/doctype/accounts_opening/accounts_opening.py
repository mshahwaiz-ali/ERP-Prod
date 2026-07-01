# Copyright (c) 2026, Millitrix and contributors
# For license information, see license.txt

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class AccountsOpening(Document):

	def before_insert(self):
		if not self.opening_date:
			self.opening_date = frappe.utils.today()
		assign_numeric_id(self, "glopenid")

