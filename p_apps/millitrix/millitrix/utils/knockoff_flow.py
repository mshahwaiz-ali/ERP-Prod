# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _


_RECEIPT_PCAT_IDS = frozenset({13})
_PAYMENT_PCAT_IDS = frozenset({11, 12})


def resolve_knockoff_flow(partyid: str) -> str:
	"""Infer payment vs receipt knockoff flow from party category."""
	if not partyid:
		frappe.throw(_("Party is required"))
	pcat_id = frappe.db.get_value("Party", partyid, "pcat_id")
	if not pcat_id:
		frappe.throw(_("Party {0} has no category").format(partyid))
	pcat_int = int(pcat_id)
	if pcat_int in _RECEIPT_PCAT_IDS:
		return "receipt"
	if pcat_int in _PAYMENT_PCAT_IDS:
		return "payment"

	description = (frappe.db.get_value("Party Category", pcat_id, "description") or "").lower()
	if "customer" in description or "sub sales" in description:
		return "receipt"
	return "payment"
