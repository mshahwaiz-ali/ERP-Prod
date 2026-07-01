# Remove Millitrix prefix from DocType / Report names — module is already Millitrix ERP.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
import re
from pathlib import Path

from millitrix.utils.client_doctype_map import (
	MILLITRIX_PREFIX,
	slug,
	strip_rename_map,
)

APP_ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = APP_ROOT / "millitrix_erp" / "doctype"
REPORT_ROOT = APP_ROOT / "millitrix_erp" / "report"

SKIP_REPLACE_IN = {
	"client_doctype_map.py",
	"prefix_millitrix_doctypes.py",
	"strip_millitrix_prefix.py",
	"rename_doctypes_to_client_names.py",
}

# Reports that still carry a Millitrix prefix in report_name.
REPORT_STRIP_MAP: dict[str, str] = {
	"Millitrix BankBook": "BankBook",
	"Millitrix BankFinanceStatus": "BankFinanceStatus",
	"Millitrix BankStatus": "BankStatus",
	"Millitrix PartyLedger": "PartyLedger",
	"Millitrix PartyBalance": "PartyBalance",
	"Millitrix Party_Info": "Party_Info",
	"Millitrix Party_Bal_Paid": "Party_Bal_Paid",
	"Millitrix PartyPRegister": "PartyPRegister",
	"Millitrix PartyRRegister": "PartyRRegister",
	"Millitrix PartyBardana": "PartyBardana",
	"Millitrix PartyBardanaBincard": "PartyBardanaBincard",
}


def _all_replacements() -> list[tuple[str, str]]:
	items = list(strip_rename_map().items()) + list(REPORT_STRIP_MAP.items())
	return sorted(items, key=lambda x: len(x[0]), reverse=True)


def execute() -> None:
	import frappe

	from millitrix.patches.fix_doctype_controller_classes import execute as fix_controllers

	_rename_reports_in_database()
	_rename_doctypes_in_database()
	_update_source_files()
	_rename_doctype_folders()
	_fix_accounts_opening_entry_mode()
	fix_controllers()
	_regenerate_workspaces()
	frappe.clear_cache()
	frappe.db.commit()


def _rename_doctypes_in_database() -> None:
	import frappe

	for old, new in _all_replacements():
		if old == new or not old.startswith(MILLITRIX_PREFIX):
			continue
		if not frappe.db.exists("DocType", old):
			continue
		if frappe.db.exists("DocType", new):
			continue
		try:
			frappe.rename_doc("DocType", old, new, force=True)
			print(f"renamed DocType: {old} -> {new}")
		except Exception as exc:
			print(f"FAILED DocType {old} -> {new}: {exc}")


def _rename_reports_in_database() -> None:
	import frappe

	for old, new in sorted(REPORT_STRIP_MAP.items(), key=lambda x: len(x[0]), reverse=True):
		if not frappe.db.exists("Report", old):
			continue
		if frappe.db.exists("Report", new):
			if old != new:
				frappe.delete_doc("Report", old, force=1, ignore_permissions=True)
			continue
		try:
			frappe.rename_doc("Report", old, new, force=True)
			print(f"renamed Report: {old} -> {new}")
		except Exception as exc:
			print(f"FAILED Report {old} -> {new}: {exc}")


def _update_source_files() -> None:
	replacements = _all_replacements()
	for path in APP_ROOT.rglob("*"):
		if not path.is_file():
			continue
		if path.suffix not in {".py", ".js", ".json", ".md", ".html", ".css", ".txt"}:
			continue
		if path.name in SKIP_REPLACE_IN:
			continue
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


def _fix_accounts_opening_entry_mode() -> None:
	"""GL Opening: Item / Employee / Party only (client Oracle UI)."""
	import frappe

	path = DOCTYPE_ROOT / "accounts_opening" / "accounts_opening.json"
	if not path.exists():
		# folder may still be old name before migrate re-read
		for candidate in DOCTYPE_ROOT.glob("**/accounts_opening.json"):
			path = candidate
			break
	if not path.exists():
		return

	data = json.loads(path.read_text(encoding="utf-8"))
	changed = False
	for field in data.get("fields", []):
		if field.get("fieldname") == "entry_mode":
			field["options"] = "Item\nEmployee\nParty"
			field["default"] = "Party"
			changed = True
		elif field.get("fieldname") == "location_id":
			field["label"] = "Location"
			if field.get("options", "").startswith(MILLITRIX_PREFIX):
				field["options"] = field["options"].replace(MILLITRIX_PREFIX, "")
				changed = True
		elif field.get("fieldname") == "details":
			if field.get("options", "").startswith(MILLITRIX_PREFIX):
				field["options"] = field["options"].replace(MILLITRIX_PREFIX, "")
				changed = True
	if changed:
		path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
		print("fixed accounts_opening.json entry modes")

	detail_path = path.parent.parent / "accounts_opening_detail" / "accounts_opening_detail.json"
	if not detail_path.exists():
		for candidate in DOCTYPE_ROOT.glob("**/accounts_opening_detail.json"):
			detail_path = candidate
			break
	if detail_path.exists():
		detail = json.loads(detail_path.read_text(encoding="utf-8"))
		detail_changed = False
		for field in detail.get("fields", []):
			if field.get("fieldname") == "partyid":
				field["label"] = "Party"
			if field.get("fieldtype") in {"Link", "Table"} and field.get("options", "").startswith(MILLITRIX_PREFIX):
				field["options"] = field["options"].replace(MILLITRIX_PREFIX, "")
				detail_changed = True
			elif field.get("fieldname") == "partyid" and field.get("label") == "Party":
				detail_changed = True
		if detail_changed:
			detail_path.write_text(json.dumps(detail, indent=1) + "\n", encoding="utf-8")
			print("fixed accounts_opening_detail.json")

	# Normalize stored entry_mode values in DB (table may not exist until first save).
	if frappe.db.exists("DocType", "Accounts Opening"):
		try:
			frappe.db.sql(
				"""
				UPDATE `tabAccounts Opening`
				SET entry_mode = CASE entry_mode
					WHEN 'Millitrix Party' THEN 'Party'
					WHEN 'Millitrix Account' THEN 'Party'
					ELSE entry_mode
				END
				WHERE entry_mode IN ('Millitrix Party', 'Millitrix Account')
				"""
			)
		except Exception:
			pass


def _regenerate_workspaces() -> None:
	from millitrix.utils.workspace_layout import write_all

	write_all()
