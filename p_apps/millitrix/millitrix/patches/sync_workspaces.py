# Copyright (c) 2026, Millitrix and contributors
"""Regenerate workspace JSON from workspace_layout and import into the site database."""

from __future__ import annotations

import frappe
from frappe.modules.import_file import import_file_by_path

from millitrix.patches.fix_workspace_titles import execute as fix_workspace_titles
from millitrix.utils.workspace_layout import WORKSPACE_ROOT, write_all


def execute() -> None:
	from millitrix.patches.fix_report_module_paths import execute as fix_reports

	fix_reports()
	write_all()
	fix_workspace_titles()

	for folder in sorted(WORKSPACE_ROOT.iterdir()):
		if not folder.is_dir():
			continue
		for json_path in sorted(folder.glob("*.json")):
			import_file_by_path(str(json_path), force=True, reset_permissions=True)
			print(f"synced workspace: {json_path.stem}")

	# import_file can remove module JSON from disk — restore from layout source.
	write_all()

	frappe.clear_cache()
	print("Millitrix workspaces synced to database.")
