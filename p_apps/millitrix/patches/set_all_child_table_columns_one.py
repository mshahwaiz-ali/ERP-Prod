# Set columns=1 on every child-table field shown in the grid (in_list_view).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.patches.apply_ui_field_options import LAYOUT_FIELDTYPES

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"


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
			if field.get("fieldtype") in LAYOUT_FIELDTYPES or field.get("hidden"):
				continue
			if not field.get("in_list_view"):
				continue
			if field.get("columns") != 1:
				field["columns"] = 1
				changed = True

		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			print("columns=1", data.get("name") or folder.name)


def _sync_db() -> None:
	for name in frappe.get_all(
		"DocType",
		filters={"istable": 1, "module": "Millitrix ERP"},
		pluck="name",
	):
		for row in frappe.get_all(
			"DocField",
			filters={"parent": name, "parenttype": "DocType", "in_list_view": 1},
			fields=["name", "fieldtype", "hidden", "columns"],
		):
			if row.fieldtype in LAYOUT_FIELDTYPES or row.hidden:
				continue
			if row.columns != 1:
				frappe.db.set_value("DocField", row.name, "columns", 1, update_modified=False)

	# frappe.db.commit()  # DISABLED SAFE MODE


def execute() -> None:
	_apply_json()
	_sync_db()
	frappe.clear_cache(doctype="DocType")
