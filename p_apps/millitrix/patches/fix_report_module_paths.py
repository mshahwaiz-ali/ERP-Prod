# Copyright (c) 2026, Millitrix and contributors
"""Align Report.name with on-disk folder so Frappe can import report modules."""

from __future__ import annotations

import json
import re
import shutil

import frappe

from millitrix.utils.report_registry import (
	REPORT_ROOT,
	canonical_report_name,
	folder_to_report_name,
	load_report_catalog,
	scrub,
)


def _update_js_key(js_path, old_name: str, new_name: str) -> None:
	if not js_path.exists():
		return
	text = js_path.read_text(encoding="utf-8")
	updated = text.replace(f'frappe.query_reports["{old_name}"]', f'frappe.query_reports["{new_name}"]')
	if updated != text:
		js_path.write_text(updated, encoding="utf-8")


def execute() -> None:
	removed = 0
	for folder in list(REPORT_ROOT.iterdir()):
		if not folder.is_dir():
			continue
		if folder.name.startswith("millitrix_") and not (folder / f"{folder.name}.json").exists():
			shutil.rmtree(folder, ignore_errors=True)
			removed += 1
			print(f"removed orphan report folder: {folder.name}")

	renamed = 0
	for folder, meta in load_report_catalog().items():
		json_path = meta["json_path"]
		data = json.loads(json_path.read_text(encoding="utf-8"))
		old_name = data.get("name") or ""
		new_name = canonical_report_name(folder)
		if scrub(old_name) == folder and old_name == new_name:
			continue

		if old_name and old_name != new_name and frappe.db.exists("Report", old_name):
			if frappe.db.exists("Report", new_name):
				frappe.delete_doc("Report", old_name, force=1, ignore_permissions=True)
			else:
				frappe.rename_doc("Report", old_name, new_name, force=True)
			renamed += 1

		data["name"] = new_name
		data["report_name"] = new_name
		json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
		_update_js_key(meta["js_path"], old_name, new_name)
		if old_name and old_name != new_name:
			print(f"report: {old_name} -> {new_name}")

	# frappe.db.commit()  # DISABLED SAFE MODE
	frappe.clear_cache()
	print(f"fix_report_module_paths: renamed={renamed}, removed_orphans={removed}")
