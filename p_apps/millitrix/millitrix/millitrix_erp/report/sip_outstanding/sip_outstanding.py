# Copyright (c) 2026, Millitrix and contributors
# Oracle SIPOutstanding.RDF

from __future__ import annotations

from frappe.utils import getdate

from millitrix.utils.extended_reports import get_sip_outstanding_rows
from millitrix.utils.report_columns import sip_outstanding_columns
from millitrix.utils.report_filters import normalize_report_filters


def execute(filters=None):
	filters = _normalize_outstanding_filters(filters)
	return sip_outstanding_columns(), get_sip_outstanding_rows(filters)


def _normalize_outstanding_filters(filters: dict | None) -> dict:
	filters = normalize_report_filters(filters)
	for field in ("as_of_date", "from_date", "to_date"):
		if filters.get(field):
			filters[field] = str(getdate(filters[field]))
	return filters
