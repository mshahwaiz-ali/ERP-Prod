# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _


def get_party_accid(partyid: str) -> str:
	if not partyid:
		frappe.throw(_("Party is required for GL posting"))
	pcat_id = frappe.db.get_value("Party", partyid, "pcat_id")
	if not pcat_id:
		frappe.throw(_("Party {0} has no category").format(partyid))
	accid = frappe.db.get_value("Party Category", pcat_id, "accid")
	if not accid:
		frappe.throw(_("Party Category {0} has no GL account").format(pcat_id))
	return accid
