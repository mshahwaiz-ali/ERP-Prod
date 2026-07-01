# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.utils.erpnext_compat import get_session_location
from millitrix.utils.user_permissions import (
	bypasses_mill_permissions,
	get_default_store,
	get_mill_user,
	get_user_locations,
	get_user_stores,
)


@frappe.whitelist()
def get_report_parameter_defaults() -> dict:
	"""Defaults for new Report Parameter rows (session location, user, dates)."""
	from frappe.utils import add_months, today

	from millitrix.utils.erpnext_compat import get_session_location
	from millitrix.utils.para_form_launcher import _resolve_userid

	from_date, to_date = str(add_months(today(), -1)), str(today())
	out: dict = {
		"location_id": get_session_location(),
		"from_date": from_date,
		"to_date": to_date,
	}
	userid = _resolve_userid(required=False)
	if userid:
		out["userid"] = userid
	return out


@frappe.whitelist()
def get_saved_filters_for_report(report_name: str) -> dict:
	"""Saved Report Parameter cache for a query report (para-form module)."""
	from millitrix.utils.para_form_launcher import get_saved_filters_for_report as _load

	return _load(report_name) or {}


@frappe.whitelist()
def get_user_scope() -> dict:
	"""Return User Rights location/store scope for form defaults."""
	if bypasses_mill_permissions():
		return {
			"bypass": True,
			"location_id": get_session_location(),
			"default_store": None,
			"allowed_stores": [],
			"allowed_locations": [],
		}

	mill_user = get_mill_user()
	if not mill_user:
		return {
			"bypass": False,
			"location_id": None,
			"default_store": None,
			"allowed_stores": [],
			"allowed_locations": [],
		}

	locations = get_user_locations(mill_user)
	return {
		"bypass": False,
		"location_id": mill_user.location_id or (locations[0] if locations else None),
		"default_store": get_default_store(mill_user),
		"allowed_stores": get_user_stores(mill_user),
		"allowed_locations": locations,
	}
