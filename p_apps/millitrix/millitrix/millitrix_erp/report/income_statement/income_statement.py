# Copyright (c) 2026, Millitrix and contributors
# Oracle IncomeStatement.RDF

from __future__ import annotations

from frappe.utils import flt

from millitrix.utils.finance_reports import get_income_statement_rows
from millitrix.utils.report_columns import trial_style_columns
from millitrix.utils.report_filters import normalize_report_dates
from frappe import _


def execute(filters=None):
	filters = normalize_report_dates(filters)
	columns = get_columns()
	rows = get_income_statement_rows(filters)
	if not filters.get("show_zero_values"):
		rows = [
			row
			for row in rows
			if any(
				flt(row.get(f))
				for f in (
					"opening_debit",
					"opening_credit",
					"debit",
					"credit",
					"closing_debit",
					"closing_credit",
				)
			)
		]
	return columns, rows


def get_columns():
	columns = trial_style_columns(include_nature=True)
	if not any(col.get("fieldname") == "statement_line" for col in columns):
		columns.insert(0, {"label": _("Statement Line"), "fieldname": "statement_line", "fieldtype": "Data", "width": 180})
	return columns
