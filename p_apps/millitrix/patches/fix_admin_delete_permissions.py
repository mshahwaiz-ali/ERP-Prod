# Copyright (c) 2026, Millitrix and contributors
# Restore Delete / Submit / Cancel on desk for Administrator and admin roles.

from __future__ import annotations

import frappe



def execute() -> None:
	frappe.clear_cache()
