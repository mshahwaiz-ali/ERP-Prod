# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from frappe import _
from frappe.utils import flt

from millitrix.utils.finance_reports import get_balance_sheet_rows
from millitrix.utils.report_columns import trial_style_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	columns = get_columns()
	rows = get_balance_sheet_rows(filters)
	if not filters.get("show_zero_values"):
		rows = [
			row
			for row in rows
			if any(flt(row.get(f)) for f in ("closing_debit", "closing_credit", "debit", "credit"))
		]
	return columns, rows


def get_columns():
	columns = trial_style_columns(include_nature=True)
	if not any(col.get("fieldname") == "statement_line" for col in columns):
		columns.insert(0, {"label": _("Statement Line"), "fieldname": "statement_line", "fieldtype": "Data", "width": 180})
	return columns
