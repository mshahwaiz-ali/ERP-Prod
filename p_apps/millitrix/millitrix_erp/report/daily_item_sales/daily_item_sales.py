# Copyright (c) 2026, Millitrix and contributors
# Oracle DailyItemSales.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_daily_item_sales_rows
from millitrix.utils.report_columns import daily_item_sales_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return daily_item_sales_columns(), get_daily_item_sales_rows(normalize_report_dates(filters))
