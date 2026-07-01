# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.api.permissions import require_permission
from millitrix.utils.gl_parameter_form import (
	execute_gl_para_report,
	get_gl_para_defaults,
	save_gl_para_parameters,
)


@frappe.whitelist()
def get_defaults():
	require_permission("Report Parameter", "read")
	return get_gl_para_defaults()


@frappe.whitelist()
def save_condition(payload=None):
	require_permission("Report Parameter", "write")
	return save_gl_para_parameters(payload or {})


@frappe.whitelist()
def execute(payload=None):
	return execute_gl_para_report(payload or {})
