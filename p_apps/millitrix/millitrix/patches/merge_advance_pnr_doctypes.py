# Copyright (c) 2026, Millitrix and contributors
"""Merge Advance Payment + Advance Receipt into unified Advance PNR DocType."""

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.utils.doctype_ids import ADVANCE_PNR

LEGACY_ADVANCE_DOCTYPES = ("Advance Payment", "Advance Receipt")
FLOW_BY_LEGACY = {"Advance Payment": "Payment", "Advance Receipt": "Receipt"}
DEPRECATED_JSON_FLAGS = {
	"show_name_in_global_search": 0,
	"allow_import": 0,
}


def _copy_row(old_doctype: str, name: str, *, advance_flow: str) -> None:
	if frappe.db.exists(ADVANCE_PNR, name):
		frappe.throw(f"Advance PNR {name} already exists while migrating {old_doctype} {name}")

	doc = frappe.get_doc(old_doctype, name)
	child_rows = frappe.get_all(
		"Payment and Receipt Instrument",
		filters={"parent": name, "parenttype": old_doctype},
		fields=["*"],
	)
	new = frappe.new_doc(ADVANCE_PNR)
	new.update(
		{
			"pnrno": doc.pnrno,
			"advance_flow": advance_flow,
			"location_id": doc.location_id,
			"partyid": doc.partyid,
			"pnrdate": doc.pnrdate,
			"bankaccid": doc.bankaccid,
			"referno": doc.referno,
			"referdate": doc.referdate,
			"pnrmode": doc.pnrmode,
			"amount": doc.amount,
			"narration": doc.narration,
			"doctypeid": doc.doctypeid,
			"posted": doc.posted,
		}
	)
	for row in child_rows:
		row.pop("name", None)
		row.pop("parent", None)
		row.pop("parenttype", None)
		row.pop("parentfield", None)
		new.append("instruments", row)
	new.flags.ignore_permissions = True
	new.flags.ignore_mandatory = True
	new.insert()
	if doc.docstatus == 1:
		frappe.db.set_value(ADVANCE_PNR, new.name, "docstatus", 1)
		frappe.db.set_value(ADVANCE_PNR, new.name, "posted", doc.posted or "Submitted")
	elif doc.docstatus == 2:
		frappe.db.set_value(ADVANCE_PNR, new.name, "docstatus", 2)


def _migrate_legacy_rows() -> int:
	migrated = 0
	for old_doctype, advance_flow in FLOW_BY_LEGACY.items():
		for name in frappe.get_all(old_doctype, pluck="name", order_by="creation asc"):
			_copy_row(old_doctype, name, advance_flow=advance_flow)
			migrated += 1
	return migrated


def _deprecate_legacy_doctypes() -> None:
	base = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"
	for doctype in LEGACY_ADVANCE_DOCTYPES:
		folder = frappe.scrub(doctype)
		jp = base / folder / f"{folder}.json"
		if jp.exists():
			data = json.loads(jp.read_text(encoding="utf-8"))
			data.update(DEPRECATED_JSON_FLAGS)
			jp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
		if frappe.db.exists("DocType", doctype):
			for key, value in DEPRECATED_JSON_FLAGS.items():
				frappe.db.set_value("DocType", doctype, key, value)


def _update_report_refs() -> None:
	base = Path(__file__).resolve().parents[1] / "millitrix_erp" / "report"
	for folder in ("advance_p_register", "advance_r_register"):
		jp = base / folder / f"{folder}.json"
		if not jp.exists():
			continue
		data = json.loads(jp.read_text(encoding="utf-8"))
		data["ref_doctype"] = ADVANCE_PNR
		jp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")


def _ensure_print_formats() -> None:
	from millitrix.utils.print_format_html import PRINT_FORMATS

	for _folder, name, doc_type, html_fn in PRINT_FORMATS:
		if name not in ("Advance Payment Voucher", "Advance Receipt Voucher"):
			continue
		if frappe.db.exists("Print Format", name):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Print Format",
				"name": name,
				"doc_type": doc_type,
				"module": "Millitrix ERP",
				"print_format_type": "Jinja",
				"custom_format": 1,
				"standard": "Yes",
				"html": html_fn(),
			}
		)
		doc.insert(ignore_permissions=True)


def execute() -> None:
	if not frappe.db.exists("DocType", ADVANCE_PNR):
		frappe.reload_doc("millitrix_erp", "doctype", "advance_pnr")
	migrated = _migrate_legacy_rows()
	_deprecate_legacy_doctypes()
	_update_report_refs()
	_ensure_print_formats()
	frappe.clear_cache(doctype="DocType")
	print(f"merged {migrated} advance rows into Advance PNR; deprecated legacy advance DocTypes")
