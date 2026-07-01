# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe


def execute():
	"""Millitrix Remove Millitrix-prefixed reports replaced by Oracle-exact names."""
	for name in (
		"Millitrix Trial Balance",
		"Millitrix Account Ledger",
		"Party Ledger",
		"Party Balance Summary",
		"Millitrix Income Statement",
		"Voucher Transaction Register",
		"Item Setup Stock",
		"Millitrix Balance Sheet",
		"Millitrix Cash Book",
		"Purchase Invoice Register",
		"Sales Invoice Register",
		"Millitrix PO Pending",
		"Millitrix SO Pending",
		"Millitrix PO Register",
		"Millitrix SO Register",
	):
		if frappe.db.exists("Report", name):
			frappe.delete_doc("Report", name, force=1, ignore_permissions=True)
	frappe.db.commit()
