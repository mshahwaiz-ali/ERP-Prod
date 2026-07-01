# Copyright (c) 2026, Millitrix and contributors
# Oracle ChartOfAccount / REP_GL_HEADS — hierarchical accid (101, 201, 30101, …).

from __future__ import annotations

import frappe
from frappe import _


def assign_coa_accid(doc) -> None:
	if doc.get("accid"):
		return
	level = int(doc.chartlevel or 0)
	if level < 1 or level > 5:
		frappe.throw(_("Chart Level must be between 1 and 5"))
	doc.accid = _next_coa_accid(level)


def _next_coa_accid(chartlevel: int) -> int:
	"""Oracle PRE-INSERT: level digit + padded sequence within level."""
	level = int(chartlevel)
	pad = 1 if level == 1 else 2
	rows = frappe.db.sql(
		"SELECT accid FROM `tabChart of Accounting` WHERE chartlevel = %s",
		level,
	)
	max_n = 0
	prefix = str(level)
	for (raw,) in rows:
		val = str(raw).strip()
		if not val.startswith(prefix):
			continue
		suffix = val[len(prefix) :]
		try:
			max_n = max(max_n, int(suffix))
		except ValueError:
			continue
	return int(f"{prefix}{max_n + 1:0{pad}d}")
