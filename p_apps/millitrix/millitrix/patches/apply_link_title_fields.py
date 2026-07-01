# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from pathlib import Path

from millitrix.utils.link_title_fields import apply_all


def execute():
	root = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"
	apply_all(root)
