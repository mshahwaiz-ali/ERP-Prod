# Copyright (c) 2026, Millitrix and contributors
# Blueprint 4.10 — PAY_SALARYINCREMENT / PAY_SIDETL

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doctype_ids import PAY_SALARY_INCREMENT
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.stock import mark_posted, mark_unposted


def _total_increment(doc) -> float:
	return sum(flt(line.amount) for line in doc.details or [])


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = PAY_SALARY_INCREMENT
	validate_fiscal_period(doc.indate)
	if not doc.details:
		frappe.throw(_("Add at least one increment detail line"))
	total = _total_increment(doc)
	if total <= 0:
		frappe.throw(_("Total increment amount must be positive"))
	if not frappe.db.exists("Employee Setup", doc.empno):
		frappe.throw(_("Employee Setup {0} not found").format(doc.empno))


def on_submit(doc, method=None):
	total = _total_increment(doc)
	current = flt(frappe.db.get_value("Employee Setup", doc.empno, "salary"))
	frappe.db.set_value(
		"Employee Setup",
		doc.empno,
		"salary",
		current + total,
		update_modified=True,
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
	total = _total_increment(doc)
	current = flt(frappe.db.get_value("Employee Setup", doc.empno, "salary"))
	revised = current - total
	if revised < -0.01:
		frappe.throw(
			_("Cannot cancel increment {0}: employee salary would become negative").format(doc.incrid)
		)
	frappe.db.set_value(
		"Employee Setup",
		doc.empno,
		"salary",
		max(revised, 0),
		update_modified=True,
	)
	mark_unposted(doc)
