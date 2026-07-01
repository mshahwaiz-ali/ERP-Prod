# Apply blueprint.md field rules to all DocType JSON files.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.patches.apply_ui_field_options import apply as apply_select_options
from millitrix.utils.blueprint_form_rules import (
	HIDDEN_FIELDS,
	REMOVED_FIELDS,
	hidden_for,
	link_options_for,
	location_ui_hidden,
	mandatory_for,
	read_only_for,
	removed_for,
	should_not_be_mandatory_ui,
)
from millitrix.utils.client_field_labels import label_for_field

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

LAYOUT_EXCLUDED = frozenset(HIDDEN_FIELDS.get("*", []))


def _remove_orphan_fields(data: dict) -> bool:
	doctype = data.get("name") or ""
	remove = {
		fname
		for fname in REMOVED_FIELDS.get("*", []) + REMOVED_FIELDS.get(doctype, [])
		if removed_for(doctype, fname)
	}
	if not remove:
		return False
	changed = False
	fields = data.get("fields", [])
	new_fields = [field for field in fields if field.get("fieldname") not in remove]
	if len(new_fields) != len(fields):
		data["fields"] = new_fields
		changed = True
	field_order = data.get("field_order", [])
	new_order = [fname for fname in field_order if fname not in remove]
	if new_order != field_order:
		data["field_order"] = new_order
		changed = True
	return changed


def _strip_hidden_from_layout(data: dict) -> bool:
	doctype = data.get("name") or ""
	exclude = {fname for fname in LAYOUT_EXCLUDED if hidden_for(doctype, fname)}
	exclude.update(
		fname for fname in HIDDEN_FIELDS.get(doctype, []) if hidden_for(doctype, fname)
	)
	if location_ui_hidden(doctype):
		exclude.add("location_id")
	if not exclude:
		return False
	field_order = data.get("field_order", [])
	new_order = [fname for fname in field_order if fname not in exclude]
	if new_order == field_order:
		return False
	data["field_order"] = new_order
	return True


def _apply_field_rules(data: dict) -> bool:
	doctype = data.get("name") or ""
	autoname = data.get("autoname") or ""
	autoname_id = autoname.split(":", 1)[1] if autoname.startswith("field:") else None
	changed = False
	for field in data.get("fields", []):
		fname = field.get("fieldname")
		if not fname or field.get("fieldtype") in ("Section Break", "Column Break", "Tab Break", "Table"):
			continue

		label = label_for_field(doctype, fname, field.get("label"))
		if label and field.get("label") != label:
			field["label"] = label
			changed = True

		if hidden_for(doctype, fname):
			if not field.get("hidden"):
				field["hidden"] = 1
				changed = True
			if not field.get("print_hide"):
				field["print_hide"] = 1
				changed = True
			if not field.get("report_hide"):
				field["report_hide"] = 1
				changed = True

		if read_only_for(doctype, fname):
			if not field.get("read_only"):
				field["read_only"] = 1
				changed = True

		if should_not_be_mandatory_ui(doctype, fname, field, autoname_id=autoname_id):
			if field.get("reqd"):
				field["reqd"] = 0
				changed = True
		else:
			req = mandatory_for(doctype, fname)
			if req is True and not field.get("reqd"):
				field["reqd"] = 1
				changed = True

		if field.get("fieldtype") == "Link":
			opts = link_options_for(doctype, fname)
			if opts and field.get("options") != opts:
				field["options"] = opts
				changed = True

	return changed


def execute() -> None:
	updated: list[str] = []
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		changed = _remove_orphan_fields(data)
		if _apply_field_rules(data):
			changed = True
		if _strip_hidden_from_layout(data):
			changed = True
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			updated.append(data.get("name") or folder.name)

	apply_select_options()

	from millitrix.patches.blueprint_field_fixes import _patch_json_files

	_patch_json_files()

	for doctype in updated:
		try:
			frappe.reload_doc("millitrix_erp", "doctype", frappe.scrub(doctype))
		except Exception:
			pass

	frappe.clear_cache(doctype="DocType")
	print(f"blueprint form rules applied to {len(updated)} doctypes")
