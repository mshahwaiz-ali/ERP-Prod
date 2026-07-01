# Copyright (c) 2026, Millitrix and contributors
# Oracle ItemBinCard.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_item_bincard_rows
from millitrix.utils.report_columns import item_bincard_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return item_bincard_columns(), get_item_bincard_rows(normalize_report_dates(filters))
