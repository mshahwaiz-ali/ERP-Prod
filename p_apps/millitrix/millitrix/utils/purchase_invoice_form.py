# Copyright (c) 2026, Millitrix and contributors
# Oracle PurchInvoice.fmb — header defaults on item select.

from __future__ import annotations

import frappe

from millitrix.utils.bardana_items import is_bardana_item


@frappe.whitelist()
def fetch_item_header_defaults(itemcode: str) -> dict:
	"""Oracle WHEN-VALIDATE ITEMCODE — mundtype + amount-by (bag vs mund)."""
	if not itemcode or not frappe.db.exists("Item Setup", itemcode):
		return {"mundtype": "New Mund", "amntby": "Mund", "is_bardana": False}

	mundtype = frappe.db.get_value("Item Setup", itemcode, "mundtype") or "New Mund"
	bardana = is_bardana_item(itemcode)
	amntby = "Bag Quantity" if bardana else "Mund"
	return {"mundtype": mundtype, "amntby": amntby, "is_bardana": bardana}
