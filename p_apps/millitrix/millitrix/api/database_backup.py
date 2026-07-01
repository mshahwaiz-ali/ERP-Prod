# Copyright (c) 2026, Millitrix and contributors
# Oracle BACKUP.fmb — site database backup (exp.exe equivalent).

from __future__ import annotations

import os

import frappe
from frappe import _
from frappe.utils import cint, now_datetime


def _require_backup_permission() -> None:
	if "System Manager" in frappe.get_roles() or "Millitrix ERP Manager" in frappe.get_roles():
		return
	frappe.throw(_("Not permitted to run database backup"), frappe.PermissionError)


@frappe.whitelist()
def run_database_backup(*, include_files: int = 0) -> dict:
	"""Take a Frappe site backup and return the generated file paths."""
	_require_backup_permission()

	from frappe.utils.backups import scheduled_backup

	odb = scheduled_backup(ignore_files=not cint(include_files), force=True, verbose=False)
	db_path = odb.backup_path_db
	if not db_path or not os.path.isfile(db_path):
		frappe.throw(_("Database backup failed — no dump file was created"))

	return {
		"database": db_path,
		"database_name": os.path.basename(db_path),
		"backup_time": now_datetime(),
		"include_files": cint(include_files),
	}


@frappe.whitelist()
def list_recent_backups(limit: int = 10) -> list[dict]:
	"""List recent backup files from the site private/backups folder."""
	_require_backup_permission()

	from frappe.utils.backups import get_backup_path

	backup_dir = get_backup_path()
	if not os.path.isdir(backup_dir):
		return []

	rows: list[dict] = []
	for name in sorted(os.listdir(backup_dir), reverse=True):
		path = os.path.join(backup_dir, name)
		if not os.path.isfile(path):
			continue
		stat = os.stat(path)
		rows.append(
			{
				"name": name,
				"size": stat.st_size,
				"modified": stat.st_mtime,
			}
		)
		if len(rows) >= cint(limit):
			break
	return rows
