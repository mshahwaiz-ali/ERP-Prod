# Copyright (c) 2026, Millitrix and contributors
# Oracle ChartOfAccount.fmb — tabbed level builder API.

from __future__ import annotations

import frappe
from frappe import _

from millitrix.api.permissions import require_permission

COA = "Chart of Accounting"


@frappe.whitelist()
def get_accounts(chartlevel: int, parentid: str | None = None) -> list[dict]:
	require_permission(COA, "read")
	level = int(chartlevel)
	filters: dict = {"chartlevel": level}
	if parentid:
		filters["parentid"] = parentid
	return frappe.get_all(
		COA,
		filters=filters,
		fields=["name", "accid", "description", "nature", "chartlevel", "parentid", "transflag"],
		order_by="accid asc",
	)


@frappe.whitelist()
def get_account(name: str) -> dict:
	require_permission(COA, "read")
	if not frappe.db.exists(COA, name):
		frappe.throw(_("Account {0} not found").format(name))
	return frappe.get_doc(COA, name).as_dict()


@frappe.whitelist()
def save_account(data) -> dict:
	require_permission(COA, "write")
	payload = frappe.parse_json(data) if isinstance(data, str) else dict(data or {})
	name = payload.pop("name", None)
	if name and frappe.db.exists(COA, name):
		doc = frappe.get_doc(COA, name)
		doc.update(payload)
	else:
		doc = frappe.get_doc({"doctype": COA, **payload})
	doc.save()
	if int(doc.chartlevel or 0) < 5 and doc.nature:
		_cascade_nature(doc.name, doc.nature)
	return doc.as_dict()


def _cascade_nature(parent_name: str, nature: str) -> None:
	for child in frappe.get_all(COA, filters={"parentid": parent_name}, pluck="name"):
		frappe.db.set_value(COA, child, "nature", nature, update_modified=False)
		_cascade_nature(child, nature)


@frappe.whitelist()
def delete_account(name: str) -> dict:
	require_permission(COA, "delete")
	if not name or not frappe.db.exists(COA, name):
		frappe.throw(_("Account not found"))
	children = frappe.db.count(COA, {"parentid": name})
	if children:
		frappe.throw(_("Cannot delete account with child accounts"))
	frappe.delete_doc(COA, name, force=1)
	return {"ok": True}
