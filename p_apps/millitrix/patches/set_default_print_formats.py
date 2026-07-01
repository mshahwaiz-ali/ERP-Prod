# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.patches.sync_print_formats_from_source import _default_mapping


def set_default_print_format(doctype: str, print_format: str) -> None:
	"""Assign default print format via Property Setter (standard DocTypes)."""
	if not frappe.db.exists("Print Format", print_format):
		return
	if not frappe.db.exists("DocType", doctype):
		return

	# Direct column values break DocType save validation on standard forms.
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


def execute():
	"""Set default print format on key DocTypes (split + legacy finance)."""
	for doctype, print_format in _default_mapping().items():
		set_default_print_format(doctype, print_format)

	# frappe.db.commit()  # DISABLED SAFE MODE
