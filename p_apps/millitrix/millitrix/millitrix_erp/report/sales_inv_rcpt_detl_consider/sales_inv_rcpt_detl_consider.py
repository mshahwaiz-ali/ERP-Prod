# Copyright (c) 2026, Millitrix and contributors
# Oracle SalesInvRcptDetl_Consider.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_sales_inv_receipt_rows
from millitrix.utils.report_columns import sales_inv_receipt_detail_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters or {})
	filters["include_consider"] = 1
	return sales_inv_receipt_detail_columns(), get_sales_inv_receipt_rows(filters)
