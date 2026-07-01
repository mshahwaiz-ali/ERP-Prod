# Prefix all client DocType names with Millitrix (Millitrix Accounts Opening, etc.)
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

from millitrix.utils.client_doctype_map import (
	PREFIX_RENAME_MAP,
	replacements_longest_first,
	slug,
)

APP_ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = APP_ROOT / "millitrix_erp" / "doctype"

SKIP_REPLACE_IN = {
	"client_doctype_map.py",
	"prefix_millitrix_doctypes.py",
	"rename_doctypes_to_client_names.py",
}


def execute() -> None:
	import frappe

	from millitrix.patches.fix_doctype_controller_classes import execute as fix_controllers

	_rename_in_database()
	_update_source_files()
	_rename_doctype_folders()
	fix_controllers()
	frappe.clear_cache()
	frappe.db.commit()


def _rename_in_database() -> None:
	import frappe

	for old, new in replacements_longest_first(PREFIX_RENAME_MAP):
		if old == new:
			continue
		if frappe.db.exists("DocType", new):
			continue
		if not frappe.db.exists("DocType", old):
			continue
		try:
			frappe.rename_doc("DocType", old, new, force=True)
			print(f"renamed DocType: {old} -> {new}")
		except Exception as exc:
			print(f"FAILED {old} -> {new}: {exc}")


def _update_source_files() -> None:
	"""Replace only whole DocType name strings (longest first) — never partial substrings."""
	replacements = replacements_longest_first(PREFIX_RENAME_MAP)
	for path in APP_ROOT.rglob("*"):
		if not path.is_file():
			continue
		if path.suffix not in {".py", ".js", ".json", ".md", ".html", ".css", ".txt"}:
			continue
		if path.name in SKIP_REPLACE_IN:
			continue
		if "doctype" in path.parts and path.suffix == ".json" and path.parent.parent.name == "doctype":
			continue  # JSON names fixed via folder rebuild / migrate
		try:
			text = path.read_text(encoding="utf-8")
		except (UnicodeDecodeError, OSError):
			continue
		original = text
		for old, new in replacements:
			text = text.replace(old, new)
		if text != original:
			path.write_text(text, encoding="utf-8")
			print(f"updated {path.relative_to(APP_ROOT)}")


def _rename_doctype_folders() -> None:
	for folder in sorted(DOCTYPE_ROOT.iterdir()):
		if not folder.is_dir():
			continue
		json_files = list(folder.glob("*.json"))
		if not json_files:
			continue
		data = json.loads(json_files[0].read_text(encoding="utf-8"))
		new_name = data.get("name")
		if not new_name:
			continue
		new_slug = slug(new_name)
		new_folder = DOCTYPE_ROOT / new_slug
		if folder == new_folder:
			_rename_internal_files(folder, new_slug)
			continue
		if new_folder.exists():
			_rename_internal_files(folder, new_slug)
			_merge_into(folder, new_folder)
		else:
			folder.rename(new_folder)
			print(f"renamed folder {folder.name} -> {new_slug}")
			_rename_internal_files(new_folder, new_slug)


def _merge_into(src: Path, dest: Path) -> None:
	for item in src.iterdir():
		target = dest / item.name
		if item.is_dir():
			if target.exists():
				_merge_into(item, target)
			else:
				item.rename(target)
		elif not target.exists():
			item.rename(target)
	src.rmdir()
	print(f"merged {src.name} -> {dest.name}")


def _rename_internal_files(folder: Path, slug_name: str) -> None:
	for path in list(folder.iterdir()):
		stem = path.stem
		if stem == slug_name:
			continue
		if path.suffix in {".py", ".js", ".json"} and not stem.startswith("test_"):
			new_name = f"{slug_name}{path.suffix}"
		elif stem.startswith("test_") and stem != f"test_{slug_name}":
			new_name = f"test_{slug_name}{path.suffix}"
		else:
			continue
		new_path = folder / new_name
		if path != new_path and not new_path.exists():
			path.rename(new_path)
			print(f"  renamed file {path.name} -> {new_name}")
