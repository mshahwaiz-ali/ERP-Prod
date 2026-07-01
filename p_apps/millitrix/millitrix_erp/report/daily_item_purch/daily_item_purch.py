# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from millitrix.utils.extended_reports import get_daily_item_purch_rows
from millitrix.utils.report_columns import daily_item_purch_columns
from millitrix.utils.report_filters import normalize_report_dates
from frappe import _

def execute(filters=None):
	return daily_item_purch_columns(), get_daily_item_purch_rows(normalize_report_dates(filters))
