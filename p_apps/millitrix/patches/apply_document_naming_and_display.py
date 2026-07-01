# Copyright (c) 2026, Millitrix and contributors
"""Auto-readonly document IDs + clean link/hover titles (no narration Oracle ids)."""

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.utils.document_display import MASTER_TITLE, id_field_for
from millitrix.utils.naming import DOCTYPE_PREFIX

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"


def _apply_json(data: dict) -> bool:
	if data.get("istable"):
		return False

	doctype = data.get("name") or ""
	autoname = data.get("autoname") or ""
	if not autoname.startswith("field:"):
		return False

	id_field = autoname.split(":", 1)[1]
	is_transaction = doctype in DOCTYPE_PREFIX or doctype in (
		"Advance Payment",
		"Advance Receipt",
	)
	is_master = doctype in MASTER_TITLE
	changed = False

	for field in data.get("fields", []):
		if field.get("fieldname") != id_field:
			continue
		if is_transaction or is_master:
			if field.get("reqd"):
				field["reqd"] = 0
				changed = True
			if not field.get("read_only"):
				field["read_only"] = 1
				changed = True
		break

	if is_transaction:
		if data.get("title_field") in ("remarks", "narration", None) or data.get("title_field") != id_field:
			if data.get("title_field") != id_field:
				data["title_field"] = id_field
				changed = True
		if data.get("show_title_field_in_link"):
			data["show_title_field_in_link"] = 0
			changed = True
		search = data.get("search_fields") or ""
		if search and "narration" in search.split(","):
			parts = [p.strip() for p in search.split(",") if p.strip() and p.strip() != "narration"]
			if id_field not in parts:
				parts.insert(0, id_field)
			new_search = ",".join(parts)
			if new_search != search:
				data["search_fields"] = new_search
				changed = True

	if is_master:
		title = MASTER_TITLE[doctype]
		if data.get("title_field") != title:
			data["title_field"] = title
			changed = True
		if not data.get("show_title_field_in_link"):
			data["show_title_field_in_link"] = 1
			changed = True

	return changed


def execute() -> None:
	from millitrix.utils.document_display import install_title_patch

	install_title_patch()
	updated: list[str] = []
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		jp = folder / f"{folder.name}.json"
		if not jp.exists():
			continue
		data = json.loads(jp.read_text(encoding="utf-8"))
		if _apply_json(data):
			jp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			updated.append(data.get("name") or folder.name)

	for doctype in updated:
		try:
			frappe.reload_doc("millitrix_erp", "doctype", frappe.scrub(doctype))
		except Exception:
			pass

	frappe.clear_cache(doctype="DocType")
	print(f"document naming/display applied to {len(updated)} doctypes")
