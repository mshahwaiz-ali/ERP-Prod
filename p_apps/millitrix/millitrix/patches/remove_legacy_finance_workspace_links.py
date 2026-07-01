# Copyright (c) 2026, Millitrix and contributors
"""Remove deprecated merged finance DocTypes from workspace navigation."""

from __future__ import annotations

import json
from pathlib import Path

LEGACY_LINKS = {
	"Payment and Receipt Voucher",
	"Cash and Bank Voucher",
	"Advance Adjustment",
	"Advance PNR",
}


def _scrub_workspace(path: Path) -> bool:
	if not path.exists():
		return False
	data = json.loads(path.read_text(encoding="utf-8"))
	links = data.get("links") or []
	new_links = [link for link in links if link.get("link_to") not in LEGACY_LINKS]
	if len(new_links) == len(links):
		return False
	data["links"] = new_links
	path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
	return True


def execute() -> None:
	base = Path(__file__).resolve().parents[1] / "millitrix_erp" / "workspace"
	count = 0
	for ws in base.iterdir():
		if ws.is_dir() and _scrub_workspace(ws / f"{ws.name}.json"):
			count += 1
	print(f"remove_legacy_finance_workspace_links: updated {count} workspaces")
