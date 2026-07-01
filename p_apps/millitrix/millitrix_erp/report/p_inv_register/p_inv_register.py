# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from frappe import _

from millitrix.utils.report_columns import purchase_invoice_register_columns
from millitrix.utils.report_filters import normalize_report_dates
from millitrix.utils.trading_reports import get_purchase_invoice_register_rows


def execute(filters=None):
	filters = normalize_report_dates(filters)
	return purchase_invoice_register_columns(), get_purchase_invoice_register_rows(filters)
