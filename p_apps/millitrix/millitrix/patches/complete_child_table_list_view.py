# Complete child-table list view metadata for remaining DocTypes.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.patches.apply_ui_field_options import IN_LIST_VIEW, apply as apply_json


def execute() -> None:
	apply_json()
	_sync_list_view_columns()
	frappe.clear_cache(doctype="DocType")


def _sync_list_view_columns() -> None:
	for doctype, fieldnames in IN_LIST_VIEW.items():
		for fieldname in fieldnames:
			frappe.db.set_value(
				"DocField",
				{"parent": doctype, "fieldname": fieldname, "parenttype": "DocType"},
				{"in_list_view": 1, "columns": 1},
				update_modified=False,
			)
	frappe.db.commit()
