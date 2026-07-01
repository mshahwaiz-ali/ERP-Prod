# Copyright (c) 2026, Millitrix and contributors
# Oracle PurchItemSummary.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_purch_item_summary_rows
from millitrix.utils.report_columns import purch_item_summary_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return purch_item_summary_columns(), get_purch_item_summary_rows(normalize_report_dates(filters))
