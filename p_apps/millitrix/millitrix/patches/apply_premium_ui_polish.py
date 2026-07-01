# Sprint P1+P2 UI polish — field removal, grid columns, parent lists.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.patches.apply_ui_field_options import apply as apply_ui_json
from millitrix.patches.complete_child_table_list_view import _sync_list_view_columns
from millitrix.patches.compact_transaction_forms import apply_json as compact_forms_json
from millitrix.patches.compact_transaction_forms import _sync_db as sync_compact_forms_db
from millitrix.patches.configure_parent_list_views import apply_json as apply_parent_lists
from millitrix.patches.configure_parent_list_views import _sync_db as sync_parent_lists_db
from millitrix.patches.remove_redundant_fetch_fields import _sync_db_removals
from millitrix.patches.remove_redundant_fetch_fields import apply_json as remove_fetch_json


def execute() -> None:
	removed = remove_fetch_json()
	if removed:
		_sync_db_removals(removed)
	apply_ui_json()
	_sync_list_view_columns()
	apply_parent_lists()
	sync_parent_lists_db()
	compact_forms_json()
	sync_compact_forms_db()
	frappe.clear_cache(doctype="DocType")
