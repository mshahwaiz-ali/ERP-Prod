# Copyright (c) 2026, Millitrix and contributors
"""Align Document controller class names with Frappe convention after client rename."""

from __future__ import annotations

import json
import re
from pathlib import Path

import frappe


def frappe_class_name(doctype: str) -> str:
	return doctype.replace(" ", "").replace("-", "")


def _fix_py_class(path: Path, expected: str) -> bool:
	text = path.read_text()
	match = re.search(r"^class\s+(.+?)\s*\(", text, re.MULTILINE)
	if not match:
		return False
	current = match.group(1).strip()
	if current == expected:
		return False
	text = text.replace(f"class {current}(", f"class {expected}(", 1)
	path.write_text(text)
	return True


def execute():
	doctype_root = Path(frappe.get_app_path("millitrix")) / "millitrix_erp" / "doctype"
	updated: list[str] = []
	skipped: list[str] = []

	for folder in sorted(doctype_root.iterdir()):
		if not folder.is_dir():
			continue
		json_files = list(folder.glob("*.json"))
		if not json_files:
			continue
		meta = json.loads(json_files[0].read_text())
		if meta.get("doctype") != "DocType":
			continue
		doctype_name = meta["name"]
		expected = frappe_class_name(doctype_name)
		py_file = folder / f"{folder.name}.py"
		if not py_file.exists():
			skipped.append(doctype_name)
			continue
		if _fix_py_class(py_file, expected):
			updated.append(f"{doctype_name}: {expected}")

	# Fix broken test class names (spaces from bad bulk replace)
	for test_py in doctype_root.glob("**/test_*.py"):
		text = test_py.read_text()
		fixed = re.sub(r"class\s+TestEmployee\s+Setup(\w+)", r"class TestEmployeeSetup\1", text)
		if fixed != text:
			test_py.write_text(fixed)
			updated.append(f"test fix: {test_py.name}")

	frappe.db.commit()
	print(f"Updated {len(updated)} controller classes")
	for line in updated:
		print(f"  {line}")
	if skipped:
		print(f"Skipped {len(skipped)} (no .py): {', '.join(skipped[:5])}...")
