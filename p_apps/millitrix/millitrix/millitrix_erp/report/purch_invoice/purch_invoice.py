# Copyright (c) 2026, Millitrix and contributors
# Oracle PurchInvoice.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_purch_invoice_detail_rows
from millitrix.utils.report_columns import purch_invoice_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return purch_invoice_columns(), get_purch_invoice_detail_rows(filters)
