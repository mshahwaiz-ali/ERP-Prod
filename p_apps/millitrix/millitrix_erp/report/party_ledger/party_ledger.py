# Copyright (c) 2026, Millitrix and contributors
# Blueprint Section 20 — Party Ledger report (Oracle PartyLedger.RDF)

from __future__ import annotations

from frappe import _

from millitrix.utils.gl_reports import get_party_ledger_rows
from millitrix.utils.report_columns import ledger_line_columns, normalize_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	filters = normalize_report_dates(filters)
	columns = ledger_line_columns(include_balance=True, include_doc_type=True)
	for idx, col in enumerate(columns):
		if col.get("fieldname") == "partyid":
			columns.insert(
				idx + 1,
				{"label": _("Party Name"), "fieldname": "party_name", "fieldtype": "Data", "width": 180},
			)
			break
	return normalize_columns(columns), get_party_ledger_rows(filters)
