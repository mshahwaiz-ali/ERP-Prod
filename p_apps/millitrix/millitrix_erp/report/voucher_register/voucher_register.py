# Copyright (c) 2026, Millitrix and contributors
# Oracle VoucherRegister.RDF

from __future__ import annotations

from millitrix.utils.gl_reports import get_voucher_register_rows
from millitrix.utils.report_columns import voucher_register_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return voucher_register_columns(), get_voucher_register_rows(normalize_report_dates(filters))
