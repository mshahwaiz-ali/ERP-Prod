# Copyright (c) 2026, Millitrix and contributors
# Oracle SuppInvAndPay.RDF — customer SI detail + receipt knockoff

from __future__ import annotations

from millitrix.utils.final_reports import get_supp_inv_and_pay_rows
from millitrix.utils.report_columns import supp_inv_and_pay_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return supp_inv_and_pay_columns(), get_supp_inv_and_pay_rows(normalize_report_dates(filters))
