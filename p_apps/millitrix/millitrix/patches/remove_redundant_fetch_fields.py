# Remove redundant fetch_from display fields — Link titles replace them.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

# Functional fetch tails — not pure name/description duplicates.
KEEP_FETCH_TAILS = frozenset(
	{
		"rate",
		"iclassid",
		"bagweight",
		"mundtype",
		"weight",
		"weightreceived",
		"truckqty",
	}
)


def _fetch_tail(fetch_from: str) -> str:
	return (fetch_from or "").rsplit(".", 1)[-1].strip().lower()


def should_remove_fetch_field(field: dict) -> bool:
	fetch_from = field.get("fetch_from")
	if not fetch_from:
		return False
	tail = _fetch_tail(fetch_from)
	if tail in KEEP_FETCH_TAILS:
		return False
	return True


def apply_json() -> dict[str, list[str]]:
	removed: dict[str, list[str]] = {}
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		doctype = data.get("name") or folder.name.replace("_", " ").title()
		to_remove = {
			f.get("fieldname")
			for f in data.get("fields", [])
			if f.get("fieldname") and should_remove_fetch_field(f)
		}
		if not to_remove:
			continue
		data["fields"] = [f for f in data["fields"] if f.get("fieldname") not in to_remove]
		order = data.get("field_order") or []
		data["field_order"] = [fn for fn in order if fn not in to_remove]
		json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
		removed[doctype] = sorted(to_remove)
		print("removed fetch fields", doctype, removed[doctype])
	return removed


def _sync_db_removals(removed: dict[str, list[str]]) -> None:
	for doctype, fieldnames in removed.items():
		for fieldname in fieldnames:
			frappe.db.delete(
				"DocField",
				{
					"parent": doctype,
					"fieldname": fieldname,
					"parenttype": "DocType",
				},
			)
	frappe.db.commit()


def execute() -> None:
	removed = apply_json()
	if removed:
		_sync_db_removals(removed)
	frappe.clear_cache(doctype="DocType")


if __name__ == "__main__":
	apply_json()
