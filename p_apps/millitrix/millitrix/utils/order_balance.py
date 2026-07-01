# Copyright (c) 2026, Millitrix and contributors
# Blueprint Section 5.6 — PO/SO pending truck balance.

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.invoice_calc import open_truck_qty

SIDE_PURCHASE = "purchase"
SIDE_SALES = "sales"

_ORDER_CONFIG = {
	SIDE_PURCHASE: {
		"order_doctype": "Purchase Order",
		"invoice_doctype": "Purchase Invoice",
		"invoice_detail": "Purchase Invoice Detail",
		"order_link_field": "ponumber",
		"fulfilled_field": "truckreceived",
		"cancel_field": "truckqtycancel",
		"order_qty_field": "truckqty",
		"type_field": "potype",
		"amount_field": "payable",
	},
	SIDE_SALES: {
		"order_doctype": "Sales Order",
		"invoice_doctype": "Sales Invoice",
		"invoice_detail": "Sales Invoice Detail",
		"order_link_field": "sonumber",
		"fulfilled_field": "truckissued",
		"cancel_field": "truckqtycancel",
		"order_qty_field": "truckqty",
		"type_field": "sotype",
		"amount_field": "receivable",
	},
}


def is_sub_order(order_type) -> bool:
	return (str(order_type or "").strip() == "Sub Order")


def unposted_invoice_truck_qty(
	order_name: str,
	side: str,
	*,
	exclude_invoice: str | None = None,
) -> float:
	cfg = _ORDER_CONFIG[side]
	conditions = [
		f"d.{cfg['order_link_field']} = %(order_name)s",
		"parent.docstatus = 0",
	]
	params: dict = {"order_name": order_name}
	if exclude_invoice:
		conditions.append("parent.name != %(exclude_invoice)s")
		params["exclude_invoice"] = exclude_invoice

	count = frappe.db.sql(
		f"""SELECT COUNT(*)
		FROM `tab{cfg['invoice_detail']}` d
		INNER JOIN `tab{cfg['invoice_doctype']}` parent ON parent.name = d.parent
		WHERE {" AND ".join(conditions)}""",
		params,
	)[0][0]
	return flt(count)


def unposted_split_child_truck_qty(
	parent_order_name: str,
	side: str,
	*,
	exclude_order: str | None = None,
) -> float:
	cfg = _ORDER_CONFIG[side]
	conditions = [
		"parentid = %(parent)s",
		f"{cfg['type_field']} = 'Sub Order'",
		"docstatus = 0",
	]
	params: dict = {"parent": parent_order_name}
	if exclude_order:
		conditions.append("name != %(exclude_order)s")
		params["exclude_order"] = exclude_order

	qty = frappe.db.sql(
		f"""SELECT COALESCE(SUM({cfg['order_qty_field']}), 0)
		FROM `tab{cfg['order_doctype']}`
		WHERE {" AND ".join(conditions)}""",
		params,
	)[0][0]
	return flt(qty)


def open_truck_qty_for_order(
	order,
	side: str,
	*,
	exclude_invoice: str | None = None,
	exclude_split_order: str | None = None,
) -> float:
	"""Full client balance including unposted invoices and unposted split child orders."""
	cfg = _ORDER_CONFIG[side]
	if isinstance(order, str):
		order = frappe.get_doc(cfg["order_doctype"], order)

	base = open_truck_qty(
		order.get(cfg["order_qty_field"]),
		order.get(cfg["fulfilled_field"]),
		order.get(cfg["cancel_field"]),
	)
	reserved = unposted_invoice_truck_qty(order.name, side, exclude_invoice=exclude_invoice)
	reserved += unposted_split_child_truck_qty(
		order.name,
		side,
		exclude_order=exclude_split_order,
	)
	return base - reserved


def get_order_for_update(order_name: str, side: str):
	"""Load PO/SO with row lock before fulfilling trucks on submit."""
	cfg = _ORDER_CONFIG[side]
	return frappe.get_doc(cfg["order_doctype"], order_name, for_update=True)


def projected_open_truck_qty(
	order,
	side: str,
	*,
	fulfilled: float | None = None,
	cancelled: float | None = None,
	exclude_invoice: str | None = None,
	exclude_split_order: str | None = None,
) -> float:
	"""Open balance after applying projected fulfilled/cancelled counts."""
	cfg = _ORDER_CONFIG[side]
	if isinstance(order, str):
		order = frappe.get_doc(cfg["order_doctype"], order)

	if fulfilled is None:
		fulfilled = order.get(cfg["fulfilled_field"])
	if cancelled is None:
		cancelled = order.get(cfg["cancel_field"])

	base = open_truck_qty(order.get(cfg["order_qty_field"]), fulfilled, cancelled)
	reserved = unposted_invoice_truck_qty(order.name, side, exclude_invoice=exclude_invoice)
	reserved += unposted_split_child_truck_qty(
		order.name,
		side,
		exclude_order=exclude_split_order,
	)
	return base - reserved


def validate_split_child_order(doc, side: str) -> None:
	cfg = _ORDER_CONFIG[side]
	type_field = cfg["type_field"]
	order_type = doc.get(type_field)

	if is_sub_order(order_type):
		if not doc.parentid:
			frappe.throw(_("Parent Order Number is required for Sub Order"))
		if not frappe.db.exists(cfg["order_doctype"], doc.parentid):
			frappe.throw(_("Parent order {0} not found").format(doc.parentid))
		parent = frappe.get_doc(cfg["order_doctype"], doc.parentid)
		if parent.docstatus != 1:
			frappe.throw(_("Parent order must be submitted before creating a Sub Order"))
		doc.rate = parent.rate
		doc.amount = flt(flt(doc.truckqty) * flt(doc.rate), 2)
		setattr(doc, cfg["amount_field"], doc.amount)
		open_parent = open_truck_qty_for_order(parent, side, exclude_split_order=doc.name)
		if flt(doc.truckqty) > open_parent + 1e-9:
			frappe.throw(
				_("Sub order truck quantity exceeds parent open balance ({0})").format(open_parent)
			)
	elif doc.parentid:
		frappe.throw(_("Parent Order Number is only allowed for Sub Order"))
