# Copyright (c) 2026, Millitrix and contributors
# Oracle BankBook.RDF

from __future__ import annotations

from millitrix.utils.finance_reports import get_bank_book_rows
from millitrix.utils.report_columns import ledger_line_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	columns = ledger_line_columns(include_balance=True, include_doc_type=True)
	return columns, get_bank_book_rows(filters)
