# Copyright (c) 2026, Millitrix and contributors
# Oracle GJ.RDF — General Journal (manual Voucher Transaction)

from __future__ import annotations

from millitrix.utils.gl_reports import get_gj_rows
from millitrix.utils.report_columns import gj_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return gj_columns(), get_gj_rows(normalize_report_dates(filters))
