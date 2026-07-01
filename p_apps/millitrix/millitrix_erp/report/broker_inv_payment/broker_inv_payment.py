# Copyright (c) 2026, Millitrix and contributors
# Oracle BrokerInvPayment.RDF

from __future__ import annotations

from frappe import _

from millitrix.utils.final_reports import get_broker_inv_payment_register_rows
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return get_columns(), get_broker_inv_payment_register_rows(normalize_report_dates(filters))


def get_columns():
	return [
		{"label": _("Type"), "fieldname": "row_type", "fieldtype": "Data", "width": 80},
		{"label": _("Inv Type"), "fieldname": "inv_type", "fieldtype": "Data", "width": 80},
		{"label": _("Doc No"), "fieldname": "doc_no", "fieldtype": "Data", "width": 110},
		{"label": _("Doc Date"), "fieldname": "doc_date", "fieldtype": "Date", "width": 110},
		{"label": _("Location"), "fieldname": "location_id", "fieldtype": "Link", "options": "Location", "width": 120},
		{"label": _("Party"), "fieldname": "partyid", "fieldtype": "Link", "options": "Party", "width": 130},
		{"label": _("Party Name"), "fieldname": "party_name", "fieldtype": "Data", "width": 160},
		{"label": _("Broker"), "fieldname": "brokerid", "fieldtype": "Link", "options": "Party", "width": 130},
		{"label": _("Broker Name"), "fieldname": "broker_name", "fieldtype": "Data", "width": 160},
		{"label": _("Item"), "fieldname": "itemcode", "fieldtype": "Link", "options": "Item Setup", "width": 120},
		{"label": _("Doc Amount"), "fieldname": "doc_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Paid"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Mode"), "fieldname": "pnrmode", "fieldtype": "Data", "width": 90},
		{"label": _("Refer No"), "fieldname": "referno", "fieldtype": "Data", "width": 100},
		{"label": _("Brokery"), "fieldname": "brokery", "fieldtype": "Data", "width": 80},
	]
