# Copyright (c) 2026, Millitrix and contributors
# One-time migration: Oracle single-letter LOV values → full-word labels in DB.

from __future__ import annotations

import frappe

_POSTED_MAP = {"Y": "Submitted", "N": "Draft"}
_NATURE_MAP = {
	"A": "Assets",
	"L": "Liabilities",
	"C": "Capital",
	"R": "Revenue",
	"E": "Expenses",
}
_TRANSFLAG_MAP = {"Y": "Yes", "N": "No"}
_STATUS_MAP = {"IN": "Initial", "IP": "In Progress", "CO": "Complete", "CA": "Cancelled"}
_BAGS_MAP = {"OUR": "Our", "PARTY": "Party", "PA": "Party", "PU": "Purchase Bardana", "SA": "Sales Bardana"}


def _swap(table: str, field: str, mapping: dict[str, str]) -> None:
	for old, new in mapping.items():
		if old == new:
			continue
		frappe.db.sql(
			f"UPDATE `tab{table}` SET `{field}` = %(new)s WHERE `{field}` = %(old)s",
			{"old": old, "new": new},
		)


_YES_NO_MAP = {"Y": "Yes", "N": "No"}
_ACTIVE_MAP = {"Y": "Active", "N": "Inactive"}
_CHECK_MAP = {"Y": "1", "N": "0", "Yes": "1", "No": "0"}


def execute():
	"""Migrate legacy single-letter values after UI option update."""
	for doctype in frappe.get_all("DocType", filters={"module": "Millitrix ERP"}, pluck="name"):
		table = f"tab{doctype}"
		if not frappe.db.table_exists(table):
			continue
		if frappe.db.has_column(table, "posted"):
			_swap(doctype, "posted", _POSTED_MAP)

	if frappe.db.table_exists("Millitrix tabChart of Accounting"):
		_swap("Chart of Accounting", "nature", _NATURE_MAP)
		_swap("Chart of Accounting", "transflag", _TRANSFLAG_MAP)

	for doctype in ("Purchase Order", "Sales Order"):
		if frappe.db.table_exists(f"tab{doctype}"):
			_swap(doctype, "status", _STATUS_MAP)

	for doctype, field in (
		("Purchase Invoice Detail", "bags_are"),
		("Sales Invoice Detail", "bags_are"),
		("Gate Pass Detail", "bags_are"),
		("Stock Transfer Detail", "bags_are"),
		("Opening Stock Detail", "bags_are"),
		("Stock Adjustment Detail", "bags_are"),
		("Stock In Hand", "bags_are"),
		("Purchase Return Detail", "bags_are"),
		("Sales Return Detail", "bags_are"),
	):
		table = f"tab{doctype}"
		if frappe.db.table_exists(table) and frappe.db.has_column(table, field):
			_swap(doctype, field, _BAGS_MAP)

	for doctype, field in (
		("User Rights", "activestatus"),
		("Employee Category", "payslip"),
		("Store Setup", "stockable"),
		("User Store", "resaccess"),
		("User Store", "default_store"),
		("GL Statements", "active"),
	):
		table = f"tab{doctype}"
		if frappe.db.table_exists(table) and frappe.db.has_column(table, field):
			if field == "activestatus":
				_swap(doctype, field, _ACTIVE_MAP)
			else:
				_swap(doctype, field, _YES_NO_MAP)

	for field in (
		"canview",
		"canadd",
		"canedit",
		"candelete",
		"cansubmit",
		"canassign",
		"canunsubmit",
		"resaccess",
	):
		table = "Millitrix tabModule Permission"
		if frappe.db.table_exists(table) and frappe.db.has_column(table, field):
			_swap("Module Permission", field, _CHECK_MAP)

	frappe.db.commit()
