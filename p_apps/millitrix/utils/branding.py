# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

LOGO_URL = "/assets/millitrix/images/millitrix-logo.svg"
APP_NAME = "Millitrix"


def extend_bootinfo(bootinfo):
	"""Always serve Millitrix logo in desk (overrides stale boot cache)."""
	bootinfo["app_logo_url"] = LOGO_URL


def apply_branding():
	frappe.db.set_single_value("System Settings", "app_name", APP_NAME)
	frappe.db.set_single_value("Website Settings", "app_name", APP_NAME)
	frappe.db.set_single_value("Website Settings", "app_logo", LOGO_URL)
	frappe.db.set_single_value("Website Settings", "favicon", LOGO_URL)
	frappe.db.set_single_value("Website Settings", "splash_image", LOGO_URL)
	frappe.db.set_single_value("Navbar Settings", "app_logo", LOGO_URL)
	frappe.cache.delete_key("bootinfo")
	frappe.clear_cache()
	# frappe.db.commit()  # DISABLED SAFE MODE
