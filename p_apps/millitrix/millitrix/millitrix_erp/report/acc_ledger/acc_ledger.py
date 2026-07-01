# Copyright (c) 2026, Millitrix and contributors
# Blueprint Section 20 — Account Ledger report (Oracle AccLedger.RDF)

from __future__ import annotations

from frappe import _

from millitrix.utils.gl_reports import get_account_ledger_with_balance_rows
from millitrix.utils.report_columns import ledger_line_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	columns = ledger_line_columns(include_balance=True, include_doc_type=True)
	data = get_account_ledger_with_balance_rows(filters)
	return columns, data
