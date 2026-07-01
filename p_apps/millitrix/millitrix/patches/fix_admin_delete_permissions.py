# Copyright (c) 2026, Millitrix and contributors
# Restore Delete / Submit / Cancel on desk for Administrator and admin roles.

from __future__ import annotations

import frappe

from millitrix.utils.client_access import _sync_client_millitrix_permissions


def execute() -> None:
	_sync_client_millitrix_permissions()
	frappe.clear_cache()
