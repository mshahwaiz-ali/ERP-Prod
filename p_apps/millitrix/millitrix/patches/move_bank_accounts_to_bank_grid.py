# Copyright (c) 2026, Millitrix and contributors
"""Move Bank Account rows from nested branch grid to Bank-level Accounts grid."""

from __future__ import annotations

import frappe


def execute() -> None:
	nested = frappe.db.sql(
		"""
		SELECT ba.name, ba.parent AS branch_row, bb.parent AS bank_name, bb.branchid
		FROM `tabBank Account` ba
		INNER JOIN `tabBank Branch` bb ON bb.name = ba.parent
		WHERE ba.parenttype = 'Bank Branch' AND ba.parentfield = 'accounts'
		""",
		as_dict=True,
	)
	if not nested:
		return

	for row in nested:
		frappe.db.set_value(
			"Bank Account",
			row.name,
			{
				"parent": row.bank_name,
				"parenttype": "Bank",
				"parentfield": "accounts",
				"branchid": row.branchid or frappe.db.get_value("Bank Branch", row.branch_row, "branchid"),
			},
		)

	frappe.db.commit()
	print(f"Moved {len(nested)} bank account row(s) to Bank Accounts grid")
