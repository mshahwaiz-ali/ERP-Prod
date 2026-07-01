# Copyright (c) 2026, Millitrix and contributors
# Blueprint 8.8 — Closing_Transaction.fmb wizard API

from __future__ import annotations

import frappe
from frappe import _

from millitrix.finance.year_end_closing import execute_year_end_closing, preview_year_end_closing


def _check_closing_permission() -> None:
	if frappe.session.user == "Administrator":
		return
	if not frappe.has_role("Millitrix ERP Manager"):
		frappe.throw(
			_("Only ERP Manager can run year-end closing"),
			frappe.PermissionError,
		)


@frappe.whitelist()
def preview(
	location_id: str,
	closing_date: str,
	opening_date: str | None = None,
	fy_from_date: str | None = None,
	capital_acc: str | None = None,
):
	"""Preview trial balance, P&L close lines, and stock/GL roll-forward."""
	_check_closing_permission()
	if not location_id:
		frappe.throw(_("Location is required"))
	if not closing_date:
		frappe.throw(_("Closing Date is required"))
	return preview_year_end_closing(
		location_id,
		closing_date,
		opening_date=opening_date or None,
		fy_from_date=fy_from_date or None,
		capital_acc=capital_acc or None,
	)


@frappe.whitelist()
def execute(
	location_id: str,
	closing_date: str,
	opening_date: str | None = None,
	fy_from_date: str | None = None,
	capital_acc: str | None = None,
):
	"""Create and submit P&L closing, stock closing/opening, and GL opening documents."""
	_check_closing_permission()
	if not location_id:
		frappe.throw(_("Location is required"))
	if not closing_date:
		frappe.throw(_("Closing Date is required"))

	result = execute_year_end_closing(
		location_id,
		closing_date,
		opening_date=opening_date or None,
		fy_from_date=fy_from_date or None,
		capital_acc=capital_acc or None,
	)
	return result
