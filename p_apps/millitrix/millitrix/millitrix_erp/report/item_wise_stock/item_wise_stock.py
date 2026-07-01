# Copyright (c) 2026, Millitrix and contributors
# Oracle ItemWiseStock.RDF

from __future__ import annotations

from millitrix.utils.report_columns import item_wise_stock_columns
from millitrix.utils.stock_reports import get_item_wise_stock_rows
from millitrix.utils.user_permissions import apply_user_store_filters


def execute(filters=None):
	filters = apply_user_store_filters(filters)
	return item_wise_stock_columns(), get_item_wise_stock_rows(filters or {})
