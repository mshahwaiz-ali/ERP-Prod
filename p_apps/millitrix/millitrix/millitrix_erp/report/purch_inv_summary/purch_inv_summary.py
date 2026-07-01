# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from millitrix.utils.extended_reports import get_purch_inv_summary_rows
from millitrix.utils.report_filters import normalize_report_dates
from frappe import _

def execute(filters=None):
	return get_columns(), get_purch_inv_summary_rows(normalize_report_dates(filters))

def get_columns():
	return [
		{"label": _("Location"), "fieldname": "location_id", "fieldtype": "Link", "options": "Location", "width": 130},
		{"label": _("Supplier"), "fieldname": "supplierid", "fieldtype": "Link", "options": "Party", "width": 160},
		{"label": _("Invoice Count"), "fieldname": "invoice_count", "fieldtype": "Int", "width": 100},
		{"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 120},
		{"label": _("Total Payable"), "fieldname": "total_payable", "fieldtype": "Currency", "width": 120},
	]
