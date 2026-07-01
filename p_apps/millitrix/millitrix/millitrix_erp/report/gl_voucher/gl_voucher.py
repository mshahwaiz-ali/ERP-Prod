# Copyright (c) 2026, Millitrix and contributors
# Oracle GLVoucher.RDF — all GL voucher lines

from __future__ import annotations

from millitrix.utils.gl_reports import get_gl_voucher_rows
from millitrix.utils.report_columns import gl_voucher_line_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return gl_voucher_line_columns(), get_gl_voucher_rows(normalize_report_dates(filters))
