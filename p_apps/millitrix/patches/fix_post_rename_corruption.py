# Fix substring-replace corruption after strip_millitrix_prefix.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]

# User-facing strings wrongly prefixed during bulk rename (_m("X") → Millitrix X).
_MSG_FIXES = (
	('_("Millitrix ', '_("'),
	('__("Millitrix ', '__("'),
	('frappe.throw("Millitrix ', 'frappe.throw("'),
	('f"Millitrix ', 'f"'),
	('}"Millitrix .strip()', '}".strip()'),
	("''Millitrix UNION", "'' UNION"),
	('f"""Millitrix ', 'f"""'),
	('"""Millitrix ', '"""'),
	("Millitrix Sub Party", "Sub Party"),
	("Millitrix Unsubmitted Document Type", "Unsubmitted Document Type"),
	("Millitrix Received Advance Adjustment", "Received Advance Adjustment"),
	("Millitrix Paid Advance Adjustment", "Paid Advance Adjustment"),
	("Chart of Accountings", "Chart of Accounting"),
)


def _fix_runtime_messages() -> None:
	for path in APP_ROOT.rglob("*"):
		if path.suffix not in {".py", ".js"}:
			continue
		if "patches" in path.parts:
			continue
		try:
			text = path.read_text(encoding="utf-8")
		except (UnicodeDecodeError, OSError):
			continue
		original = text
		for old, new in _MSG_FIXES:
			text = text.replace(old, new)
		if text != original:
			path.write_text(text, encoding="utf-8")
			print(f"fixed messages: {path.relative_to(APP_ROOT)}")


def _fix_workspace_report_links() -> None:
	import frappe

	report_map = {
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
	for old, new in report_map.items():
		frappe.db.sql(
			"""
			UPDATE `tabWorkspace Link`
			SET link_to = %s
			WHERE link_type = 'Report' AND link_to = %s
			""",
			(new, old),
		)
		print(f"workspace report link: {old} -> {new}")


def _fix_print_formats() -> None:
	import frappe

	for pf in frappe.get_all("Print Format", filters={"name": ["like", "Millitrix%"]}, fields=["name", "doc_type"]):
		_process_print_format(pf)

	# doc_type-only corruption (name already clean).
	for pf in frappe.get_all(
		"Print Format",
		filters={"doc_type": ["like", "Millitrix%"]},
		fields=["name", "doc_type"],
	):
		_process_print_format(pf)


_PRINT_DOC_TYPE_ALIASES = {
	"Payment Receipt Voucher": "Payment and Receipt Voucher",
}


def _process_print_format(pf: dict) -> None:
	import frappe

	name = pf["name"]
	doc_type = pf.get("doc_type") or ""
	if doc_type.startswith("Millitrix "):
		new_dt = doc_type[len("Millitrix ") :]
		new_dt = _PRINT_DOC_TYPE_ALIASES.get(new_dt, new_dt)
		if frappe.db.exists("DocType", new_dt):
			frappe.db.set_value("Print Format", name, "doc_type", new_dt, update_modified=False)
			print(f"fixed print format doc_type: {name} -> {new_dt}")
	if name.startswith("Millitrix "):
		new_name = name[len("Millitrix ") :]
		if not new_name:
			return
		if frappe.db.exists("Print Format", new_name):
			frappe.delete_doc("Print Format", name, force=1, ignore_permissions=True)
			print(f"deleted duplicate print format: {name}")
			return
		try:
			frappe.rename_doc("Print Format", name, new_name, force=True)
			print(f"renamed print format: {name} -> {new_name}")
		except Exception as exc:
			print(f"print format rename skipped {name}: {exc}")


def execute() -> None:
	import frappe

	_fix_runtime_messages()
	_fix_print_formats()
	_fix_workspace_report_links()

	from millitrix.utils.workspace_layout import write_all

	write_all()
	frappe.clear_cache()
	# frappe.db.commit()  # DISABLED SAFE MODE
