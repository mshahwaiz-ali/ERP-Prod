# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.utils.mill_setting import SETTING_FIELDS


def execute():
	"""Millitrix Capture legacy row-based GL Parameter before Single DocType sync."""
	if not frappe.db.table_exists("Millitrix tabGL Parameter"):
		return

	columns = frappe.db.get_table_columns("GL Parameter") or []
	if "description" not in columns or "paracode" not in columns:
		return

	rows = frappe.db.sql(
		"""
		SELECT description, paracode, fromdate, todate
		FROM `tabGL Parameter`
		WHERE description IS NOT NULL AND description != ''
		""",
		as_dict=True,
	)
	if rows:
		frappe.flags.millitrix_settings_migration_rows = rows


def apply():
	"""Millitrix Apply captured GL Parameter rows onto the Single DocType."""
	rows = getattr(frappe.flags, "millitrix_settings_migration_rows", None)
	if not rows:
		return

	doc = frappe.db.get_single_value("GL Parameter", "location_id")
	changed = False

	for row in rows:
		description = row.description
		if description == "Financial Year":
			if row.fromdate and not doc.financial_year_from:
				doc.financial_year_from = row.fromdate
				changed = True
			if row.todate and not doc.financial_year_to:
				doc.financial_year_to = row.todate
				changed = True
			continue

		fieldname = SETTING_FIELDS.get(description)
		if not fieldname:
			continue
		if row.paracode and not doc.get(fieldname):
			doc.set(fieldname, row.paracode)
			changed = True

	if changed:
		doc.flags.ignore_permissions = True
		doc.save()
