# Sync client field labels to JSON files and database.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.utils.client_field_labels import label_for_field

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"


def execute() -> None:
	updated_doctypes: list[str] = []
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		doctype = data.get("name")
		if not doctype:
			continue
		changed = False
		for field in data.get("fields", []):
			fname = field.get("fieldname")
			new_label = label_for_field(doctype, fname, field.get("label"))
			if new_label and field.get("label") != new_label:
				field["label"] = new_label
				changed = True
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			updated_doctypes.append(doctype)

	for doctype in updated_doctypes:
		frappe.reload_doc("millitrix_erp", "doctype", frappe.scrub(doctype))

	frappe.clear_cache(doctype="DocType")
	print(f"synced labels for {len(updated_doctypes)} doctypes")
