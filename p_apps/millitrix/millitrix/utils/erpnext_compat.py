# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

MILL_TRADING_DOCTYPES = frozenset(
	{
		"Purchase Order",
		"PO Cancellation",
		"Purchase Invoice",
		"Purchase Return",
		"Purchase Other Bill",
		"Sales Order",
		"SO Cancellation",
		"Sales Invoice",
		"Sales Return",
		"Sales Other Bill",
		"In Out Gate Pass",
		"Voucher Transaction",
		"Payment and Receipt Voucher",
		"Cash and Bank Voucher",
		"Employee Payment Voucher",
		"Employee Receipt Voucher",
		"Closing and Adjustment Entries",
		"Accounts Opening",
		"Un-Submit Documents",
		"Crashing Refine",
		"PaySlip",
	}
)


def get_session_location():
	"""Resolve default location from the logged-in user's Mill scope."""
	from millitrix.utils.user_permissions import (
		bypasses_mill_permissions,
		get_mill_user,
		get_user_locations,
	)

	if bypasses_mill_permissions():
		locations = frappe.get_all("Location", pluck="name", limit=1, order_by="name asc")
		return locations[0] if locations else None

	mill_user = get_mill_user()
	if not mill_user:
		return None
	if mill_user.location_id:
		return mill_user.location_id
	locations = get_user_locations(mill_user)
	return locations[0] if locations else None


def set_session_location(doc, method=None):
	"""Default location_id from user session when the client form hides Location."""
	from millitrix.utils.blueprint_form_rules import location_ui_hidden

	if not location_ui_hidden(doc.doctype):
		return
	if not frappe.get_meta(doc.doctype).has_field("location_id") or doc.get("location_id"):
		return

	location = get_session_location()
	if location:
		doc.location_id = location


def set_posting_date(doc, method=None):
	if doc.doctype not in MILL_TRADING_DOCTYPES:
		return
	date = (
		doc.get("invdate")
		or doc.get("podate")
		or doc.get("sodate")
		or doc.get("billdate")
		or doc.get("retdate")
		or doc.get("candate")
		or doc.get("gpdate")
		or doc.get("vouchdate")
		or doc.get("pnrdate")
		or doc.get("opening_date")
		or doc.get("usdate")
		or doc.get("crdate")
		or doc.get("pdate")
		or doc.get("paymonth")
	)
	if date:
		doc.set("posting_date", date)
