# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.api.permissions import require_permission
from millitrix.utils.para_form_launcher import (
	execute_para_report,
	get_para_defaults,
	save_para_parameters,
)


@frappe.whitelist()
def get_defaults(form_key: str):
	require_permission("Report Parameter", "read")
	return get_para_defaults(form_key)


@frappe.whitelist()
def save_condition(form_key: str, payload=None):
	require_permission("Report Parameter", "write")
	return save_para_parameters(form_key, payload or {})


@frappe.whitelist()
def execute(form_key: str, payload=None):
	return execute_para_report(form_key, payload or {})
