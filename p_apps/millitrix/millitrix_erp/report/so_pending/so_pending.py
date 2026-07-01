# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from frappe import _

from millitrix.utils.report_columns import so_pending_columns
from millitrix.utils.trading_reports import get_sales_order_pending_rows


def execute(filters=None):
	return so_pending_columns(), get_sales_order_pending_rows(filters or {})
