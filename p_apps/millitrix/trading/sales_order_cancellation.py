# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.field_normalizers import order_status_label
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.order_balance import SIDE_SALES, open_truck_qty_for_order, projected_open_truck_qty
from millitrix.utils.stock import mark_posted, mark_unposted


def _cancel_qty_by_so(doc) -> dict[str, float]:
	totals: dict[str, float] = {}
	for line in doc.details or []:
		if not line.sonumber:
			continue
		totals[line.sonumber] = totals.get(line.sonumber, 0) + flt(line.cancelqty)
	return totals


def _validate_cancellation_lines(doc) -> None:
	if not doc.details:
		frappe.throw(_("Add Sales Order cancellation lines"))

	totals = _cancel_qty_by_so(doc)
	for sonumber, cancel_total in totals.items():
		so = frappe.get_doc("Sales Order", sonumber)
		if so.docstatus != 1:
			frappe.throw(_("Sales Order {0} must be submitted before cancellation").format(sonumber))
		if doc.partyid and so.customerid != doc.partyid:
			frappe.throw(
				_("Sales Order {0} does not belong to party {1}").format(sonumber, doc.partyid)
			)
		open_qty = open_truck_qty_for_order(so, SIDE_SALES)
		if cancel_total > open_qty + 1e-9:
			frappe.throw(
				_("Cancel qty {0} exceeds remaining open qty {1} on Sales Order {2}").format(
					cancel_total, open_qty, sonumber
				)
			)

	for line in doc.details or []:
		if not line.sonumber:
			continue
		cancel_qty = flt(line.cancelqty)
		if cancel_qty <= 0:
			frappe.throw(_("Enter Cancel Qty for Sales Order {0}").format(line.sonumber))

		so = frappe.get_doc("Sales Order", line.sonumber)
		open_qty = open_truck_qty_for_order(so, SIDE_SALES)
		if not flt(line.truckqty):
			line.truckqty = open_qty

		if cancel_qty > flt(line.truckqty) + 1e-9:
			frappe.throw(
				_("Cancel qty cannot exceed Balance Qty on Sales Order {0}").format(line.sonumber)
			)
		if cancel_qty > open_qty + 1e-9:
			frappe.throw(
				_("Cancel qty exceeds remaining open qty {0} on Sales Order {1}").format(
					open_qty, line.sonumber
				)
			)


def validate(doc, method=None):
	check_posted(doc)
	validate_fiscal_period(doc.candate)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows

	strip_blank_child_rows(doc, "details", "SO Cancellation Detail")
	_validate_cancellation_lines(doc)
	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def on_submit(doc, method=None):
	_validate_cancellation_lines(doc)
	for sonumber, cancel_total in _cancel_qty_by_so(doc).items():
		so = frappe.get_doc("Sales Order", sonumber)
		new_cancel = flt(so.truckqtycancel) + cancel_total
		new_status = (
			order_status_label("CO")
			if projected_open_truck_qty(so, SIDE_SALES, cancelled=new_cancel) <= 0
			else so.status
		)
		frappe.db.set_value(
			"Sales Order",
			sonumber,
			{"truckqtycancel": new_cancel, "status": new_status},
			update_modified=False,
		)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)