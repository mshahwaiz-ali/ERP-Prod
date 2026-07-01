# Sync Print Format records + fixture JSON from print_format_html.py
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe


def set_default_print_format(doctype, print_format):
        """Assign default print format without importing set_default_print_formats.py."""
        if not frappe.db.exists("Print Format", print_format):
                return
        if not frappe.db.exists("DocType", doctype):
                return

        frappe.db.set_value(
                "DocType", doctype, "default_print_format", None, update_modified=False
        )

        filters = {
                "doc_type": doctype,
                "doctype_or_field": "DocType",
                "property": "default_print_format",
        }
        existing = frappe.db.get_value("Property Setter", filters, "name")
        if existing:
                frappe.db.set_value(
                        "Property Setter", existing, "value", print_format, update_modified=False
                )
        else:
                frappe.make_property_setter(
                        {
                                "doctype_or_field": "DocType",
                                "doctype": doctype,
                                "property": "default_print_format",
                                "value": print_format,
                                "property_type": "Data",
                        },
                        is_system_generated=True,
                        validate_fields_for_doctype=False,
                )

        frappe.clear_cache(doctype=doctype)




def _fixture_base() -> Path:
	return Path(frappe.get_app_path("millitrix")) / "millitrix_erp" / "print_format"


def _upsert_print_format(name: str, doc_type: str, html: str) -> None:
	if not frappe.db.exists("DocType", doc_type):
		return
	if frappe.db.exists("Print Format", name):
		frappe.db.set_value(
			"Print Format",
			name,
			{
				"doc_type": doc_type,
				"html": html,
				"disabled": 0,
				"print_format_type": "Jinja",
				"custom_format": 1,
				"standard": "Yes",
			},
			update_modified=True,
		)
		return
	doc = frappe.get_doc(
		{
			"doctype": "Print Format",
			"name": name,
			"doc_type": doc_type,
			"module": "Millitrix ERP",
			"print_format_type": "Jinja",
			"custom_format": 1,
			"standard": "Yes",
			"html": html,
		}
	)
	doc.insert(ignore_permissions=True)


def _write_fixture(folder: str, name: str, doc_type: str, html: str) -> None:
	base = _fixture_base() / folder
	base.mkdir(parents=True, exist_ok=True)
	path = base / f"{folder}.json"
	payload = {
		"creation": "2026-06-14 22:00:00.000000",
		"custom_format": 1,
		"disabled": 0,
		"doc_type": doc_type,
		"doctype": "Print Format",
		"html": html,
		"idx": 0,
		"modified": "2026-06-18 12:00:00.000000",
		"modified_by": "Administrator",
		"module": "Millitrix ERP",
		"name": name,
		"owner": "Administrator",
		"print_format_for": "DocType",
		"print_format_type": "Jinja",
		"standard": "Yes",
	}
	path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")


def _default_mapping() -> dict[str, str]:
	return {
		"Purchase Invoice": "Purchase Invoice",
		"Sales Invoice": "Sales Invoice",
		"In Out Gate Pass": "In Out Gate Pass",
		"Purchase Order": "Purchase Order",
		"Sales Order": "Sales Order",
		"Voucher Transaction": "Voucher Transaction",
		"PaySlip": "PaySlip",
		"Purchase Return": "Purchase Return",
		"Sales Return": "Sales Return",
		"Stock Transfer Note": "Stock Transfer Note",
		"Party Gross Margin": "Party Gross Margin",
		"Employee Payment Voucher": "Employee Payment Voucher",
		"Employee Receipt Voucher": "Employee Receipt Voucher",
		"Purchase Invoice Payment": "Payment and Receipt Voucher",
		"Sales Invoice Receipt": "Payment and Receipt Voucher",
		"Broker Invoice Payment": "Payment and Receipt Voucher",
		"Advance Payment": "Advance Payment",
		"Advance Receipt": "Advance Receipt",
		"Advance PNR": "Advance PNR",
		"Payable Discount Note": "Payment and Receipt Voucher",
		"Receivable Discount Note": "Payment and Receipt Voucher",
		"Payment Voucher": "Cash and Bank Voucher",
		"Receipt Voucher": "Cash and Bank Voucher",
		"Expense Voucher": "Expense Voucher",
		"Party Payment Voucher": "Party Payment Voucher",
		"Party Receipt Voucher": "Party Receipt Voucher",
		"Paid Advance Adjustment": "Advance Adjustment",
		"Received Advance Adjustment": "Advance Adjustment",
		"Payment and Receipt Voucher": "Payment and Receipt Voucher",
		"Cash and Bank Voucher": "Cash and Bank Voucher",
		"Advance Adjustment": "Advance Adjustment",
		"Opening Stock": "Opening Stock",
		"Closing Stock": "Closing Stock",
		"Stock Adjustment": "Stock Adjustment",
		"Purchase Return Other Bill": "Purchase Return Other Bill",
		"Sales Return Other Bill": "Sales Return Other Bill",
		"Purchase Other Bill": "Purchase Other Bill",
		"Sales Other Bill": "Sales Other Bill",
		"Payment By Hawala": "Payment By Hawala",
		"PO Cancellation": "PO Cancellation",
		"SO Cancellation": "SO Cancellation",
		"Crashing Refine": "Crashing Refine",
	}


def execute() -> None:
	from millitrix.utils.print_format_html import PRINT_FORMATS

	synced = 0
	for folder, name, doc_type, html_fn in PRINT_FORMATS:
		html = html_fn()
		if "Millitrix >" in html or '"Millitrix' in html:
			frappe.throw(f"Corrupted HTML in print format {name!r} — fix print_format_html.py first")
		_upsert_print_format(name, doc_type, html)
		_write_fixture(folder, name, doc_type, html)
		synced += 1

	for doctype, print_format in _default_mapping().items():
		set_default_print_format(doctype, print_format)

	# frappe.db.commit()  # DISABLED SAFE MODE
	print(f"synced {synced} print formats from print_format_html.py")
