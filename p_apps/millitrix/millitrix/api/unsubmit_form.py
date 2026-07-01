# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.finance.unsubmit import SUPPORTED_UNSUBMIT_DOCTYPES, reverse_posted_document
from millitrix.utils.user_permissions import check_unsubmit_permission


@frappe.whitelist()
def get_supported_doctypes() -> list[str]:
	"""DocTypes that can be reversed via Unsubmit (Oracle UnSubmit.fmb)."""
	check_unsubmit_permission()
	return sorted(SUPPORTED_UNSUBMIT_DOCTYPES)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def module_link_query(doctype, txt, searchfield, start, page_len, filters):
	"""Module LOV — Oracle code (moduleid) + description (module name)."""
	check_unsubmit_permission()
	supported = tuple(SUPPORTED_UNSUBMIT_DOCTYPES)
	txt = f"%{txt or ''}%"
	return frappe.db.sql(
		"""
		SELECT
			name,
			CONCAT(moduleid, ' — ', module) AS label
		FROM `tabModule`
		WHERE moduletype = 'F'
			AND doctypeid IN %(supported)s
			AND (
				CAST(moduleid AS CHAR) LIKE %(txt)s
				OR module LIKE %(txt)s
				OR doctypeid LIKE %(txt)s
			)
		ORDER BY moduleid
		LIMIT %(page_len)s OFFSET %(start)s
		""",
		{"supported": supported, "txt": txt, "page_len": page_len, "start": start},
	)


@frappe.whitelist()
def unsubmit_for_edit(doctype: str, name: str) -> dict:
	"""Reverse a submitted document so it can be edited and submitted again."""
	check_unsubmit_permission()
	reverse_posted_document(doctype, name)
	return {"ok": True}


@frappe.whitelist()
def get_document_description(usdoctype: str, documentid: str, target_doctype: str | None = None) -> str:
	"""Oracle UnSubmit.fmb Doc_Desc preview."""
	check_unsubmit_permission()
	from millitrix.finance.unsubmit import resolve_target_doctype
	from millitrix.utils.unsubmit_display import get_unsubmit_document_description

	target = target_doctype
	if not target and usdoctype:
		if frappe.db.exists("DocType", usdoctype):
			target = usdoctype
		else:
			target = frappe.db.get_value("Module", usdoctype, "doctypeid")
	if not target or not documentid:
		return ""
	return get_unsubmit_document_description(target, documentid)
