# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.4 — GPSUBMIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.fiscal import validate_fiscal_period
from millitrix.utils.invoice_fields import mundtype_select_default
from millitrix.utils.naming import sync_gate_pass_gptype
from millitrix.utils.stock import (
	apply_stock_in,
	apply_stock_out,
	bardana_key_from_gate_line,
	check_bag_stock,
	grain_key_from_gate_line,
	is_in_gptype,
	is_out_gptype,
	line_grain_qty,
	mark_posted,
	mark_unposted,
)


def _sync_mundtype_from_item(doc) -> None:
	if not doc.itemcode:
		return
	mundtype = frappe.db.get_value("Item Setup", doc.itemcode, "mundtype")
	doc.mundtype = mundtype or mundtype_select_default()


def _sync_line_rates(doc) -> None:
	if not doc.itemcode or not doc.location_id:
		return
	from millitrix.utils.item_price import get_item_rate

	default_rate = flt(get_item_rate(doc.location_id, doc.itemcode, doc.gpdate, is_purchase=True))
	if not default_rate:
		return
	for line in doc.details or []:
		if not flt(line.rate):
			line.rate = default_rate


def validate(doc, method=None):
	from millitrix.utils.field_normalizers import is_yes

	sync_gate_pass_gptype(doc)
	_sync_mundtype_from_item(doc)
	validate_fiscal_period(doc.gpdate)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows

	strip_blank_child_rows(doc, "details", "Gate Pass Detail")
	if is_yes(doc.posted) and doc.docstatus == 0 and not frappe.flags.get("mill_audit_gate_pass"):
		frappe.throw(_("In Out Gate Pass is already marked posted"))

	if not doc.details:
		frappe.throw(_("Add at least one In Out Gate Pass detail line"))

	from millitrix.utils.gate_pass_calc import recalc_gate_pass_document

	recalc_gate_pass_document(doc)
	_sync_line_rates(doc)

	if not frappe.flags.get("mill_audit_gate_pass"):
		_validate_out_stock(doc)


def _validate_out_stock(doc):
	if not is_out_gptype(doc.gptype):
		return
	for line in doc.details:
		grain_qty = line_grain_qty(line)
		if doc.itemcode and grain_qty > 0:
			key = grain_key_from_gate_line(doc, line)
			from millitrix.utils.reserved_stock import get_reserved_qty
			from millitrix.utils.stock import get_in_store_item_name

			name = get_in_store_item_name(key)
			stock = flt(frappe.db.get_value("Stock In Hand", name, "stock_in_hand")) if name else 0
			reserved = get_reserved_qty(
				key, exclude_doctype="In Out Gate Pass", exclude_name=doc.name if doc.name else None
			)
			if grain_qty > stock - reserved + 1e-9:
				frappe.throw(
					_("Insufficient grain stock for {0}. Available {1}, required {2}").format(
						doc.itemcode, stock - reserved, grain_qty
					)
				)
		if line.bagid and flt(line.bagqty) > 0:
			bkey = bardana_key_from_gate_line(doc, line)
			if bkey:
				check_bag_stock(
					bkey,
					flt(line.bagqty),
					exclude_doctype="In Out Gate Pass",
					exclude_name=doc.name if doc.name else None,
				)


def on_submit(doc, method=None):
	if frappe.flags.get("mill_audit_gate_pass"):
		mark_posted(doc)
		return
	if is_out_gptype(doc.gptype):
		_process_gate_pass(doc, out=True)
	elif is_in_gptype(doc.gptype):
		_process_gate_pass(doc, out=False)
	else:
		frappe.throw(_("Unknown In Out Gate Pass type: {0}").format(doc.gptype))
	mark_posted(doc)


def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _process_gate_pass(doc, *, out: bool):
	movement_date = doc.gpdate
	for line in doc.details:
		grain_qty = line_grain_qty(line)
		if doc.itemcode and grain_qty > 0:
			key = grain_key_from_gate_line(doc, line)
			rate = flt(line.rate)
			if out:
				apply_stock_out(
					key,
					grain_qty,
					movement_date=movement_date,
					check_reserved=False,
				)
			else:
				apply_stock_in(
					key,
					grain_qty,
					rate=rate,
					movement_date=movement_date,
				)

		if line.bagid and flt(line.bagqty) > 0:
			bkey = bardana_key_from_gate_line(doc, line)
			if not bkey:
				continue
			bqty = flt(line.bagqty)
			bw = flt(line.bagweight) or None
			if out:
				apply_stock_out(
					bkey,
					bqty,
					movement_date=movement_date,
					check_reserved=False,
				)
			else:
				apply_stock_in(
					bkey,
					bqty,
					rate=flt(line.bagrate),
					movement_date=movement_date,
					bagweight=bw,
				)
