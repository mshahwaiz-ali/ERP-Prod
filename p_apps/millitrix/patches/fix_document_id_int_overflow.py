# Legacy document numbers (location + YYMM + seq) exceed signed INT max for location >= 2.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

AUTONAME_ID_FIELDS = {
	"Purchase Order": "ponumber",
	"Purchase Invoice": "purchinvno",
	"Sales Order": "sonumber",
	"Sales Invoice": "salesinvno",
	"Purchase Return": "purchretno",
	"Sales Return": "salesretno",
	"Opening Stock": "sopenid",
	"Stock Transfer Note": "transferno",
	"Purchase Other Bill": "pbillno",
	"Sales Other Bill": "sbillno",
	"Payment and Receipt Voucher": "pnrno",
	"In Out Gate Pass": "gatepassno",
	"Voucher Transaction": "voucherno",
}

DOCUMENT_ID_FIELDS = [
	("Voucher Transaction", "documentid"),
	("In Out Gate Pass", "documentid"),
	("Document Transaction", "documentid"),
	("Payment and Receipt Document", "documentid"),
	("Cash and Bank Voucher Document", "documentid"),
	("Hawala Invoice", "documentid"),
	("Adjustment Invoice", "documentid"),
	("Party Gross Margin Invoice", "documentid"),
	("Un Submit Documents", "documentid"),
	("Closing and Adjustment Entries", "documentid"),
]

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"


def execute():
	changed = []
	for doctype, fieldname in AUTONAME_ID_FIELDS.items():
		if _int_to_data(doctype, fieldname):
			changed.append((doctype, fieldname))
	for doctype, fieldname in DOCUMENT_ID_FIELDS:
		if _int_to_data(doctype, fieldname):
			changed.append((doctype, fieldname))

	_alter_columns({(d, f) for d, f in changed})
	# Also alter any JSON-updated fields already marked Data in DocField but still INT in DB.
	for doctype, fieldname in {**AUTONAME_ID_FIELDS, **dict(DOCUMENT_ID_FIELDS)}.items():
		_alter_column_if_int(doctype, fieldname)

	if changed:
		# frappe.db.commit()  # DISABLED SAFE MODE
		for doctype in {c[0] for c in changed}:
			frappe.clear_cache(doctype=doctype)
		frappe.logger("millitrix").info("Document id fields converted Int→Data: %s", changed)


def _alter_columns(pairs: set[tuple[str, str]]) -> None:
	for doctype, fieldname in pairs:
		_alter_column_if_int(doctype, fieldname)


def _alter_column_if_int(doctype: str, fieldname: str) -> None:
	table = f"tab{doctype}"
	if not frappe.db.table_exists(table) or not frappe.db.has_column(table, fieldname):
		return
	row = frappe.db.sql(f"SHOW COLUMNS FROM `{table}` WHERE Field = %s", fieldname, as_dict=True)
	if not row:
		return
	col_type = (row[0].get("Type") or "").lower()
	if col_type.startswith("int"):
		frappe.db.sql_ddl(f"ALTER TABLE `{table}` MODIFY `{fieldname}` varchar(140)")


def _int_to_data(doctype: str, fieldname: str) -> bool:
	if not frappe.db.exists("DocType", doctype):
		return False
	meta = frappe.get_meta(doctype)
	if not meta.has_field(fieldname):
		return False
	if meta.get_field(fieldname).fieldtype != "Int":
		return False

	frappe.db.set_value("DocField", {"parent": doctype, "fieldname": fieldname}, "fieldtype", "Data")
	_sync_json(doctype, fieldname)
	return True


def _sync_json(doctype: str, fieldname: str) -> None:
	path = BASE / frappe.scrub(doctype) / f"{frappe.scrub(doctype)}.json"
	if not path.exists():
		return
	data = json.loads(path.read_text())
	for field in data.get("fields", []):
		if field.get("fieldname") == fieldname and field.get("fieldtype") == "Int":
			field["fieldtype"] = "Data"
			break
	path.write_text(json.dumps(data, indent=1) + "\n")
