# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.field_normalizers import order_status_label
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.order_balance import SIDE_PURCHASE, open_truck_qty_for_order, projected_open_truck_qty
from millitrix.utils.stock import mark_posted, mark_unposted


def _cancel_qty_by_po(doc) -> dict[str, float]:
	totals: dict[str, float] = {}
	for line in doc.details or []:
		if not line.ponumber:
			continue
		totals[line.ponumber] = totals.get(line.ponumber, 0) + flt(line.cancelqty)
	return totals


def _validate_cancellation_lines(doc) -> None:
	if not doc.details:
		frappe.throw(_("Add PO cancellation lines"))

	totals = _cancel_qty_by_po(doc)
	for ponumber, cancel_total in totals.items():
		po = frappe.get_doc("Purchase Order", ponumber)
		if po.docstatus != 1:
			frappe.throw(_("PO {0} must be submitted before cancellation").format(ponumber))
		if doc.partyid and po.supplierid != doc.partyid:
			frappe.throw(
				_("PO {0} does not belong to party {1}").format(ponumber, doc.partyid)
			)
		open_qty = open_truck_qty_for_order(po, SIDE_PURCHASE)
		if cancel_total > open_qty + 1e-9:
			frappe.throw(
				_("Cancel qty {0} exceeds remaining open qty {1} on PO {2}").format(
					cancel_total, open_qty, ponumber
				)
			)

	for line in doc.details or []:
		if not line.ponumber:
			continue
		cancel_qty = flt(line.cancelqty)
		if cancel_qty <= 0:
			frappe.throw(_("Enter Cancel Qty for PO {0}").format(line.ponumber))

		po = frappe.get_doc("Purchase Order", line.ponumber)
		open_qty = open_truck_qty_for_order(po, SIDE_PURCHASE)
		if not flt(line.truckqty):
			line.truckqty = open_qty

		if cancel_qty > flt(line.truckqty) + 1e-9:
			frappe.throw(
				_("Cancel qty cannot exceed Balance Qty on PO {0}").format(line.ponumber)
			)
		if cancel_qty > open_qty + 1e-9:
			frappe.throw(
				_("Cancel qty exceeds remaining open qty {0} on PO {1}").format(open_qty, line.ponumber)
			)


def validate(doc, method=None):
	check_posted(doc)
	validate_fiscal_period(doc.candate)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows

	strip_blank_child_rows(doc, "details", "PO Cancellation Detail")
	_validate_cancellation_lines(doc)
	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def on_submit(doc, method=None):
	_validate_cancellation_lines(doc)
	for ponumber, cancel_total in _cancel_qty_by_po(doc).items():
		po = frappe.get_doc("Purchase Order", ponumber)
		new_cancel = flt(po.truckqtycancel) + cancel_total
		new_status = (
			order_status_label("CO")
			if projected_open_truck_qty(po, SIDE_PURCHASE, cancelled=new_cancel) <= 0
			else po.status
		)
		frappe.db.set_value(
			"Purchase Order",
			ponumber,
			{"truckqtycancel": new_cancel, "status": new_status},
			update_modified=False,
		)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)