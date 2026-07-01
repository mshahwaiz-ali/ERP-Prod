# Copyright (c) 2026, Millitrix and contributors
"""Remove legacy workspace names and keep child pages under Millitrix root."""

from __future__ import annotations

import frappe

from millitrix.utils.workspace_layout import OBSOLETE_WORKSPACE_LABELS, ROOT_TITLE


def execute():
	for name in OBSOLETE_WORKSPACE_LABELS + ("Millitrix Millitrix",):
		if frappe.db.exists("Workspace", name):
			frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)

	for name in frappe.get_all(
		"Workspace",
		filters={"module": "Millitrix ERP", "name": ["!=", ROOT_TITLE]},
		pluck="name",
	):
		frappe.db.set_value("Workspace", name, "parent_page", ROOT_TITLE, update_modified=False)

	frappe.db.commit()
	frappe.clear_cache()
