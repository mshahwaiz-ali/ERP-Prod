# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe


@frappe.whitelist()
def get_defaults():
	"""Default location for the wizard form."""
	rows = frappe.get_all("Location", pluck="name", limit=1, order_by="creation asc")
	return {"location_id": rows[0] if rows else None}
