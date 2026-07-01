# Copyright (c) 2026, Millitrix and contributors
"""Show names (not numeric ids) in Link fields across masters and forms."""

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.utils.document_display import MASTER_TITLE, install_title_patch
from millitrix.utils.link_title_fields import apply_all

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"


def execute() -> None:
	install_title_patch()
	updated = apply_all(BASE)

	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		jp = folder / f"{folder.name}.json"
		if not jp.exists():
			continue
		data = json.loads(jp.read_text(encoding="utf-8"))
		doctype = data.get("name") or ""
		if doctype not in MASTER_TITLE:
			continue
		title = MASTER_TITLE[doctype]
		changed = False
		if data.get("title_field") != title:
			data["title_field"] = title
			changed = True
		if not data.get("show_title_field_in_link"):
			data["show_title_field_in_link"] = 1
			changed = True
		if changed:
			jp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
			if doctype not in updated:
				updated.append(folder.name)

	reloaded: list[str] = []
	for folder in sorted(set(updated)):
		try:
			frappe.reload_doc("millitrix_erp", "doctype", folder.replace("-", "_"))
			reloaded.append(folder)
		except Exception:
			pass

	frappe.clear_cache(doctype="DocType")
	print(f"fix_master_link_titles: updated {len(updated)}, reloaded {len(reloaded)}")
