# Copyright (c) 2026, Millitrix and contributors
# Show human titles in links/hover — not Oracle ids or narration.

from __future__ import annotations

import frappe

from millitrix.utils.naming import DOCTYPE_PREFIX

# Masters: show descriptive name only (hide numeric partyid / itemcode in hover).
MASTER_TITLE: dict[str, str] = {
	"Party": "party_name",
	"Item Setup": "itemname",
	"Employee Setup": "ename",
	"Store Setup": "store_name",
	"Chart of Accounting": "description",
	"Bank": "bankname",
	"Location": "description",
	"City Setup": "cityname",
	"Voucher Type": "description",
	"Store Types": "description",
	"Party Category": "description",
	"Employee Category": "description",
	"Transaction List": "description",
	"Transaction Category": "description",
	"Mill Information": "description",
	"Module": "module",
	"Menu": "menu",
	"Designation": "description",
	"Departments": "description",
	"Item Class": "description",
	"Other Contact Setup": "name",
	"Bank Branch": "branchname",
	"Document Type": "module",
	"GL Statements": "description",
	"User Rights": "username",
}

_patched = False


def id_field_for(doctype: str) -> str | None:
	autoname = frappe.get_meta(doctype).autoname or ""
	if autoname.startswith("field:"):
		return autoname.split(":", 1)[1]
	return None


def resolve_document_name(doctype: str, document_id) -> str | None:
	"""Map prefixed display id (e.g. PI-2606-001) to Frappe document name."""
	if document_id in (None, ""):
		return None
	key = str(document_id).strip()
	if frappe.db.exists(doctype, key):
		return key
	id_field = id_field_for(doctype)
	if not id_field:
		return None
	return frappe.db.get_value(doctype, {id_field: key}, "name")


def resolve_document_title(doc) -> str | None:
	if doc.doctype in MASTER_TITLE:
		field = MASTER_TITLE[doc.doctype]
		value = doc.get(field)
		return str(value).strip() if value else None

	if doc.doctype in DOCTYPE_PREFIX or doc.doctype in (
		"Advance Payment",
		"Advance Receipt",
	):
		id_field = id_field_for(doc.doctype)
		if id_field and doc.get(id_field):
			return str(doc.get(id_field))
		return None

	id_field = id_field_for(doc.doctype)
	if id_field and doc.get(id_field):
		return str(doc.get(id_field))
	return None


def install_title_patch() -> None:
	global _patched
	if _patched:
		return

	from frappe.model.document import Document

	_original = Document.get_title

	def get_title(self):
		custom = resolve_document_title(self)
		if custom:
			return custom
		return _original(self)

	Document.get_title = get_title
	_patched = True
