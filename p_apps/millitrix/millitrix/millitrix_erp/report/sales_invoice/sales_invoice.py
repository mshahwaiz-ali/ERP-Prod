# Copyright (c) 2026, Millitrix and contributors
# Oracle SalesInvoice.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_sales_invoice_detail_rows
from millitrix.utils.report_columns import sales_invoice_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return sales_invoice_columns(), get_sales_invoice_detail_rows(filters)
