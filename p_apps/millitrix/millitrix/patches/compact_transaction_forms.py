# Compact multi-column layouts for transaction forms (PI first).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

# Parent form: fieldname -> columns (of 12) for side-by-side header rows.
PI_HEADER_COLUMNS: dict[str, int] = {
	"purchinvno": 3,
	"invdate": 3,
	"itemcode": 3,
	"supplierid": 4,
	"brokerid": 4,
	"sub_partyid": 4,
	"kantatype": 3,
	"amntby": 3,
	"brokery": 3,
	"brokery_auto_calc": 2,
	"brokery_dr_supplier": 2,
	"borrow": 3,
	"remarks": 12,
	"amount": 4,
	"payable": 4,
}

PI_DETAIL_COLUMNS = 4  # 3 fields per row in row-edit panel


def _set_columns(data: dict, mapping: dict[str, int]) -> bool:
	changed = False
	for field in data.get("fields", []):
		fname = field.get("fieldname")
		if fname not in mapping:
			continue
		want = mapping[fname]
		if field.get("columns") != want:
			field["columns"] = want
			changed = True
	return changed


def _compact_pi_detail(data: dict) -> bool:
	changed = False
	for field in data.get("fields", []):
		if field.get("hidden") or field.get("fieldtype") in ("Section Break", "Column Break"):
			continue
		if field.get("columns") != PI_DETAIL_COLUMNS:
			field["columns"] = PI_DETAIL_COLUMNS
			changed = True
	return changed


def _apply_posted_list_hide(data: dict) -> bool:
	if not data.get("is_submittable"):
		return False
	changed = False
	for field in data.get("fields", []):
		if field.get("fieldname") == "posted" and field.get("in_list_view"):
			field["in_list_view"] = 0
			changed = True
	return changed


def apply_json() -> None:
	targets = {
		"purchase_invoice": PI_HEADER_COLUMNS,
	}
	for folder, mapping in targets.items():
		json_path = BASE / folder / f"{folder}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		changed = _set_columns(data, mapping)
		changed = _apply_posted_list_hide(data) or changed
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			print("compact form", data.get("name"))

	detail_path = BASE / "purchase_invoice_detail" / "purchase_invoice_detail.json"
	if detail_path.exists():
		data = json.loads(detail_path.read_text(encoding="utf-8"))
		if _compact_pi_detail(data):
			detail_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			print("compact form", data.get("name"))


def _sync_db() -> None:
	for fname, cols in PI_HEADER_COLUMNS.items():
		if frappe.db.exists(
			"DocField",
			{"parent": "Purchase Invoice", "fieldname": fname, "parenttype": "DocType"},
		):
			frappe.db.set_value(
				"DocField",
				{"parent": "Purchase Invoice", "fieldname": fname, "parenttype": "DocType"},
				"columns",
				cols,
				update_modified=False,
			)
	if frappe.db.exists("DocType", "Purchase Invoice Detail"):
		for row in frappe.get_all(
			"DocField",
			filters={"parent": "Purchase Invoice Detail", "parenttype": "DocType"},
			fields=["fieldname", "hidden", "fieldtype"],
		):
			if row.hidden or row.fieldtype in ("Section Break", "Column Break"):
				continue
			frappe.db.set_value(
				"DocField",
				{"parent": "Purchase Invoice Detail", "fieldname": row.fieldname, "parenttype": "DocType"},
				"columns",
				PI_DETAIL_COLUMNS,
				update_modified=False,
			)
	for doctype in frappe.get_all("DocType", filters={"module": "Millitrix ERP", "is_submittable": 1}, pluck="name"):
		if frappe.db.exists(
			"DocField",
			{"parent": doctype, "fieldname": "posted", "parenttype": "DocType"},
		):
			frappe.db.set_value(
				"DocField",
				{"parent": doctype, "fieldname": "posted", "parenttype": "DocType"},
				"in_list_view",
				0,
				update_modified=False,
			)
	frappe.db.commit()


def execute() -> None:
	apply_json()
	_sync_db()
	frappe.clear_cache(doctype="DocType")


if __name__ == "__main__":
	apply_json()
