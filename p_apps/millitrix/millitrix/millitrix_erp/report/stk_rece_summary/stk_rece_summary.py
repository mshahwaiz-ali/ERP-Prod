# Copyright (c) 2026, Millitrix and contributors
# Oracle StkRece_Summary.RDF

from __future__ import annotations

from millitrix.utils.final_reports import get_stk_rece_summary_rows
from millitrix.utils.report_columns import stk_rece_summary_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return stk_rece_summary_columns(), get_stk_rece_summary_rows(normalize_report_dates(filters))
