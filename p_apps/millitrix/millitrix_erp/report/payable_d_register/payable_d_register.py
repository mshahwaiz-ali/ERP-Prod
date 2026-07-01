# Copyright (c) 2026, Millitrix and contributors
# Oracle PayableDRegister.rep

from __future__ import annotations

from millitrix.utils.finance_reports import get_discount_pnr_register_rows
from millitrix.utils.report_columns import discount_pnr_register_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return discount_pnr_register_columns(payment=True), get_discount_pnr_register_rows(filters, flow="payment")
