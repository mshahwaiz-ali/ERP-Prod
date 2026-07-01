# Copyright (c) 2026, Millitrix and contributors
# Oracle Account_Balance.RDF — closing balances with Dr/Cr side

from __future__ import annotations

from frappe import _

from millitrix.utils.gl_reports import get_account_balance_rows
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return get_columns(), get_account_balance_rows(filters)


def get_columns():
	return [
		{"label": _("Account"), "fieldname": "accid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 120},
		{"label": _("Account Name"), "fieldname": "account_name", "fieldtype": "Data", "width": 220},
		{"label": _("Type"), "fieldname": "nature", "fieldtype": "Data", "width": 100},
		{"label": _("Closing Debit"), "fieldname": "closing_debit", "fieldtype": "Currency", "width": 120},
		{"label": _("Closing Credit"), "fieldname": "closing_credit", "fieldtype": "Currency", "width": 120},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120},
		{"label": _("Dr/Cr"), "fieldname": "balance_side", "fieldtype": "Data", "width": 70},
	]
