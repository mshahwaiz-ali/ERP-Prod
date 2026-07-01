# Apply title_field + show_title_field_in_link on master DocTypes (names in Link LOVs).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

TITLE_CANDIDATES = (
	"party_name",
	"itemname",
	"ename",
	"bankname",
	"store_name",
	"cityname",
	"module",
	"description",
	"short_name",
	"name",
)

SKIP_TITLE_FIELDS = frozenset({"doctypeid"})

# DocType -> (title_field, search_fields)
EXPLICIT: dict[str, tuple[str, str]] = {
	"Mill Information": ("description", "description,short_name,company_id"),
	"Location": ("description", "description,short_name,location_id"),
	"Bank": ("bankname", "bankname,shortname,bankid"),
	"Other Contact Setup": ("name", "name,contactid"),
	"Chart of Accounting": ("description", "description,accid"),
	"Item Setup": ("itemname", "itemname,itemcode"),
	"Party": ("party_name", "party_name,partyid"),
	"Employee Setup": ("ename", "ename,empno"),
	"Store Setup": ("store_name", "store_name,storeid"),
	"Voucher Type": ("description", "description,vouchertype_id"),
	"User Rights": ("username", "username,userid,empno"),
	"Module": ("module", "module,moduleid"),
}


def _id_field(autoname: str) -> str | None:
	if autoname.startswith("field:"):
		return autoname.split(":", 1)[1]
	return None


def _pick_title_field(data: dict, id_field: str | None) -> str | None:
	name = data.get("name")
	if name in EXPLICIT:
		return EXPLICIT[name][0]

	fields = {
		f["fieldname"]: f
		for f in data.get("fields", [])
		if f.get("fieldtype") not in ("Section Break", "Column Break", "Tab Break", "Table", "HTML")
	}
	for cand in TITLE_CANDIDATES:
		if cand in fields and cand != id_field:
			return cand

	for fn, field in fields.items():
		if fn == id_field or fn in SKIP_TITLE_FIELDS:
			continue
		if field.get("fieldtype") in ("Data", "Small Text", "Text") and field.get("in_list_view"):
			return fn
	return None


def _search_fields(data: dict, title_field: str, id_field: str | None) -> str:
	name = data.get("name")
	if name in EXPLICIT:
		return EXPLICIT[name][1]
	parts = [title_field]
	if id_field and id_field not in parts:
		parts.append(id_field)
	return ",".join(parts)


def apply_to_doctype_json(path: Path) -> bool:
	data = json.loads(path.read_text(encoding="utf-8"))
	if data.get("istable"):
		return False
	if not data.get("autoname"):
		return False

	id_field = _id_field(data.get("autoname", ""))
	title_field = _pick_title_field(data, id_field)
	if not title_field or title_field in SKIP_TITLE_FIELDS:
		changed = False
		for key in ("title_field", "show_title_field_in_link", "search_fields"):
			if key in data:
				del data[key]
				changed = True
		if changed:
			path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
		return changed

	# Transaction prefixes handled by apply_document_naming_and_display patch.
	from millitrix.utils.naming import DOCTYPE_PREFIX

	if data.get("name") in DOCTYPE_PREFIX:
		return False

	changed = False
	if data.get("title_field") != title_field:
		data["title_field"] = title_field
		changed = True
	if not data.get("show_title_field_in_link"):
		data["show_title_field_in_link"] = 1
		changed = True

	search_fields = _search_fields(data, title_field, id_field)
	if data.get("search_fields") != search_fields:
		data["search_fields"] = search_fields
		changed = True

	if changed:
		path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
	return changed


def apply_all(doctype_root: str | Path) -> list[str]:
	root = Path(doctype_root)
	updated: list[str] = []
	for path in sorted(root.glob("*/*.json")):
		if apply_to_doctype_json(path):
			updated.append(path.parent.name)
	return updated


if __name__ == "__main__":
	root = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"
	changed = apply_all(root)
	print(f"Updated {len(changed)} DocTypes")
	for name in changed:
		print(f" - {name}")
