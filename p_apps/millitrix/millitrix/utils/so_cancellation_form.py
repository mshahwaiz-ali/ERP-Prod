# Copyright (c) 2026, Millitrix and contributors
# Oracle SOCancel.fmb — open SO LOV for cancellation lines.

from __future__ import annotations

import frappe
from frappe.utils import cint

from millitrix.utils.field_normalizers import normalize_order_status
from millitrix.utils.order_balance import SIDE_SALES, open_truck_qty_for_order


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_open_sales_orders(
	doctype: str,
	txt: str,
	searchfield: str,
	start: int,
	page_len: int,
	filters: dict | None = None,
):
	"""Submitted SOs with remaining open truck qty for the header party/location."""
	filters = filters or {}
	partyid = filters.get("partyid")
	location_id = filters.get("location_id")
	txt = (txt or "").strip()

	conditions = ["so.docstatus = 1"]
	values: dict = {"start": cint(start), "page_len": cint(page_len)}

	if partyid:
		conditions.append("so.customerid = %(partyid)s")
		values["partyid"] = partyid
	if location_id:
		conditions.append("so.location_id = %(location_id)s")
		values["location_id"] = location_id
	if txt:
		conditions.append("(so.name LIKE %(txt)s OR so.itemcode LIKE %(txt)s)")
		values["txt"] = f"%{txt}%"

	rows = frappe.db.sql(
		f"""
		SELECT so.name, so.itemcode, so.status
		FROM `tabSales Order` so
		WHERE {" AND ".join(conditions)}
		ORDER BY so.sodate DESC, so.name DESC
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
		if open_truck_qty_for_order(row.name, SIDE_SALES) <= 0:
			continue
		results.append([row.name, row.itemcode or ""])

	return results
