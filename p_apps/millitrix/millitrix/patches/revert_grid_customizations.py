# Revert child-table grid UI customizations (in_list_view on all fields, columns=1, in_place_edit).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.patches.apply_ui_field_options import IN_LIST_VIEW, LAYOUT_FIELDTYPES

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"


def _revert_json_files() -> None:
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue

		data = json.loads(json_path.read_text(encoding="utf-8"))
		doctype = data.get("name") or folder.name.replace("_", " ").title()
		grid_cols = set(IN_LIST_VIEW.get(doctype, []))
		changed = False

		for field in data.get("fields", []):
			fname = field.get("fieldname")

			if field.get("fieldtype") == "Table" and field.get("in_place_edit"):
				field.pop("in_place_edit", None)
				changed = True

			if not data.get("istable"):
				continue

			if "columns" in field:
				field.pop("columns", None)
				changed = True

			if field.get("fieldtype") in LAYOUT_FIELDTYPES or field.get("hidden"):
				continue

			if fname in grid_cols:
				if not field.get("in_list_view"):
					field["in_list_view"] = 1
					changed = True
			elif field.get("in_list_view"):
				field["in_list_view"] = 0
				changed = True

		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			print("reverted", doctype)


def _sync_docfields() -> None:
	for name in frappe.get_all(
		"DocType",
		filters={"istable": 1, "module": "Millitrix ERP"},
		pluck="name",
	):
		grid_cols = set(IN_LIST_VIEW.get(name, []))
		for row in frappe.get_all(
			"DocField",
			filters={"parent": name, "parenttype": "DocType"},
			fields=["name", "fieldname", "fieldtype", "hidden", "in_list_view", "columns"],
		):
			if row.fieldtype in LAYOUT_FIELDTYPES or row.hidden:
				continue
			updates = {}
			if row.columns:
				updates["columns"] = 0
			want_list = 1 if row.fieldname in grid_cols else 0
			if row.in_list_view != want_list:
				updates["in_list_view"] = want_list
			if updates:
				frappe.db.set_value("DocField", row.name, updates, update_modified=False)

	frappe.db.commit()


def execute() -> None:
	_revert_json_files()
	_sync_docfields()
	frappe.clear_cache(doctype="DocType")
