# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from frappe import _
from millitrix.utils.report_columns import po_summary_columns
from millitrix.utils.report_filters import normalize_report_dates
from millitrix.utils.trading_reports import get_po_summary_rows

def execute(filters=None):
	filters = normalize_report_dates(filters)
	return po_summary_columns(), get_po_summary_rows(filters)
