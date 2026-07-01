# Show every data field in Millitrix child-table grids (in_list_view + columns=1).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.patches.apply_ui_field_options import LAYOUT_FIELDTYPES

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"


def _is_grid_field(field: dict) -> bool:
	return (
		field.get("fieldname")
		and field.get("fieldtype") not in LAYOUT_FIELDTYPES
		and not field.get("hidden")
	)


def _apply_json() -> None:
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue

		data = json.loads(json_path.read_text(encoding="utf-8"))
		if not data.get("istable"):
			continue

		changed = False
		for field in data.get("fields", []):
			if not _is_grid_field(field):
				continue
			if not field.get("in_list_view"):
				field["in_list_view"] = 1
				changed = True
			if field.get("columns") != 1:
				field["columns"] = 1
				changed = True

		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			print("grid fields", data.get("name") or folder.name)


def _sync_db() -> None:
	for name in frappe.get_all(
		"DocType",
		filters={"istable": 1, "module": "Millitrix ERP"},
		pluck="name",
	):
		for row in frappe.get_all(
			"DocField",
			filters={"parent": name, "parenttype": "DocType"},
			fields=["name", "fieldname", "fieldtype", "hidden", "in_list_view", "columns"],
		):
			if not _is_grid_field(row):
				continue
			updates = {}
			if not row.in_list_view:
				updates["in_list_view"] = 1
			if row.columns != 1:
				updates["columns"] = 1
			if updates:
				frappe.db.set_value("DocField", row.name, updates, update_modified=False)

	# frappe.db.commit()  # DISABLED SAFE MODE


def execute() -> None:
	_apply_json()
	_sync_db()
	frappe.clear_cache(doctype="DocType")
