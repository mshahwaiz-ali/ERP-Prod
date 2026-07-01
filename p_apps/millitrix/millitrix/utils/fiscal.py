# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate

from millitrix.utils.mill_setting import get_fiscal_year


def is_fiscal_period_enforced() -> bool:
	return bool(
		frappe.db.get_single_value("GL Parameter", "enforce_fiscal_period_validation")
	)


def validate_fiscal_period(doc_date) -> None:
	if not is_fiscal_period_enforced():
		return

	doc_date = getdate(doc_date)
	from_date, to_date = get_fiscal_year()
	from_date = getdate(from_date)
	to_date = getdate(to_date)
	if doc_date < from_date or doc_date > to_date:
		frappe.throw(
			_("Date {0} is outside open fiscal period {1} to {2}").format(doc_date, from_date, to_date)
		)


def check_posted(doc) -> None:
	"""Guard against draft docs with legacy posted=Submitted (use Frappe docstatus for lifecycle)."""
	from millitrix.utils.field_normalizers import is_yes

	if doc.docstatus == 0 and is_yes(getattr(doc, "posted", None)):
		frappe.throw(_("Document is already marked posted"))
