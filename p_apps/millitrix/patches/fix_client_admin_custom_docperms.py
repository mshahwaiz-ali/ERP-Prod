# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe


FULL_ACCESS_ROLES = ("System Manager", "Millitrix ERP Manager")


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


def _ensure_docperm(doctype: str, role: str) -> None:
	if frappe.db.exists("DocPerm", {"parent": doctype, "parenttype": "DocType", "role": role}):
		return
	meta = frappe.get_meta("DocPerm")
	doc = frappe.new_doc("DocPerm")
	doc.parent = doctype
	doc.parenttype = "DocType"
	doc.parentfield = "permissions"
	doc.role = role
	for field in ("read", "write", "create", "delete", "submit", "cancel", "amend", "report", "export", "print", "email", "share"):
		if meta.has_field(field):
			setattr(doc, field, 1)
	doc.insert(ignore_permissions=True)


def execute() -> None:
	for role in FULL_ACCESS_ROLES:
		_ensure_role(role)

	for doctype in frappe.get_all("DocType", filters={"module": "Millitrix ERP"}, pluck="name"):
		for role in FULL_ACCESS_ROLES:
			_ensure_docperm(doctype, role)

	frappe.clear_cache()
