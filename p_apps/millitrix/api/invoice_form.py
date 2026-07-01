# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json

import frappe

from frappe.utils import flt

from millitrix.api.permissions import require_permission
from millitrix.utils.invoice_calc import recalc_invoice_lines
from millitrix.utils.order_balance import SIDE_PURCHASE, SIDE_SALES, open_truck_qty_for_order
from millitrix.utils.item_price import apply_price_list_to_invoice
from millitrix.utils.trading_reports import get_purchase_order_pending_rows, get_sales_order_pending_rows

_INVOICE_RECALC_DOCTYPES = {
	"Purchase Invoice": True,
	"Purchase Return": True,
	"Sales Invoice": False,
	"Sales Return": False,
}


@frappe.whitelist()
def recalc(doc, is_purchase=1):
	"""Recalculate invoice lines and header totals for live form updates."""
	if isinstance(doc, str):
		doc = json.loads(doc)

	doctype = doc.get("doctype")
	if doctype in _INVOICE_RECALC_DOCTYPES:
		is_purchase = _INVOICE_RECALC_DOCTYPES[doctype]
	else:
		is_purchase = bool(int(is_purchase or 0))
		doctype = "Purchase Invoice" if is_purchase else "Sales Invoice"

	require_permission(doctype, "write")

	invoice = frappe.get_doc(doc)
	if invoice.doctype not in _INVOICE_RECALC_DOCTYPES:
		frappe.throw(frappe._("Recalculation is not supported for {0}").format(invoice.doctype))

	apply_price_list_to_invoice(invoice, is_purchase=bool(is_purchase))
	recalc_invoice_lines(invoice, is_purchase=bool(is_purchase))
	return invoice.as_dict()


def line_brokeramnt_readonly(doc) -> bool:
	from millitrix.utils.invoice_fields import is_yes

	return is_yes(getattr(doc, "brokery_auto_calc", None))


@frappe.whitelist()
def unsubmit_for_edit(doctype, name):
	"""Backward-compatible alias — use millitrix.api.unsubmit_form.unsubmit_for_edit."""
	from millitrix.api.unsubmit_form import unsubmit_for_edit as _unsubmit_for_edit

	return _unsubmit_for_edit(doctype, name)


@frappe.whitelist()
def get_open_truck_qty(order_doctype: str, order_name: str) -> float:
	"""Open truck balance for PO/SO cancellation lines."""
	if order_doctype not in ("Purchase Order", "Sales Order"):
		frappe.throw(frappe._("Only Purchase Order or Sales Order are supported"))
	require_permission(order_doctype, "read")
	side = SIDE_PURCHASE if order_doctype == "Purchase Order" else SIDE_SALES
	return flt(open_truck_qty_for_order(order_name, side))


@frappe.whitelist()
def fetch_open_po_lines(doc):
	"""Return invoice detail rows for open PO trucks matching the header parties."""
	require_permission("Purchase Invoice", "read")
	if isinstance(doc, str):
		doc = json.loads(doc)

	location_id = doc.get("location_id")
	itemcode = doc.get("itemcode")
	brokerid = doc.get("brokerid")
	supplierid = doc.get("supplierid")
	if not (location_id and itemcode and brokerid and supplierid):
		return []

	filters = {
		"location_id": location_id,
		"itemcode": itemcode,
		"brokerid": brokerid,
		"supplierid": supplierid,
	}
	if doc.get("sub_partyid"):
		filters["sub_partyid"] = doc["sub_partyid"]

	existing_pos = {row.get("ponumber") for row in doc.get("details") or [] if row.get("ponumber")}
	lines = []
	line_no = 1
	for po in get_purchase_order_pending_rows(filters):
		if po.name in existing_pos:
			continue
		open_trucks = int(open_truck_qty_for_order(po.name, SIDE_PURCHASE))
		if open_trucks <= 0:
			continue
		per_truck_weight = flt(po.weight) / flt(po.truckqty) if flt(po.truckqty) else 0
		for _ in range(open_trucks):
			lines.append(
				{
					"pidetlno": line_no,
					"ponumber": po.name,
					"rate": flt(po.rate),
					"truckqty": per_truck_weight,
				}
			)
			line_no += 1
	return lines


@frappe.whitelist()
def fetch_open_so_lines(doc):
	"""Return invoice detail rows for open SO trucks matching the header parties."""
	require_permission("Sales Invoice", "read")
	if isinstance(doc, str):
		doc = json.loads(doc)

	location_id = doc.get("location_id")
	itemcode = doc.get("itemcode")
	brokerid = doc.get("brokerid")
	customerid = doc.get("customerid")
	if not (location_id and itemcode and brokerid and customerid):
		return []

	filters = {
		"location_id": location_id,
		"itemcode": itemcode,
		"brokerid": brokerid,
		"customerid": customerid,
	}
	if doc.get("sub_partyid"):
		filters["sub_partyid"] = doc["sub_partyid"]

	existing_sos = {row.get("sonumber") for row in doc.get("details") or [] if row.get("sonumber")}
	lines = []
	line_no = 1
	for so in get_sales_order_pending_rows(filters):
		if so.name in existing_sos:
			continue
		open_trucks = int(open_truck_qty_for_order(so.name, SIDE_SALES))
		if open_trucks <= 0:
			continue
		per_truck_weight = flt(so.weight) / flt(so.truckqty) if flt(so.truckqty) else 0
		for _ in range(open_trucks):
			lines.append(
				{
					"sidetlno": line_no,
					"sonumber": so.name,
					"rate": flt(so.rate),
					"truckqty": per_truck_weight,
				}
			)
			line_no += 1
	return lines
