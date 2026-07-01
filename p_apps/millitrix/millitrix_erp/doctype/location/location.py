# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class Location(Document):
	def before_insert(self):
		assign_numeric_id(self, "location_id")

	def after_insert(self):
		_default_location_for_current_user(self.name)


def _default_location_for_current_user(location_id: str) -> None:
	"""First Location created → assign to current user's User Rights if blank."""
	from millitrix.utils.user_permissions import get_mill_user

	mill_user = get_mill_user()
	if not mill_user or mill_user.location_id:
		return

	frappe.db.set_value("User Rights", mill_user.name, "location_id", location_id, update_modified=False)
	if getattr(mill_user, "erp_user", None):
		frappe.cache.hdel("millitrix_user_permissions", f"mill_user::{mill_user.erp_user}")
