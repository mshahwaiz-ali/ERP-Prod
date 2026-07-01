# Convert autoname Int fields to Data so PREFIX-YYMM-0001 strings can be stored.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.utils.naming import DOCTYPE_PREFIX, PREFIX_EXCLUDE

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

# Keep numeric autoname for Oracle GL account codes.
KEEP_INT = {("Chart of Accounting", "accid"), ("Party Category", "pcat_id")}


def execute() -> None:
	updated: list[tuple[str, str]] = []
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		jp = folder / f"{folder.name}.json"
		if not jp.exists():
			continue
		data = json.loads(jp.read_text(encoding="utf-8"))
		if data.get("istable"):
			continue
		doctype = data.get("name") or ""
		autoname = data.get("autoname") or ""
		if not autoname.startswith("field:"):
			continue
		fieldname = autoname.split(":", 1)[1]
		if (doctype, fieldname) in KEEP_INT:
			continue
		if doctype in PREFIX_EXCLUDE and doctype != "Party":
			continue
		if doctype not in DOCTYPE_PREFIX and doctype != "Party":
			continue

		changed = False
		for field in data.get("fields", []):
			if field.get("fieldname") != fieldname:
				continue
			if field.get("fieldtype") == "Int":
				field["fieldtype"] = "Data"
				changed = True
			break

		if changed:
			jp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			updated.append((doctype, fieldname))

	for doctype, fieldname in updated:
		_alter_column_if_int(doctype, fieldname)
		try:
			frappe.reload_doc("millitrix_erp", "doctype", frappe.scrub(doctype))
		except Exception:
			pass

	# frappe.db.commit()  # DISABLED SAFE MODE
	frappe.clear_cache(doctype="DocType")
	print(f"autoname Int→Data: {len(updated)} fields")


def _alter_column_if_int(doctype: str, fieldname: str) -> None:
	table = f"tab{doctype}"
	if not frappe.db.table_exists(table):
		return
	col_type = frappe.db.sql(
		f"SHOW COLUMNS FROM `{table}` WHERE Field = %s",
		fieldname,
	)
	if not col_type:
		return
	raw = (col_type[0][1] or "").lower()
	if "int" in raw:
		frappe.db.sql_ddl(
			f"ALTER TABLE `{table}` MODIFY `{fieldname}` VARCHAR(140)"
		)
