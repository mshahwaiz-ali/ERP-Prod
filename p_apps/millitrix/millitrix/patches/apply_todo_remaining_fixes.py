# Copyright (c) 2026, Millitrix and contributors
# Remaining todo.md fixes — bardana field, crash refine Float, re-apply blueprint rules.

from __future__ import annotations

import json
from pathlib import Path

import frappe

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

BARDANA_DETAIL_DOCTYPES = (
	"sales_invoice_detail",
	"purchase_invoice_detail",
	"sales_return_detail",
	"purchase_return_detail",
)

BARDANA_FIELD = {
	"fieldname": "bardana",
	"fieldtype": "Currency",
	"in_list_view": 0,
	"label": "Bardana",
	"read_only": 1,
}


def _add_bardana_field(json_path: Path) -> bool:
	if not json_path.exists():
		return False
	data = json.loads(json_path.read_text(encoding="utf-8"))
	fields = data.get("fields", [])
	if any(f.get("fieldname") == "bardana" for f in fields):
		return False
	insert_after = "bagamnt"
	new_fields = []
	added = False
	for field in fields:
		new_fields.append(field)
		if field.get("fieldname") == insert_after:
			new_fields.append(dict(BARDANA_FIELD))
			added = True
	if not added:
		new_fields.append(dict(BARDANA_FIELD))
		added = True
	data["fields"] = new_fields
	order = list(data.get("field_order") or [])
	if "bardana" not in order:
		if "bagamnt" in order:
			idx = order.index("bagamnt") + 1
			order.insert(idx, "bardana")
		else:
			order.append("bardana")
		data["field_order"] = order
	json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
	return True


def _float_prod_fields(json_path: Path) -> bool:
	if not json_path.exists():
		return False
	data = json.loads(json_path.read_text(encoding="utf-8"))
	changed = False
	for field in data.get("fields", []):
		if field.get("fieldname") in ("prod_1", "prod_2") and field.get("fieldtype") != "Float":
			field["fieldtype"] = "Float"
			field["precision"] = "2"
			changed = True
	if changed:
		json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
	return changed


def execute() -> None:
	updated: list[str] = []

	for folder in BARDANA_DETAIL_DOCTYPES:
		path = BASE / folder / f"{folder}.json"
		if _add_bardana_field(path):
			updated.append(folder)

	crash_input = BASE / "crash_refine_input" / "crash_refine_input.json"
	if _float_prod_fields(crash_input):
		updated.append("crash_refine_input")

	from millitrix.patches.apply_blueprint_form_rules import execute as apply_blueprint

	apply_blueprint()

	for name in updated:
		try:
			frappe.reload_doc("millitrix_erp", "doctype", name)
		except Exception:
			pass

	frappe.clear_cache(doctype="DocType")
	print(f"todo remaining fixes applied ({len(updated)} json updates + blueprint rules)")
