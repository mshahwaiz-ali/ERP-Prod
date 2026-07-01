# Resolve GL Opening detail lines from Item / Employee / Party LOV (Oracle GL_Opening.fmb).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _

from millitrix.utils.employee_gl import get_employee_category_accid
from millitrix.utils.mill_setting import get_setting_account


def _account_line(
	accid: str,
	*,
	itemcode: str | None = None,
	partyid: str | None = None,
	empno: str | int | None = None,
) -> dict:
	description = frappe.db.get_value("Chart of Accounting", accid, "description") or ""
	return {
		"accid": accid,
		"account_description": description,
		"itemcode": itemcode,
		"partyid": partyid,
		"empno": str(empno) if empno not in (None, "") else None,
		"debit": 0,
		"credit": 0,
	}


def _resolve_party_posting_account(partyid: str) -> str | None:
	party_name = frappe.db.get_value("Party", partyid, "party_name")
	if not party_name:
		return None

	exact = frappe.db.get_value(
		"Chart of Accounting",
		{"chartlevel": 5, "transflag": "Yes", "description": party_name},
		"name",
	)
	if exact:
		return exact

	candidates = frappe.get_all(
		"Chart of Accounting",
		filters={
			"chartlevel": 5,
			"transflag": "Yes",
			"description": ["like", f"%{party_name}%"],
		},
		fields=["name"],
		limit=2,
	)
	if len(candidates) == 1:
		return candidates[0].name
	return None


def get_opening_lines_for_party(partyid: str) -> list[dict]:
	if not frappe.db.exists("Party", partyid):
		frappe.throw(_("Party {0} not found").format(partyid))

	accid = _resolve_party_posting_account(partyid)
	if not accid:
		party_name = frappe.db.get_value("Party", partyid, "party_name")
		frappe.throw(
			_(
				"No Chart of Accounting Level 5 account found for party {0}. "
				"Create a posting account with Account Name matching the party name."
			).format(party_name or partyid)
		)
	return [_account_line(accid, partyid=partyid)]


def get_opening_lines_for_item(itemcode: str) -> list[dict]:
	if not frappe.db.exists("Item Setup", itemcode):
		frappe.throw(_("Item {0} not found").format(itemcode))

	lines: list[dict] = []
	stockable = (frappe.db.get_value("Item Setup", itemcode, "stockable") or "No") == "Yes"

	if stockable:
		for setting_key in ("Item Stock GL", "Item Opening GL"):
			accid = get_setting_account(setting_key)
			lines.append(_account_line(accid, itemcode=itemcode))
	else:
		accid = get_setting_account("Item Opening GL")
		lines.append(_account_line(accid, itemcode=itemcode))

	return lines


def get_opening_lines_for_employee(empno) -> list[dict]:
	emp_key = str(empno)
	if not frappe.db.exists("Employee Setup", emp_key):
		frappe.throw(_("Employee {0} not found").format(empno))

	lines: list[dict] = []
	category_acc = get_employee_category_accid(empno)
	lines.append(_account_line(category_acc, empno=emp_key))

	return lines


def get_opening_lines(entry_mode: str, entity_id: str) -> list[dict]:
	mode = (entry_mode or "").strip()
	if mode == "Party":
		return get_opening_lines_for_party(entity_id)
	if mode == "Item":
		return get_opening_lines_for_item(entity_id)
	if mode == "Employee":
		return get_opening_lines_for_employee(entity_id)
	frappe.throw(_("Unsupported entry mode: {0}").format(entry_mode))
