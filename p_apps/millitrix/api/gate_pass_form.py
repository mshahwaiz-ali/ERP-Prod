# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.api.permissions import require_permission
from millitrix.utils.erpnext_compat import get_session_location
from millitrix.utils.gate_pass_form import (
	get_bag_line_defaults,
	get_header_item_defaults,
	search_bagid,
	search_header_item,
)


def _resolve_location(location_id: str | None) -> str:
	location_id = (location_id or "").strip() or (get_session_location() or "").strip()
	if location_id:
		return location_id
	location_id = frappe.db.get_single_value("GL Parameter", "location_id") or ""
	if location_id:
		return location_id
	frappe.throw(frappe._("Location is required — set session location or GL Parameter"))


@frappe.whitelist()
def fetch_item_defaults(
	itemcode: str,
	location_id: str | None = None,
	gpdate: str | None = None,
):
	require_permission("In Out Gate Pass", "read")
	if not itemcode:
		frappe.throw(frappe._("Item is required"))
	return get_header_item_defaults(
		location_id=_resolve_location(location_id),
		itemcode=itemcode,
		gpdate=gpdate or None,
	)


@frappe.whitelist()
def fetch_bag_defaults(
	storeid: str,
	bagid: str,
	location_id: str | None = None,
	emptybags: str | None = None,
	itemcode: str | None = None,
	gpdate: str | None = None,
):
	require_permission("In Out Gate Pass", "read")
	if not storeid or not bagid:
		frappe.throw(frappe._("Store and Bag are required"))
	return get_bag_line_defaults(
		location_id=_resolve_location(location_id),
		storeid=storeid,
		bagid=bagid,
		emptybags=emptybags,
		itemcode=itemcode,
		gpdate=gpdate or None,
	)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def itemcode_query(doctype, txt, searchfield, start, page_len, filters):
	require_permission("In Out Gate Pass", "read")
	return search_header_item(doctype, txt, searchfield, start, page_len, filters)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def bagid_query(doctype, txt, searchfield, start, page_len, filters):
	require_permission("In Out Gate Pass", "read")
	return search_bagid(doctype, txt, searchfield, start, page_len, filters)
