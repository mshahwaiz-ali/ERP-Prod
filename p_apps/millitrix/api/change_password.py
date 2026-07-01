# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.core.doctype.user.user import _update_password
from frappe.utils import cint


@frappe.whitelist()
def set_user_password(user: str, new_password: str, logout_all_sessions: int = 0) -> None:
	"""Allow Millitrix managers to reset another user's password (Oracle Change User Password)."""
	if not (
		frappe.has_permission("User", "write")
		or "System Manager" in frappe.get_roles()
		or "Millitrix ERP Manager" in frappe.get_roles()
	):
		frappe.throw(_("Not permitted to change password for other users"), frappe.PermissionError)

	if not user:
		frappe.throw(_("User Id is required"))
	if not frappe.db.exists("User", user):
		frappe.throw(_("User {0} does not exist").format(user))

	_update_password(user, new_password, logout_all_sessions=cint(logout_all_sessions))
