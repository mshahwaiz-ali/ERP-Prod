# Copyright (c) 2026, Millitrix and contributors
# Restore Frappe built-in Administrator — strip Millitrix Client and ERPNext role bleed.

from __future__ import annotations

import frappe

from millitrix.utils.client_access import sanitize_administrator_user


def execute() -> None:
	sanitize_administrator_user()
	frappe.clear_cache()
