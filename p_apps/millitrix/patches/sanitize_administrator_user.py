# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe


ADMIN_ROLES = ("System Manager", "Millitrix ERP Manager")


def _ensure_role(role_name: str) -> None:
	if frappe.db.exists("Role", role_name):
		return
	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": role_name,
			"desk_access": 1,
		}
	).insert(ignore_permissions=True)


def _ensure_user_role(user: str, role_name: str) -> None:
	if not frappe.db.exists("User", user):
		return
	if frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": role_name}):
		return
	frappe.get_doc(
		{
			"doctype": "Has Role",
			"parent": user,
			"parenttype": "User",
			"parentfield": "roles",
			"role": role_name,
		}
	).insert(ignore_permissions=True)


def execute() -> None:
	if not frappe.db.exists("User", "Administrator"):
		return

	for role in ADMIN_ROLES:
		_ensure_role(role)
		_ensure_user_role("Administrator", role)

	frappe.db.set_value(
		"User",
		"Administrator",
		{
			"enabled": 1,
			"user_type": "System User",
		},
		update_modified=False,
	)
	frappe.clear_cache(user="Administrator")
