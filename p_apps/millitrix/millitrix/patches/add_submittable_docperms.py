# Copyright (c) 2026, Millitrix and contributors
"""Add submit/cancel to standard DocPerm on all submittable Millitrix DocTypes."""

from __future__ import annotations

import json
from pathlib import Path


def execute() -> None:
	base = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"
	updated = 0
	for folder in sorted(base.iterdir()):
		if not folder.is_dir():
			continue
		jp = folder / f"{folder.name}.json"
		if not jp.exists():
			continue
		data = json.loads(jp.read_text(encoding="utf-8"))
		if not data.get("is_submittable"):
			continue
		perms = data.get("permissions") or []
		changed = False
		for perm in perms:
			if perm.get("submit") != 1:
				perm["submit"] = 1
				changed = True
			if perm.get("cancel") != 1:
				perm["cancel"] = 1
				changed = True
		if changed:
			jp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			updated += 1
	print(f"add_submittable_docperms: updated {updated} doctypes")
