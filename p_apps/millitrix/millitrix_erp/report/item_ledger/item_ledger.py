# Copyright (c) 2026, Millitrix and contributors
# Oracle ItemLedger.RDF

from __future__ import annotations

from millitrix.utils.report_columns import item_ledger_columns
from millitrix.utils.report_filters import normalize_report_dates
from millitrix.utils.stock_reports import get_item_ledger_report_rows


def execute(filters=None):
	return item_ledger_columns(), get_item_ledger_report_rows(normalize_report_dates(filters))
