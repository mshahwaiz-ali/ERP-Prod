# Copyright (c) 2026, Millitrix and contributors
# Oracle BrokerLedgerSummary.RDF

from __future__ import annotations

from frappe import _

from millitrix.utils.final_reports import get_broker_ledger_summary_rows
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return get_columns(), get_broker_ledger_summary_rows(normalize_report_dates(filters))


def get_columns():
	return [
		{"label": _("Broker"), "fieldname": "partyid", "fieldtype": "Link", "options": "Party", "width": 130},
		{"label": _("Broker Name"), "fieldname": "party_name", "fieldtype": "Data", "width": 180},
		{"label": _("Opening"), "fieldname": "opening_balance", "fieldtype": "Currency", "width": 110},
		{"label": _("Purchase"), "fieldname": "purchase", "fieldtype": "Currency", "width": 110},
		{"label": _("Sales"), "fieldname": "sales", "fieldtype": "Currency", "width": 110},
		{"label": _("Advance"), "fieldname": "advance", "fieldtype": "Currency", "width": 110},
		{"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "width": 110},
		{"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 110},
		{"label": _("Payment"), "fieldname": "payment", "fieldtype": "Currency", "width": 110},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120},
	]
