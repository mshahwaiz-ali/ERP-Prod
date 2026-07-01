# Copyright (c) 2026, Millitrix and contributors
# Cap Float/Percent precision at 2 for Millitrix forms (no .000 display).

from __future__ import annotations

import json
from pathlib import Path

import frappe

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"
DISPLAY_PRECISION = "2"
NUMERIC_FIELDTYPES = frozenset({"Float", "Percent"})


def apply() -> list[str]:
	changed_doctypes: list[str] = []
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		changed = False
		for field in data.get("fields", []):
			if field.get("fieldtype") not in NUMERIC_FIELDTYPES:
				continue
			if field.get("precision") != DISPLAY_PRECISION:
				field["precision"] = DISPLAY_PRECISION
				changed = True
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			changed_doctypes.append(data.get("name") or folder.name)
	return changed_doctypes


def execute() -> None:
	updated = apply()
	for name in updated:
		try:
			slug = name.lower().replace(" ", "_")
			frappe.reload_doc("millitrix_erp", "doctype", slug)
		except Exception:
			pass
	if updated:
		frappe.clear_cache(doctype="DocType")
	print(f"number display precision applied ({len(updated)} doctypes)")
