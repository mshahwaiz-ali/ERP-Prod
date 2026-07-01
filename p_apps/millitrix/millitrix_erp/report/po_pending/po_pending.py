# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from frappe import _

from millitrix.utils.report_columns import po_pending_columns
from millitrix.utils.trading_reports import get_purchase_order_pending_rows


def execute(filters=None):
	columns = po_pending_columns()
	data = get_purchase_order_pending_rows(filters or {})
	return columns, data
