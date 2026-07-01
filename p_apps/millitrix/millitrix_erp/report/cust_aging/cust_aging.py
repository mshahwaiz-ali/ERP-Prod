# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from millitrix.utils.extended_reports import get_cust_aging_rows
from frappe import _
from frappe.utils import getdate

def execute(filters=None):
	filters = dict(filters or {})
	if filters.get("as_of_date"):
		filters["as_of_date"] = str(getdate(filters["as_of_date"]))
	return get_columns(), get_cust_aging_rows(filters)

def get_columns():
	return [
		{"label": _("Party"), "fieldname": "partyid", "fieldtype": "Link", "options": "Party", "width": 140},
		{"label": _("Party Name"), "fieldname": "party_name", "fieldtype": "Data", "width": 180},
		{"label": _("Location"), "fieldname": "location_id", "fieldtype": "Link", "options": "Location", "width": 130},
		{"label": _("0-30 Days"), "fieldname": "current", "fieldtype": "Currency", "width": 110},
		{"label": _("31-60 Days"), "fieldname": "days_31_60", "fieldtype": "Currency", "width": 110},
		{"label": _("61-90 Days"), "fieldname": "days_61_90", "fieldtype": "Currency", "width": 110},
		{"label": _("Over 90 Days"), "fieldname": "over_90", "fieldtype": "Currency", "width": 110},
		{"label": _("Total Outstanding"), "fieldname": "total_outstanding", "fieldtype": "Currency", "width": 130},
	]
