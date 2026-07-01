# Copyright (c) 2026, Millitrix and contributors
# Oracle MonthlyItemSales.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_monthly_item_sales_rows
from millitrix.utils.report_columns import monthly_item_sales_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return monthly_item_sales_columns(), get_monthly_item_sales_rows(normalize_report_dates(filters))
