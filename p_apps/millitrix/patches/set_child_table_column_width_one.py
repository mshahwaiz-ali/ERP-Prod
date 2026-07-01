# Set columns=1 on all Millitrix child-table fields; normalize saved GridView widths.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json

import frappe

from millitrix.patches.apply_ui_field_options import LAYOUT_FIELDTYPES, apply as apply_json


def execute() -> None:
	apply_json()
	_sync_child_table_columns()
	_normalize_grid_view_user_settings()
	frappe.clear_cache(doctype="DocType")


def _sync_child_table_columns() -> None:
	for row in frappe.get_all(
		"DocField",
		filters={"parenttype": "DocType", "parentfield": "fields"},
		fields=["name", "parent", "fieldtype", "hidden", "columns", "in_list_view"],
	):
		meta = frappe.get_cached_value("DocType", row.parent, ["istable", "module"], as_dict=True)
		if not meta or not meta.istable or meta.module != "Millitrix ERP":
			continue
		if row.hidden or row.fieldtype in LAYOUT_FIELDTYPES:
			continue
		updates = {}
		if row.columns != 1:
			updates["columns"] = 1
		if not row.in_list_view:
			updates["in_list_view"] = 1
		if updates:
			frappe.db.set_value("DocField", row.name, updates, update_modified=False)
	# frappe.db.commit()  # DISABLED SAFE MODE


def _normalize_grid_view_user_settings() -> None:
	for row in frappe.db.sql(
		"SELECT `user`, doctype, data FROM `__UserSettings` WHERE data LIKE %s",
		("%GridView%",
	),
		as_dict=True,
	):
		if not row.data:
			continue
		try:
			data = json.loads(row.data)
		except json.JSONDecodeError:
			continue
		grid_view = data.get("GridView")
		if not isinstance(grid_view, dict):
			continue
		changed = False
		for _child_dt, cols in grid_view.items():
			if not isinstance(cols, list):
				continue
			for col in cols:
				if isinstance(col, dict) and col.get("columns") != 1:
					col["columns"] = 1
					changed = True
		if not changed:
			continue
		frappe.db.sql(
			"UPDATE `__UserSettings` SET data=%s WHERE `user`=%s AND doctype=%s",
			(json.dumps(data), row.user, row.doctype),
		)
		frappe.cache.hset("_user_settings", f"{row.doctype}::{row.user}", None)
	# frappe.db.commit()  # DISABLED SAFE MODE
