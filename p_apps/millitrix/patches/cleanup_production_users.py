# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe


PROTECTED_USERS = {
	"Administrator",
	"Guest",
	"All",
}

CLIENT_USER_CANDIDATES = {
	"client@millitrix.local",
	"demo@millitrix.local",
	"millitrix.client@local",
	"millitrix-client@local",
	"client@example.com",
}


def _is_safe_client_user(user: str) -> bool:
	if not user or user in PROTECTED_USERS:
		return False
	if user not in CLIENT_USER_CANDIDATES and not user.lower().startswith("client@millitrix"):
		return False
	if not frappe.db.exists("User", user):
		return False
	return not frappe.get_all(
		"Has Role",
		filters={
			"parent": user,
			"parenttype": "User",
			"role": ["in", ["System Manager", "Administrator"]],
		},
		limit=1,
	)


def execute() -> None:
	for user in sorted(CLIENT_USER_CANDIDATES):
		if not _is_safe_client_user(user):
			continue
		frappe.db.set_value(
			"User",
			user,
			{"enabled": 0},
			update_modified=False,
		)
		frappe.clear_cache(user=user)
