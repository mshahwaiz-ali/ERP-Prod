# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.utils.client_access import _remove_client_admin_custom_docperms


def execute() -> None:
	_remove_client_admin_custom_docperms()
	frappe.clear_cache()
