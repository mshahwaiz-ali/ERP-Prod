# Copyright (c) 2026, Millitrix and contributors
# Oracle UnSubmit_Stock.RDF

from __future__ import annotations

from millitrix.utils.report_columns import unsubmit_stock_columns
from millitrix.utils.report_filters import normalize_report_dates
from millitrix.utils.stock_reports import get_unsubmit_stock_rows


def execute(filters=None):
	return unsubmit_stock_columns(), get_unsubmit_stock_rows(normalize_report_dates(filters or {}))
