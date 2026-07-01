# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from millitrix.utils.extended_reports import get_cash_flow_rows
from millitrix.utils.report_filters import normalize_report_dates
from frappe import _

def execute(filters=None):
	return get_columns(), get_cash_flow_rows(normalize_report_dates(filters))

def get_columns():
	return [
		{"label": _("Cash/Bank"), "fieldname": "cash_flow", "fieldtype": "Data", "width": 80},
		{"label": _("Date"), "fieldname": "vouchdate", "fieldtype": "Date", "width": 100},
		{"label": _("Voucher No"), "fieldname": "voucherno", "fieldtype": "Data", "width": 110},
		{"label": _("Location"), "fieldname": "location_id", "fieldtype": "Link", "options": "Location", "width": 130},
		{"label": _("Account"), "fieldname": "accid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 120},
		{"label": _("Account Name"), "fieldname": "account_name", "fieldtype": "Data", "width": 160},
		{"label": _("Cash Desc"), "fieldname": "cash_desc", "fieldtype": "Data", "width": 180},
		{"label": _("Acc Desc"), "fieldname": "acc_desc", "fieldtype": "Data", "width": 180},
		{"label": _("Party"), "fieldname": "partyid", "fieldtype": "Link", "options": "Party", "width": 140},
		{"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "width": 110},
		{"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 110},
		{"label": _("Narration"), "fieldname": "narration", "fieldtype": "Data", "width": 180},
	]
