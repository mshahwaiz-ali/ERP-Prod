# Copyright (c) 2026, Millitrix and contributors
# Oracle SOInvDetail.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_so_inv_detail_rows
from millitrix.utils.report_columns import so_inv_detail_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return so_inv_detail_columns(), get_so_inv_detail_rows(normalize_report_dates(filters))
