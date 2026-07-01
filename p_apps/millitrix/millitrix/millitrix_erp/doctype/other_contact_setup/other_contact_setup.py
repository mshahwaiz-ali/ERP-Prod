# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id

OTHER_CONTACT_PCAT_EXCLUDE = frozenset({"11", "12", "13"})


class OtherContactSetup(Document):
	def before_insert(self):
		assign_numeric_id(self, "contactid")

	def validate(self):
		pcat = str(self.pcat_id or "").strip()
		if pcat in OTHER_CONTACT_PCAT_EXCLUDE:
			frappe.throw(
				"Broker, Supplier and Customer categories use Party Setup — pick another category"
			)
		if self.pcat_id and not frappe.db.exists("Party Category", self.pcat_id):
			frappe.throw(f"Party Category {self.pcat_id} not found in master setup")
		if self.cityid and not frappe.db.exists("City Setup", self.cityid):
			frappe.throw(f"City {self.cityid} not found in master setup")
