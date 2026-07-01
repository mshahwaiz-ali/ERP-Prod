# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe


def execute() -> None:
	_op = {"+": "Add", "-": "Subtract"}
	_side = {"NET": "Net", "DR": "Debit", "CR": "Credit", "DR/CR": "Net"}

	if frappe.db.table_exists("tabGL Statements") and frappe.db.has_column("tabGL Statements", "operation"):
		for old, new in _op.items():
			frappe.db.sql(
				"UPDATE `tabGL Statements` SET operation = %(new)s WHERE operation = %(old)s",
				{"old": old, "new": new},
			)

	if frappe.db.table_exists("tabGL Sub Statement"):
		for old, new in _op.items():
			frappe.db.sql(
				"UPDATE `tabGL Sub Statement` SET operation = %(new)s WHERE operation = %(old)s",
				{"old": old, "new": new},
			)

	if frappe.db.table_exists("tabGL Statement Account"):
		for old, new in _side.items():
			frappe.db.sql(
				"UPDATE `tabGL Statement Account` SET show_side = %(new)s WHERE show_side = %(old)s",
				{"old": old, "new": new},
			)
		if frappe.db.has_column("tabGL Statement Account", "operation"):
			frappe.db.sql("UPDATE `tabGL Statement Account` SET operation = NULL WHERE operation IS NOT NULL")

	# frappe.db.commit()  # DISABLED SAFE MODE
