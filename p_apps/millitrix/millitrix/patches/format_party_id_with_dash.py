# Copyright (c) 2026, Millitrix and contributors
"""Convert legacy numeric Party Number (110001) to 11-0001 format."""

from __future__ import annotations

import frappe

from millitrix.utils.party import format_party_id, parse_party_id


def execute() -> None:
	rows = frappe.get_all("Party", fields=["name", "partyid", "pcat_id"])
	if not rows:
		return

	for row in rows:
		raw = str(row.partyid or "").strip()
		if not raw or "-" in raw:
			continue

		category_no, sequence = parse_party_id(raw)
		new_id = format_party_id(category_no, sequence)
		if new_id == raw:
			continue

		old_name = row.name
		frappe.db.set_value("Party", old_name, "partyid", new_id, update_modified=False)
		if old_name != new_id:
			frappe.rename_doc("Party", old_name, new_id, force=True, merge=False)

	frappe.db.commit()
	print(f"Formatted {len(rows)} party record(s) to category-0001 pattern")
