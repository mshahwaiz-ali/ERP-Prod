# Copyright (c) 2026, Millitrix and contributors
# Oracle AdvRAdjustReg.rep — Receivable Advance Adjustment register.

from __future__ import annotations

from millitrix.utils.finance_reports import get_advance_adjustment_register
from millitrix.utils.report_columns import advance_adjustment_register_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return advance_adjustment_register_columns(payment=False), get_advance_adjustment_register(
		filters, received=True
	)
