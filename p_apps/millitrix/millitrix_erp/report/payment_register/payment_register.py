# Copyright (c) 2026, Millitrix and contributors
# Oracle Payment_Register.rep

from __future__ import annotations

from millitrix.utils.finance_reports import get_payment_register_detail_rows
from millitrix.utils.report_columns import payment_register_detail_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return payment_register_detail_columns(), get_payment_register_detail_rows(filters, receipt=False)
