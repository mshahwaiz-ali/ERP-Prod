# Copyright (c) 2026, Millitrix and contributors
# Oracle Item_Stock.RDF

from __future__ import annotations

from millitrix.utils.report_columns import item_stock_columns
from millitrix.utils.stock_reports import get_item_stock_rows
from millitrix.utils.user_permissions import apply_user_store_filters, assert_report_access


def execute(filters=None):
	assert_report_access("Item_Stock")
	filters = apply_user_store_filters(filters)
	return item_stock_columns(), get_item_stock_rows(filters or {})
