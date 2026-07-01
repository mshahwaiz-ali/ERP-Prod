# Copyright (c) 2026, Millitrix and contributors
# Oracle PartyPRegister.rep — Party Payment vouchers.

from __future__ import annotations

from millitrix.utils.finance_reports import get_party_voucher_register_rows
from millitrix.utils.report_columns import party_p_register_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return party_p_register_columns(), get_party_voucher_register_rows(filters, receipt=False)
