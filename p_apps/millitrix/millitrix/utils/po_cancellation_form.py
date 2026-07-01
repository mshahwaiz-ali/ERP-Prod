# Copyright (c) 2026, Millitrix and contributors
# Oracle POCancel.fmb — open PO LOV for cancellation lines.

from __future__ import annotations

import frappe
from frappe.utils import cint

from millitrix.utils.field_normalizers import normalize_order_status
from millitrix.utils.order_balance import SIDE_PURCHASE, open_truck_qty_for_order


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_open_purchase_orders(
	doctype: str,
	txt: str,
	searchfield: str,
	start: int,
	page_len: int,
	filters: dict | None = None,
):
	"""Submitted POs with remaining open truck qty for the header party/location."""
	filters = filters or {}
	partyid = filters.get("partyid")
	location_id = filters.get("location_id")
	txt = (txt or "").strip()

	conditions = ["po.docstatus = 1"]
	values: dict = {"start": cint(start), "page_len": cint(page_len)}

	if partyid:
		conditions.append("po.supplierid = %(partyid)s")
		values["partyid"] = partyid
	if location_id:
		conditions.append("po.location_id = %(location_id)s")
		values["location_id"] = location_id
	if txt:
		conditions.append("(po.name LIKE %(txt)s OR po.itemcode LIKE %(txt)s)")
		values["txt"] = f"%{txt}%"

	rows = frappe.db.sql(
		f"""
		SELECT po.name, po.itemcode, po.status
		FROM `tabPurchase Order` po
		WHERE {" AND ".join(conditions)}
		ORDER BY po.podate DESC, po.name DESC
		LIMIT %(start)s, %(page_len)s
		""",
		values,
		as_dict=True,
	)

	results = []
	for row in rows:
		status = normalize_order_status(row.status)
		if status not in ("IN", "IP"):
			continue
		if open_truck_qty_for_order(row.name, SIDE_PURCHASE) <= 0:
			continue
		results.append([row.name, row.itemcode or ""])

	return results
