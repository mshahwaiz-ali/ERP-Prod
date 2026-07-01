# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from frappe import _

from millitrix.api.permissions import require_permission
from millitrix.utils.crash_refine_form import (
	get_bagdust_defaults,
	get_input_line_defaults,
	get_output_line_defaults,
	search_crbagid,
	search_critem,
	search_proditem,
)
from millitrix.utils.erpnext_compat import get_session_location


def _resolve_location(location_id: str | None) -> str:
	location_id = (location_id or "").strip()
	if location_id:
		return location_id
	location_id = (get_session_location() or "").strip()
	if location_id:
		return location_id
	location_id = frappe.db.get_single_value("GL Parameter", "location_id") or ""
	if location_id:
		return location_id
	frappe.throw(_("Location is required — set Mill or GL Parameter location"))


@frappe.whitelist()
def fetch_input_defaults(
	storeid: str,
	location_id: str | None = None,
	critem: str | None = None,
	crbagid: str | None = None,
	crdate: str | None = None,
):
	require_permission("Crashing Refine", "read")
	if not storeid:
		frappe.throw(frappe._("Store is required"))
	location_id = _resolve_location(location_id)
	return get_input_line_defaults(
		location_id=location_id,
		storeid=storeid,
		critem=critem or None,
		crbagid=crbagid or None,
		crdate=crdate or None,
	)


@frappe.whitelist()
def fetch_output_defaults(
	proditem: str,
	location_id: str | None = None,
	crdate: str | None = None,
):
	require_permission("Crashing Refine", "read")
	if not proditem:
		frappe.throw(frappe._("Item is required"))
	location_id = _resolve_location(location_id)
	return get_output_line_defaults(
		location_id=location_id,
		proditem=proditem,
		crdate=crdate or None,
	)


@frappe.whitelist()
def fetch_bagdust_defaults(
	bagdust: float = 0,
	location_id: str | None = None,
	crdate: str | None = None,
):
	require_permission("Crashing Refine", "read")
	location_id = _resolve_location(location_id)
	return get_bagdust_defaults(location_id=location_id, bagdust=bagdust, crdate=crdate or None)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def critem_query(doctype, txt, searchfield, start, page_len, filters):
	require_permission("Crashing Refine", "read")
	return search_critem(doctype, txt, searchfield, start, page_len, filters)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def crbagid_query(doctype, txt, searchfield, start, page_len, filters):
	require_permission("Crashing Refine", "read")
	return search_crbagid(doctype, txt, searchfield, start, page_len, filters)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def proditem_query(doctype, txt, searchfield, start, page_len, filters):
	require_permission("Crashing Refine", "read")
	return search_proditem(doctype, txt, searchfield, start, page_len, filters)


@frappe.whitelist()
def recalc(doc):
	"""Recalculate crashing refine lines for live form / before_save sync."""
	import json

	from millitrix.utils.crash_refine_form import recalc_document_lines

	require_permission("Crashing Refine", "read")
	if isinstance(doc, str):
		doc = json.loads(doc)
	cr_doc = frappe.get_doc(doc)
	recalc_document_lines(cr_doc)
	return cr_doc.as_dict()
