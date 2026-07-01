# Copyright (c) 2026, Millitrix and contributors
# Oracle ItemDailyStock.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_item_daily_stock_rows
from millitrix.utils.report_columns import item_daily_stock_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return item_daily_stock_columns(), get_item_daily_stock_rows(normalize_report_dates(filters))
