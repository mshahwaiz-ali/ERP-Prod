# Copyright (c) 2026, Millitrix and contributors
"""Clear mandatory flag on read-only / auto-populated DocType fields."""

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.utils.blueprint_form_rules import read_only_for, should_not_be_mandatory_ui

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"


def _fix_doctype_json(data: dict) -> bool:
	autoname = data.get("autoname") or ""
	autoname_id = autoname.split(":", 1)[1] if autoname.startswith("field:") else None
	doctype = data.get("name") or ""
	changed = False
	for field in data.get("fields", []):
		fname = field.get("fieldname")
		if not fname:
			continue
		if read_only_for(doctype, fname) and not field.get("read_only"):
			field["read_only"] = 1
			changed = True
		if should_not_be_mandatory_ui(doctype, fname, field, autoname_id=autoname_id):
			if field.get("reqd"):
				field["reqd"] = 0
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
		if _fix_doctype_json(data):
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			updated.append(data.get("name") or folder.name)

	for doctype in updated:
		try:
			frappe.reload_doc("millitrix_erp", "doctype", frappe.scrub(doctype))
		except Exception:
			pass

	frappe.clear_cache(doctype="DocType")
	print(f"readonly/mandatory conflict fixed on {len(updated)} doctypes")
