# Human-readable description for Un-Submit Documents list (Oracle UnSubmit.fmb Doc_Desc).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.utils.document_display import resolve_document_name, resolve_document_title


def get_unsubmit_document_description(doctype: str, document_id: str) -> str:
	"""Build a short description like Oracle WHEN-VALIDATE DocumentId."""
	if not doctype or not document_id:
		return ""

	name = resolve_document_name(doctype, document_id)
	if not name:
		return ""

	doc = frappe.get_doc(doctype, name)
	parts: list[str] = []

	party = doc.get("partyid") or doc.get("supplierid") or doc.get("customerid")
	if party:
		parts.append(frappe.db.get_value("Party", party, "party_name") or party)

	item = doc.get("itemcode") or doc.get("primary_item")
	if item:
		parts.append(frappe.db.get_value("Item Setup", item, "itemname") or item)

	if doctype == "Stock Transfer Note":
		store = doc.get("fromstoreid")
		if store:
			store_name = frappe.db.get_value("Store Setup", store, "store_name") or store
			parts.insert(0, store_name)

	if parts:
		return ", ".join(parts[:3])

	title = resolve_document_title(doc)
	return title or str(document_id)
