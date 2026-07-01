# Copyright (c) 2026, Millitrix and contributors
# Oracle SuppPayAndInv.RDF

from __future__ import annotations

from millitrix.utils.final_reports import get_supp_pay_and_inv_rows
from millitrix.utils.report_columns import supp_pay_and_inv_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return supp_pay_and_inv_columns(), get_supp_pay_and_inv_rows(normalize_report_dates(filters))
