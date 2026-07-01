# Copyright (c) 2026, Millitrix and contributors
# Oracle SISummary.RDF

from __future__ import annotations

from millitrix.utils.report_columns import si_summary_columns
from millitrix.utils.report_filters import normalize_report_dates
from millitrix.utils.trading_reports import get_si_summary_rows


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return si_summary_columns(), get_si_summary_rows(filters)
