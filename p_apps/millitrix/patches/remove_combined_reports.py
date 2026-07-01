# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe


def execute():
	"""Remove merged reports replaced by Oracle-named split reports."""
	for name in (
		"Millitrix CNB Register",
		"Advance Adjustment Register",
		"Millitrix PNR Register",
	):
		if frappe.db.exists("Report", name):
			frappe.delete_doc("Report", name, force=1, ignore_permissions=True)
	# frappe.db.commit()  # DISABLED SAFE MODE
