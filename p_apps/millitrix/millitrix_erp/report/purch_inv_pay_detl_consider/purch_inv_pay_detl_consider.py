# Copyright (c) 2026, Millitrix and contributors
# Oracle PurchInvPayDetl_Consider.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_purch_inv_payment_rows
from millitrix.utils.report_columns import purch_inv_payment_detail_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters or {})
	filters["include_consider"] = 1
	return purch_inv_payment_detail_columns(), get_purch_inv_payment_rows(filters)
