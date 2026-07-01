# Copyright (c) 2026, Millitrix and contributors

import frappe


def after_install():
	"""Make the default desk app on this site."""

	for role in ("Millitrix ERP Manager", "Millitrix ERP User"):
		if not frappe.db.exists("Role", role):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role,
				"desk_access": 1
			}).insert(ignore_permissions=True)

	frappe.db.set_single_value("System Settings", "default_app", "millitrix")
	frappe.db.set_default("desktop:home_page", "millitrix")

	if frappe.db.exists("Installed Application", {"app_name": "millitrix"}):
		name = frappe.db.get_value(
			"Installed Application",
			{"app_name": "millitrix"},
			"name"
		)
		frappe.db.set_value(
			"Installed Application",
			name,
			{
				"has_setup_wizard": 0,
				"is_setup_complete": 1,
			},
		)

	# client system removed → admin-only setup
	# from millitrix.utils.client_access import ensure_client_user, sanitize_administrator_user
	# sanitize_administrator_user()
	# ensure_client_user()

	# frappe.db.commit()  # SAFE MODE DISABLED


def cleanup_old_mill_module():
	"""Remove leftover Mill ERP module records after rebrand."""

	old_doctypes = frappe.get_all(
		"DocType",
		filters={"module": "Mill ERP"},
		pluck="name"
	)

	for name in old_doctypes:
		frappe.db.delete("DocField", {"parent": name, "parenttype": "DocType"})
		frappe.db.delete("DocPerm", {"parent": name, "parenttype": "DocType"})
		frappe.db.delete("DocType", {"name": name})

	if frappe.db.exists("Module Def", "Mill ERP"):
		frappe.db.delete("Module Def", {"name": "Mill ERP"})

	for role in ("Mill ERP Manager", "Mill ERP User"):
		if frappe.db.exists("Role", role):
			frappe.delete_doc("Role", role, force=1, ignore_permissions=True)

	# frappe.db.commit()  # SAFE MODE DISABLED