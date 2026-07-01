# Copyright (c) 2026, Millitrix and contributors
# Oracle TRANSACTION_SETUP → category default account on CNB / expense lines.

from __future__ import annotations

import frappe
from frappe import _


def get_transaction_accid(trans_id) -> str:
	key = str(trans_id)
	if not frappe.db.exists("Transaction List", key):
		frappe.throw(_("Transaction {0} not found").format(trans_id))
	tcat_id = frappe.db.get_value("Transaction List", key, "tcat_id")
	if not tcat_id:
		frappe.throw(_("Transaction {0} has no category").format(trans_id))
	accid = frappe.db.get_value("Transaction Category", str(tcat_id), "accid")
	if not accid:
		frappe.throw(_("Transaction Category {0} has no GL account").format(tcat_id))
	return accid
