# Copyright (c) 2026, Millitrix and contributors
# Oracle MonthlyItemPurch.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_monthly_item_purch_rows
from millitrix.utils.report_columns import monthly_item_purch_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return monthly_item_purch_columns(), get_monthly_item_purch_rows(normalize_report_dates(filters))
