# Copyright (c) 2026, Millitrix and contributors
# Oracle CrashRefine.RDF

from __future__ import annotations

from frappe import _

from millitrix.utils.report_filters import normalize_report_dates
from millitrix.utils.stock_reports import get_crash_refine_report_rows


def execute(filters=None):
	return get_columns(), get_crash_refine_report_rows(normalize_report_dates(filters))


def get_columns():
	return [
		{"label": _("Crash ID"), "fieldname": "crashid", "fieldtype": "Data", "width": 110},
		{"label": _("Date"), "fieldname": "crdate", "fieldtype": "Date", "width": 100},
		{"label": _("Mill"), "fieldname": "mill_id", "fieldtype": "Link", "options": "Location", "width": 100},
		{"label": _("Location"), "fieldname": "location_id", "fieldtype": "Link", "options": "Location", "width": 130},
		{"label": _("Line Type"), "fieldname": "line_type", "fieldtype": "Data", "width": 80},
		{"label": _("Store"), "fieldname": "storeid", "fieldtype": "Link", "options": "Store Setup", "width": 130},
		{"label": _("Item"), "fieldname": "itemcode", "fieldtype": "Link", "options": "Item Setup", "width": 130},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 160},
		{"label": _("Bag Item"), "fieldname": "crbagid", "fieldtype": "Link", "options": "Item Setup", "width": 120},
		{"label": _("Bag Name"), "fieldname": "bag_name", "fieldtype": "Data", "width": 140},
		{"label": _("Bags"), "fieldname": "bagqty", "fieldtype": "Float", "width": 80},
		{"label": _("Per Bag"), "fieldname": "bagweight", "fieldtype": "Float", "width": 80},
		{"label": _("Weight"), "fieldname": "weight", "fieldtype": "Float", "width": 90},
		{"label": _("Bag Dust"), "fieldname": "bagdust", "fieldtype": "Float", "width": 80},
		{"label": _("Ref. Weight"), "fieldname": "ref_weight", "fieldtype": "Float", "width": 90},
		{"label": _("Dip"), "fieldname": "dip", "fieldtype": "Float", "width": 70},
		{"label": _("Prod. 1"), "fieldname": "prod_1", "fieldtype": "Data", "width": 80},
		{"label": _("Prod. 2"), "fieldname": "prod_2", "fieldtype": "Data", "width": 80},
		{"label": _("Prod Item"), "fieldname": "proditem", "fieldtype": "Link", "options": "Item Setup", "width": 120},
		{"label": _("Prod Name"), "fieldname": "proditem_name", "fieldtype": "Data", "width": 140},
		{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 90},
	]
