# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from millitrix.utils.extended_reports import get_po_inv_detail_rows
from millitrix.utils.report_columns import po_inv_detail_columns
from millitrix.utils.report_filters import normalize_report_dates
from frappe import _

def execute(filters=None):
	return po_inv_detail_columns(), get_po_inv_detail_rows(normalize_report_dates(filters))
