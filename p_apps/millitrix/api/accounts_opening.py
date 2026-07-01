# Accounts Opening — detail lines from Item / Employee / Party Link fields on grid rows.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _

from millitrix.api.permissions import require_permission
from millitrix.utils.gl_opening_lines import get_opening_lines


@frappe.whitelist()
def get_detail_lines(entry_mode: str, entity_id: str) -> list[dict]:
	"""Return GL Opening detail rows after Item / Employee / Party selection."""
	require_permission("Accounts Opening", "read")
	if not entry_mode or not entity_id:
		frappe.throw("entry_mode and entity_id are required")
	return get_opening_lines(entry_mode, str(entity_id))
