# Copyright (c) 2026, Millitrix and contributors
# Oracle SalesInvReceipt.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_sales_inv_receipt_register_rows
from millitrix.utils.report_columns import sales_inv_receipt_register_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return sales_inv_receipt_register_columns(), get_sales_inv_receipt_register_rows(normalize_report_dates(filters))
