# Ensure List View Settings show enough columns for Millitrix parent forms.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json

import frappe

from millitrix.utils.list_view_plan import PARENT_LIST_COLUMNS


def execute() -> None:
	for doctype in PARENT_LIST_COLUMNS:
		if not frappe.db.exists("DocType", doctype):
			continue
		_ensure_list_view_settings(doctype)
	_clear_low_column_user_settings(PARENT_LIST_COLUMNS.keys())
	frappe.clear_cache(doctype="DocType")


def _ensure_list_view_settings(doctype: str) -> None:
	try:
		doc = frappe.get_doc("List View Settings", doctype)
	except frappe.DoesNotExistError:
		doc = frappe.new_doc("List View Settings")
		doc.name = doctype
		doc.doctype = "List View Settings"

	current = int(doc.total_fields or 0)
	if current >= 10:
		return

	doc.total_fields = "10"
	doc.save(ignore_permissions=True)
	print("list view settings", doctype, "total_fields=10")


def _clear_low_column_user_settings(doctypes) -> None:
	rows = frappe.db.sql(
		"""
		SELECT `user`, doctype, data
		FROM `__UserSettings`
		WHERE doctype IN %(doctypes)s
		""",
		{"doctypes": list(doctypes)},
		as_dict=True,
	)
	cleared = 0
	for row in rows:
		data = json.loads(row.data or "{}")
		changed = False
		for key in ("List", "ListView"):
			if key not in data:
				continue
			entry = data[key]
			if isinstance(entry, dict) and int(entry.get("total_fields") or 10) < 6:
				del data[key]
				changed = True
		if changed:
			frappe.db.sql(
				"""
				UPDATE `__UserSettings`
				SET data = %s
				WHERE `user` = %s AND doctype = %s
				""",
				(json.dumps(data), row.user, row.doctype),
			)
			frappe.cache.hdel("_user_settings", f"{row.doctype}::{row.user}")
			cleared += 1
	if cleared:
		print("cleared low-column list user settings", cleared)
	frappe.db.commit()
