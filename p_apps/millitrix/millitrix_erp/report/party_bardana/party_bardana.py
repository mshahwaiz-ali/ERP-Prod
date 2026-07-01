# Copyright (c) 2026, Millitrix and contributors
# Oracle PartyBardana.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_party_bardana_rows
from millitrix.utils.report_columns import party_bardana_columns


def execute(filters=None):
	return party_bardana_columns(), get_party_bardana_rows(filters)
