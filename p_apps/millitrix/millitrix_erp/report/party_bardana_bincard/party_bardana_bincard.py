# Copyright (c) 2026, Millitrix and contributors
# Oracle PartyBardanaBincard.RDF

from __future__ import annotations

from millitrix.utils.final_reports import get_party_bardana_bincard_rows
from millitrix.utils.report_columns import party_bardana_bincard_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return party_bardana_bincard_columns(), get_party_bardana_bincard_rows(normalize_report_dates(filters))
