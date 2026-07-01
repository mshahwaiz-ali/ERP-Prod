# Copyright (c) 2026, Millitrix and contributors
# Oracle PartyBalance.RDF

from __future__ import annotations

from millitrix.utils.finance_reports import get_party_balance_report_rows
from millitrix.utils.report_columns import party_balance_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return party_balance_columns(), get_party_balance_report_rows(normalize_report_dates(filters))
