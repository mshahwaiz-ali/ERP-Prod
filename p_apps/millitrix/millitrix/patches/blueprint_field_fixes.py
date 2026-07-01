# Blueprint field fixes — read_only calculated fields, missing header fields.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.patches.apply_ui_field_options import apply as apply_json

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

READ_ONLY_FIELDS: dict[str, list[str]] = {
	"Purchase Order": ["amount", "payable"],
	"Sales Order": ["amount", "receivable"],
	"Purchase Return": ["amount", "receivable", "brokerypayable", "brokeramnt"],
	"Sales Return": ["amount", "payable", "brokerypayable", "brokeramnt"],
	"Purchase Invoice Detail": ["total_weight", "mund", "bagamnt", "netweight", "totalamnt"],
	"Sales Invoice Detail": ["netweight", "totalamnt"],
	"Purchase Return Detail": ["total_weight", "mund", "bagamnt", "netweight", "totalamnt"],
	"Sales Return Detail": ["total_weight", "mund", "bagamnt", "netweight", "totalamnt", "brokeramnt"],
	"Gate Pass Detail": ["netweight"],
	"Stock Transfer Detail": ["netweight"],
	"Payment and Receipt Voucher": ["amount", "balance"],
	"Payment and Receipt Document": ["party_name", "item_name", "docbalamnt", "balance"],
}


def _patch_json_files() -> None:
	for folder in sorted(BASE.iterdir()):
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		doctype = data.get("name") or folder.name
		changed = False

		if doctype == "Purchase Invoice":
			fields = {f["fieldname"]: f for f in data.get("fields", [])}
			if "mundtype" not in fields:
				data["field_order"].insert(
					data["field_order"].index("kantatype") + 1,
					"mundtype",
				)
				data["fields"].append(
					{
						"fieldname": "mundtype",
						"fieldtype": "Select",
						"label": "Mund Type",
						"options": "New Mund\nOld Mund\nQuantity",
						"default": "New Mund",
					}
				)
				changed = True

		if doctype == "Sales Invoice Detail":
			new_fields = [f for f in data.get("fields", []) if f.get("fieldname") != "inkanta"]
			if len(new_fields) != len(data.get("fields", [])):
				data["fields"] = new_fields
				data["field_order"] = [x for x in data.get("field_order", []) if x != "inkanta"]
				changed = True

		if doctype == "Sales Return Detail":
			for field in data.get("fields", []):
				if field.get("fieldname") == "inkanta" and field.get("fieldtype") != "Float":
					field["fieldtype"] = "Float"
					changed = True

		for field in data.get("fields", []):
			fname = field.get("fieldname")
			if fname in READ_ONLY_FIELDS.get(doctype, []):
				if not field.get("read_only"):
					field["read_only"] = 1
					changed = True
			if doctype == "Gate Pass Detail" and fname == "netweight" and not field.get("read_only"):
				field["read_only"] = 1
				changed = True

		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			print("blueprint fix", doctype)


def execute() -> None:
	_patch_json_files()
	apply_json()
	frappe.clear_cache(doctype="DocType")
