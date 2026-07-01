# Copyright (c) 2026, Millitrix and contributors
# Oracle PNL.RDF

from __future__ import annotations

from frappe.utils import flt

from millitrix.utils.finance_reports import get_pnl_report_rows
from millitrix.utils.report_columns import pnl_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	rows = get_pnl_report_rows(filters)
	if not filters.get("show_zero_values"):
		rows = [
			row
			for row in rows
			if any(
				flt(row.get(f))
				for f in ("opening_balance", "debit", "credit", "balance")
			)
		]
	return pnl_columns(), rows
