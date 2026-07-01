# Copyright (c) 2026, Millitrix and contributors
# Oracle Expanse_Register.RDF — Expense Voucher (EV) register

from __future__ import annotations

from millitrix.utils.extended_reports import get_expense_register_rows
from millitrix.utils.report_filters import normalize_report_dates
from frappe import _


def execute(filters=None):
	return get_columns(), get_expense_register_rows(normalize_report_dates(filters))


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "doc_date", "fieldtype": "Date", "width": 100},
		{"label": _("Voucher No"), "fieldname": "documentid", "fieldtype": "Data", "width": 110},
		{"label": _("Location"), "fieldname": "location_id", "fieldtype": "Link", "options": "Location", "width": 130},
		{"label": _("Cash/Bank"), "fieldname": "description", "fieldtype": "Data", "width": 140},
		{"label": _("Refer No"), "fieldname": "referno", "fieldtype": "Data", "width": 110},
		{"label": _("Refer Date"), "fieldname": "referdate", "fieldtype": "Date", "width": 100},
		{"label": _("Instrument"), "fieldname": "instrument", "fieldtype": "Data", "width": 110},
		{"label": _("Doc Amount"), "fieldname": "doc_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Acc Desc"), "fieldname": "acc_desc", "fieldtype": "Data", "width": 180},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Detail"), "fieldname": "detail", "fieldtype": "Data", "width": 180},
		{"label": _("Narration"), "fieldname": "narration", "fieldtype": "Data", "width": 180},
	]
