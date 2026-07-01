# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _


def require_permission(doctype: str, ptype: str = "read") -> None:
	if not frappe.has_permission(doctype, ptype):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
