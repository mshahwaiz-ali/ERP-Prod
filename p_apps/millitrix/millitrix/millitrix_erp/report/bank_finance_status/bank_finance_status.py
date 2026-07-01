# Copyright (c) 2026, Millitrix and contributors
# Oracle BankFinanceStatus.RDF

from __future__ import annotations

from frappe import _

from millitrix.utils.extended_reports import get_bank_finance_status_rows
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return get_columns(), get_bank_finance_status_rows(normalize_report_dates(filters))


def get_columns():
	return [
		{"label": _("Mill"), "fieldname": "mill_name", "fieldtype": "Data", "width": 140},
		{"label": _("Bank A/c No"), "fieldname": "bankaccid", "fieldtype": "Int", "width": 100},
		{"label": _("GL Account"), "fieldname": "accid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 120},
		{"label": _("Account Name"), "fieldname": "account_name", "fieldtype": "Data", "width": 180},
		{"label": _("Nature"), "fieldname": "ac_nature", "fieldtype": "Data", "width": 130},
		{"label": _("Opening"), "fieldname": "opening_balance", "fieldtype": "Currency", "width": 110},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 110},
		{"label": _("Dr/Cr"), "fieldname": "balance_side", "fieldtype": "Data", "width": 70},
		{"label": _("Limit"), "fieldname": "amntlimit", "fieldtype": "Currency", "width": 110},
		{"label": _("OD Balance"), "fieldname": "od_balance", "fieldtype": "Currency", "width": 120},
		{"label": _("Available"), "fieldname": "available", "fieldtype": "Currency", "width": 110},
	]
