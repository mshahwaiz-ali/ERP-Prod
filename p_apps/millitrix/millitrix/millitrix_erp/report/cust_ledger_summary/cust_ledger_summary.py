# Copyright (c) 2026, Millitrix and contributors
# Oracle CustLedgerSummary.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_cust_ledger_summary_rows
from millitrix.utils.report_filters import normalize_report_dates
from frappe import _


def execute(filters=None):
	return get_columns(), get_cust_ledger_summary_rows(normalize_report_dates(filters))


def get_columns():
	return [
		{"label": _("Party"), "fieldname": "partyid", "fieldtype": "Link", "options": "Party", "width": 140},
		{"label": _("Party Name"), "fieldname": "party_name", "fieldtype": "Data", "width": 180},
		{"label": _("Opening"), "fieldname": "opening_balance", "fieldtype": "Currency", "width": 120},
		{"label": _("Debit"), "fieldname": "total_debit", "fieldtype": "Currency", "width": 120},
		{"label": _("Credit"), "fieldname": "total_credit", "fieldtype": "Currency", "width": 120},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120},
	]
