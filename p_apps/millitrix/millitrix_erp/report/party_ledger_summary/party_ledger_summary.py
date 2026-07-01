# Copyright (c) 2026, Millitrix and contributors
# Oracle PartyLedgerSummary.RDF

from __future__ import annotations

from millitrix.utils.finance_reports import get_party_ledger_summary_rows
from millitrix.utils.report_columns import party_ledger_summary_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return party_ledger_summary_columns(), get_party_ledger_summary_rows(normalize_report_dates(filters))
