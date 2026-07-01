# Copyright (c) 2026, Millitrix and contributors
# Shared filter definitions for Mill ERP script reports.

from __future__ import annotations

from frappe import _
from frappe.utils import add_months, getdate, today

MILL_REPORT_ROLES = [
	{"role": "System Manager"},
	{"role": "Millitrix ERP Manager"},
	{"role": "Millitrix ERP User"},
]


def default_date_range() -> tuple[str, str]:
	to_date = today()
	from_date = add_months(to_date, -1)
	return str(from_date), str(to_date)


def ensure_session_location(filters: dict) -> dict:
	"""Default location_id from user session (Oracle :Global.Location_Id)."""
	if filters.get("location_id"):
		return filters
	from millitrix.utils.erpnext_compat import get_session_location

	location_id = get_session_location()
	if location_id:
		filters["location_id"] = location_id
	return filters


def normalize_report_filters(filters: dict | None) -> dict:
	return ensure_session_location(dict(filters or {}))


def ensure_date_filters(filters: dict) -> dict:
	from_date, to_date = default_date_range()
	filters.setdefault("from_date", from_date)
	filters.setdefault("to_date", to_date)
	return ensure_session_location(filters)


def date_location_filter_defs() -> list[dict]:
	from millitrix.utils.erpnext_compat import get_session_location

	from_date, to_date = default_date_range()
	location_id = get_session_location()
	location_filter: dict = {
		"fieldname": "location_id",
		"label": _("Location"),
		"fieldtype": "Link",
		"options": "Location",
	}
	if location_id:
		location_filter["default"] = location_id
	return [
		{
			"fieldname": "from_date",
			"label": _("From Date"),
			"fieldtype": "Date",
			"default": from_date,
			"mandatory": 1,
		},
		{
			"fieldname": "to_date",
			"label": _("To Date"),
			"fieldtype": "Date",
			"default": to_date,
			"mandatory": 1,
		},
		location_filter,
	]


def stock_filter_defs() -> list[dict]:
	from millitrix.utils.erpnext_compat import get_session_location

	location_id = get_session_location()
	location_filter: dict = {
		"fieldname": "location_id",
		"label": _("Location"),
		"fieldtype": "Link",
		"options": "Location",
	}
	if location_id:
		location_filter["default"] = location_id
	return [
		location_filter,
		{
			"fieldname": "storeid",
			"label": _("Store"),
			"fieldtype": "Link",
			"options": "Store Setup",
		},
		{
			"fieldname": "itemcode",
			"label": _("Item"),
			"fieldtype": "Link",
			"options": "Item Setup",
		},
		{
			"fieldname": "partyid",
			"label": _("Party"),
			"fieldtype": "Link",
			"options": "Party",
		},
	]


def account_ledger_filter_defs() -> list[dict]:
	filters = date_location_filter_defs()
	filters.append(
		{
			"fieldname": "accid",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Chart of Accounting",
		}
	)
	return filters


def party_ledger_filter_defs() -> list[dict]:
	filters = date_location_filter_defs()
	filters.append(
		{
			"fieldname": "partyid",
			"label": _("Party"),
			"fieldtype": "Link",
			"options": "Party",
			"mandatory": 1,
		}
	)
	return filters


def apply_location_filter(rows: list[dict], filters: dict, field: str = "location_id") -> list[dict]:
	location = filters.get(field)
	if not location:
		return rows
	return [row for row in rows if row.get(field) == location]


def normalize_report_dates(filters: dict | None) -> dict:
	filters = dict(filters or {})
	if filters.get("from_date"):
		filters["from_date"] = str(getdate(filters["from_date"]))
	if filters.get("to_date"):
		filters["to_date"] = str(getdate(filters["to_date"]))
	return ensure_session_location(ensure_date_filters(filters))


def _report_parameter_name(location_id: str, userid: str, moduleid: str) -> str:
	return f"{location_id}-{userid}-{moduleid}"


def get_saved_report_parameters(
	location_id: str,
	userid: str,
	moduleid: str,
) -> dict:
	"""Load cached report filters (Oracle REPORT_PARA)."""
	import frappe

	name = _report_parameter_name(location_id, userid, moduleid)
	if not frappe.db.exists("Report Parameter", name):
		return {}
	row = frappe.db.get_value(
		"Report Parameter",
		name,
		["from_date", "to_date", "coa_level", "parameter_string"],
		as_dict=True,
	)
	if not row:
		return {}
	out: dict = {}
	if row.from_date:
		out["from_date"] = str(row.from_date)
	if row.to_date:
		out["to_date"] = str(row.to_date)
	if row.coa_level is not None:
		out["coa_level"] = row.coa_level
	if row.parameter_string:
		out["parameter_string"] = row.parameter_string
	return out


def save_report_parameters(
	location_id: str,
	userid: str,
	moduleid: str,
	filters: dict,
) -> str:
	"""Upsert Oracle-style report parameter cache for one user / module."""
	import time

	import frappe

	name = _report_parameter_name(location_id, userid, moduleid)
	payload = {
		"location_id": location_id,
		"userid": userid,
		"moduleid": moduleid,
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date"),
		"coa_level": filters.get("coa_level"),
		"parameter_string": filters.get("parameter_string"),
	}

	for attempt in range(3):
		try:
			return _upsert_report_parameter(name, payload)
		except frappe.QueryDeadlockError:
			frappe.db.rollback()
			if attempt == 2:
				raise
			time.sleep(0.05 * (attempt + 1))


def _upsert_report_parameter(name: str, payload: dict) -> str:
	import frappe

	if frappe.db.exists("Report Parameter", name):
		doc = frappe.get_doc("Report Parameter", name)
		doc.update(payload)
		doc.save(ignore_permissions=True)
		return doc.name

	try:
		doc = frappe.get_doc({"doctype": "Report Parameter", **payload})
		doc.insert(ignore_permissions=True)
		return doc.name
	except frappe.DuplicateEntryError:
		frappe.db.rollback()
		doc = frappe.get_doc("Report Parameter", name)
		doc.update(payload)
		doc.save(ignore_permissions=True)
		return doc.name


def merge_saved_report_filters(
	filters: dict | None,
	location_id: str,
	userid: str,
	moduleid: str,
) -> dict:
	"""Apply saved defaults without overwriting values already supplied."""
	merged = normalize_report_dates(filters)
	saved = get_saved_report_parameters(location_id, userid, moduleid)
	for key, value in saved.items():
		if value is not None and not merged.get(key):
			merged[key] = value
	return merged
