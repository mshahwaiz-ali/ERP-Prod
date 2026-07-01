# Repair DocType folders/files after prefix rename (fix double Millitrix, wrong slugs).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import frappe

from millitrix.utils.client_doctype_map import CLIENT_DOCTYPES, normalize_doctype_name, slug

APP_ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = APP_ROOT / "millitrix_erp" / "doctype"


def execute() -> None:
	_fix_double_prefix_in_sources()
	_rename_corrupted_in_database()
	_rebuild_doctype_folders()
	from millitrix.patches.fix_doctype_controller_classes import execute as fix_controllers

	fix_controllers()
	frappe.clear_cache()
	frappe.db.commit()


def _rename_corrupted_in_database() -> None:
	for name in frappe.get_all("DocType", filters={"module": "Millitrix ERP"}, pluck="name"):
		fixed = normalize_doctype_name(name)
		if fixed == name or not frappe.db.exists("DocType", name):
			continue
		if frappe.db.exists("DocType", fixed):
			continue
		try:
			frappe.rename_doc("DocType", name, fixed, force=True)
			print(f"renamed DB DocType: {name} -> {fixed}")
		except Exception as exc:
			print(f"FAILED DB {name} -> {fixed}: {exc}")


def _fix_double_prefix_in_sources() -> None:
	from millitrix.utils.client_doctype_map import CLIENT_DOCTYPES

	for path in APP_ROOT.rglob("*"):
		if not path.is_file() or path.suffix not in {".py", ".js", ".json", ".md", ".html", ".css", ".txt"}:
			continue
		try:
			text = path.read_text(encoding="utf-8")
		except (UnicodeDecodeError, OSError):
			continue
		fixed = text
		for name in sorted(CLIENT_DOCTYPES, key=len, reverse=True):
			# fix corrupted names in source text
			broken = name
			while "Millitrix Millitrix" in broken or re.search(r"\bMillitrix \w+ Millitrix ", broken):
				body = broken[len("Millitrix ") :]
				body = re.sub(r"\bMillitrix ", "", body)
				broken = "Millitrix " + body
			if broken != name:
				fixed = fixed.replace(broken, name)
		# collapse duplicate start prefixes in quoted strings
		fixed = re.sub(r'"(?:Millitrix )+', '"Millitrix ', fixed)
		if fixed != text:
			path.write_text(fixed, encoding="utf-8")
			print(f"deduped {path.relative_to(APP_ROOT)}")


def _rebuild_doctype_folders() -> None:
	by_name: dict[str, tuple[dict, Path]] = {}
	for folder in DOCTYPE_ROOT.iterdir():
		if not folder.is_dir() or folder.name.startswith("_") or folder.name == "__pycache__":
			continue
		data, src = _read_canonical_json(folder)
		if not data:
			continue
		name = normalize_doctype_name(data.get("name") or "")
		data["name"] = name
		for field in data.get("fields", []):
			if field.get("fieldtype") in {"Link", "Table"} and field.get("options"):
				field["options"] = normalize_doctype_name(field["options"])
		by_name[name] = (data, folder)

	staging = DOCTYPE_ROOT / "_rebuild_staging"
	if staging.exists():
		shutil.rmtree(staging)
	staging.mkdir()

	for name, (data, src_folder) in sorted(by_name.items()):
		correct_slug = slug(name)
		dest = staging / correct_slug
		dest.mkdir(parents=True, exist_ok=True)
		for item in src_folder.iterdir():
			if item.name in {"__pycache__"}:
				continue
			target = dest / item.name
			if item.is_dir():
				shutil.copytree(item, target, dirs_exist_ok=True)
			else:
				shutil.copy2(item, target)
		json_path = dest / f"{correct_slug}.json"
		json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
		_rename_internal_files(dest, correct_slug)
		print(f"staged {name} -> {correct_slug}")

	for folder in list(DOCTYPE_ROOT.iterdir()):
		if folder.name in {"_rebuild_staging", "__pycache__"}:
			continue
		if folder.is_file() and folder.name == "__init__.py":
			continue
		if folder.is_dir():
			shutil.rmtree(folder)
			print(f"removed {folder.name}")

	for folder in sorted(staging.iterdir()):
		shutil.move(str(folder), str(DOCTYPE_ROOT / folder.name))
	staging.rmdir()
	print(f"rebuilt {len(by_name)} doctype folders")


def _read_canonical_json(folder: Path) -> tuple[dict | None, Path | None]:
	json_files = [p for p in folder.glob("*.json") if not p.name.startswith("test_")]
	if not json_files:
		return None, None
	best_name = None
	best_data = None
	best_path = None
	for path in json_files:
		try:
			data = json.loads(path.read_text(encoding="utf-8"))
		except (json.JSONDecodeError, OSError):
			continue
		if data.get("doctype") != "DocType":
			continue
		name = normalize_doctype_name(data.get("name") or "")
		if name in CLIENT_DOCTYPES:
			return data, path
		if best_name is None or len(name) < len(best_name):
			best_name, best_data, best_path = name, data, path
	return best_data, best_path


def _rename_internal_files(folder: Path, slug_name: str) -> None:
	for path in list(folder.iterdir()):
		if path.name == "__pycache__":
			continue
		stem = path.stem
		if path.suffix in {".py", ".js", ".json"} and not stem.startswith("test_") and stem != slug_name:
			new_path = folder / f"{slug_name}{path.suffix}"
			if not new_path.exists():
				path.rename(new_path)
		elif stem.startswith("test_") and stem != f"test_{slug_name}":
			new_path = folder / f"test_{slug_name}{path.suffix}"
			if not new_path.exists():
				path.rename(new_path)
