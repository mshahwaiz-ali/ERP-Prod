# Copyright (c) 2026, Millitrix and contributors
# Oracle Party_Bal_Paid.RDF

from __future__ import annotations

from millitrix.utils.final_reports import get_party_bal_paid_rows
from millitrix.utils.report_columns import party_bal_paid_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return party_bal_paid_columns(), get_party_bal_paid_rows(normalize_report_dates(filters))
