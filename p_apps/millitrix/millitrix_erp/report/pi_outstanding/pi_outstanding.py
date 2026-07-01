# Copyright (c) 2026, Millitrix and contributors
# Oracle PIOutstanding.rep

from __future__ import annotations

from frappe.utils import getdate

from millitrix.utils.knockoff_docs import get_pi_outstanding_rows
from millitrix.utils.report_columns import invoice_outstanding_columns
from millitrix.utils.report_filters import normalize_report_filters


def execute(filters=None):
	filters = _normalize_outstanding_filters(filters)
	return invoice_outstanding_columns(party_label="Supplier"), get_pi_outstanding_rows(filters)


def _normalize_outstanding_filters(filters: dict | None) -> dict:
	filters = normalize_report_filters(filters)
	for field in ("as_of_date", "from_date", "to_date"):
		if filters.get(field):
			filters[field] = str(getdate(filters[field]))
	return filters
