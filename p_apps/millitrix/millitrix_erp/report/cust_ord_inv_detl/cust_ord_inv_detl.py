# Copyright (c) 2026, Millitrix and contributors
# Oracle CustOrdInvDetl.RDF

from __future__ import annotations

from millitrix.utils.final_reports import get_cust_ord_inv_detl_rows
from millitrix.utils.report_columns import so_inv_detail_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return so_inv_detail_columns(), get_cust_ord_inv_detl_rows(normalize_report_dates(filters))
