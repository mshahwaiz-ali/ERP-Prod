# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.utils.client_access import ensure_client_user


def execute():
	ensure_client_user()
	frappe.db.set_single_value("System Settings", "default_app", "millitrix")
	frappe.db.commit()
