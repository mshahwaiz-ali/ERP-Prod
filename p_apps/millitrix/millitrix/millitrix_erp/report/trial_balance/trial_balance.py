# Copyright (c) 2026, Millitrix and contributors
# Oracle Trial_Balance.RDF

from __future__ import annotations

from frappe.utils import flt

from millitrix.utils.gl_reports import get_trial_balance_rows
from millitrix.utils.report_columns import trial_balance_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return trial_balance_columns(), get_data(filters)


def get_data(filters):
	rows = get_trial_balance_rows(filters)
	if filters.get("accid"):
		rows = [row for row in rows if row.get("accid") == filters["accid"]]
	if not filters.get("show_zero_values"):
		rows = [
			row
			for row in rows
			if any(
				flt(row.get(field))
				for field in (
					"opening_debit",
					"opening_credit",
					"debit",
					"credit",
					"closing_debit",
					"closing_credit",
				)
			)
		]
	return rows
