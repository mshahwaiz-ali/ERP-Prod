# Drop saved GridView column picks (old 10-field cap) so child grids auto-show all fields.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json

import frappe


def execute() -> None:
	parents = frappe.get_all(
		"DocType",
		filters={"module": "Millitrix ERP", "istable": 0},
		pluck="name",
	)
	if not parents:
		return

	rows = frappe.db.sql(
		"""
		SELECT `user`, doctype, data
		FROM `__UserSettings`
		WHERE doctype IN %(parents)s
		""",
		{"parents": parents},
		as_dict=True,
	)

	cleared = 0
	for row in rows:
		data = json.loads(row.data or "{}")
		if "GridView" not in data:
			continue
		del data["GridView"]
		frappe.db.sql(
			"""
			UPDATE `__UserSettings`
			SET data = %s
			WHERE `user` = %s AND doctype = %s
			""",
			(json.dumps(data), row.user, row.doctype),
		)
		frappe.cache.hdel("_user_settings", f"{row.doctype}::{row.user}")
		cleared += 1

	if cleared:
		print("cleared GridView", cleared)

	# frappe.db.commit()  # DISABLED SAFE MODE
