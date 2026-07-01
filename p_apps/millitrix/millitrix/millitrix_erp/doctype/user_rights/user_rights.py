# Copyright (c) 2026, Millitrix and contributors
# For license information, see license.txt

import frappe
from frappe.model.document import Document

from millitrix.api.permissions import require_permission
from millitrix.utils.naming import assign_numeric_id


@frappe.whitelist()
def load_all_modules():
	require_permission("User Rights", "read")
	return frappe.get_all(
		"Module",
		fields=["moduleid", "module"],
		order_by="moduleid asc",
	)


class UserRights(Document):

	def before_insert(self):
		assign_numeric_id(self, "userid")

	def validate(self):
		self._sync_primary_location()
		if self.empno and not self.username:
			self.username = frappe.db.get_value("Employee Setup", self.empno, "ename") or self.username

	def _sync_primary_location(self):
		"""Keep user_locations in sync with header location (Oracle User_Locations)."""
		if not self.location_id:
			return
		locations = [row.location_id for row in (self.user_locations or []) if row.location_id]
		if self.location_id not in locations:
			row = self.append("user_locations", {})
			row.location_id = self.location_id
