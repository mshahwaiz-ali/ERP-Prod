# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _

from millitrix.api.permissions import require_permission
from millitrix.utils.advance_pnr import get_outstanding_advance_pnr
from millitrix.utils.erpnext_compat import get_session_location
from millitrix.utils.knockoff_docs import get_outstanding_broker_documents, get_outstanding_documents
from millitrix.utils.knockoff_flow import resolve_knockoff_flow


def _resolve_location(location_id: str | None) -> str:
	location_id = (location_id or "").strip()
	if location_id:
		return location_id
	location_id = get_session_location()
	if not location_id:
		frappe.throw(_("Location is required"))
	return location_id


@frappe.whitelist()
def get_documents(partyid: str, location_id: str, flow: str, as_of_date: str | None = None):
	"""Return outstanding invoices for knockoff child tables (PNR/CNB/adjustment)."""
	require_permission("Party", "read")
	if not partyid:
		frappe.throw(_("Party is required"))
	location_id = _resolve_location(location_id)
	if not flow:
		frappe.throw(_("Flow is required (payment or receipt)"))
	return get_outstanding_documents(partyid, location_id, flow, as_of_date=as_of_date)


@frappe.whitelist()
def get_broker_documents(brokerid: str, location_id: str, as_of_date: str | None = None):
	"""Return outstanding broker commission invoices for Broker Invoice Payment."""
	require_permission("Broker Invoice Payment", "read")
	if not brokerid:
		frappe.throw(_("Broker is required"))
	location_id = _resolve_location(location_id)
	return get_outstanding_broker_documents(brokerid, location_id, as_of_date=as_of_date)


@frappe.whitelist()
def resolve_flow(partyid: str):
	"""Return payment or receipt based on party category."""
	require_permission("Party", "read")
	return resolve_knockoff_flow(partyid)


@frappe.whitelist()
def get_advance_pnr_lines(partyid: str, location_id: str, as_of_date: str | None = None):
	"""Return outstanding advance PNR rows for advance adjustment."""
	if not (
		frappe.has_permission("Paid Advance Adjustment", "read")
		or frappe.has_permission("Received Advance Adjustment", "read")
	):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if not partyid:
		frappe.throw(_("Party is required"))
	location_id = _resolve_location(location_id)
	return get_outstanding_advance_pnr(partyid, location_id, as_of_date=as_of_date)


_PNR_INVOICE_FLOWS = {
	"Purchase Invoice Payment": "payment",
	"Sales Invoice Receipt": "receipt",
	"Broker Invoice Payment": "payment",
}


@frappe.whitelist()
def get_pnr_accounting_lines(doctype: str, name: str, flow: str | None = None):
	"""Return accounting lines for PNR invoice forms (preview or posted)."""
	if doctype not in _PNR_INVOICE_FLOWS:
		frappe.throw(_("Accounting is not supported for {0}").format(doctype))
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	resolved_flow = (flow or _PNR_INVOICE_FLOWS[doctype]).lower()
	if doc.docstatus == 1:
		from millitrix.finance.pnr_invoice_common import get_posted_pnr_accounting_lines

		return get_posted_pnr_accounting_lines(doc)
	from millitrix.finance.pnr_invoice_common import preview_pnr_invoice_accounting_lines

	return preview_pnr_invoice_accounting_lines(doc, flow=resolved_flow)


_CNB_ACCOUNTING_DOCTYPES = {
	"Employee Payment Voucher": "empvno",
	"Employee Receipt Voucher": "empvno",
	"Expense Voucher": "cnbvno",
	"Payment Voucher": "cnbvno",
	"Receipt Voucher": "cnbvno",
}


@frappe.whitelist()
def get_cnb_accounting_lines(doctype: str, name: str):
	"""Return accounting lines for CNB-style vouchers (preview or posted)."""
	if doctype not in _CNB_ACCOUNTING_DOCTYPES:
		frappe.throw(_("Accounting is not supported for {0}").format(doctype))
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	id_field = _CNB_ACCOUNTING_DOCTYPES[doctype]
	if doc.docstatus == 1:
		from millitrix.finance.cnb_voucher import get_posted_cnb_accounting_lines

		return get_posted_cnb_accounting_lines(doc, document_id_field=id_field)
	from millitrix.finance.cnb_voucher import preview_cnb_accounting_lines

	return preview_cnb_accounting_lines(doc)


_ADJUSTMENT_ACCOUNTING_DOCTYPES = {
	"Paid Advance Adjustment": "payment",
	"Received Advance Adjustment": "receipt",
}


@frappe.whitelist()
def get_adjustment_accounting_lines(doctype: str, name: str, flow: str | None = None):
	"""Return accounting lines for advance adjustment forms (preview or posted)."""
	if doctype not in _ADJUSTMENT_ACCOUNTING_DOCTYPES:
		frappe.throw(_("Accounting is not supported for {0}").format(doctype))
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	resolved_flow = (flow or _ADJUSTMENT_ACCOUNTING_DOCTYPES[doctype]).lower()
	if doc.docstatus == 1:
		from millitrix.finance.advance_adjustment_common import get_posted_adjustment_accounting_lines

		return get_posted_adjustment_accounting_lines(doc)
	from millitrix.finance.advance_adjustment_common import preview_adjustment_accounting_lines

	return preview_adjustment_accounting_lines(doc, flow=resolved_flow)


_DISCOUNT_ACCOUNTING_DOCTYPES = {
	"Payable Discount Note": "payment",
	"Receivable Discount Note": "receipt",
}


@frappe.whitelist()
def get_discount_accounting_lines(doctype: str, name: str, flow: str | None = None):
	"""Return accounting lines for discount note forms (preview or posted)."""
	if doctype not in _DISCOUNT_ACCOUNTING_DOCTYPES:
		frappe.throw(_("Accounting is not supported for {0}").format(doctype))
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	resolved_flow = (flow or _DISCOUNT_ACCOUNTING_DOCTYPES[doctype]).lower()
	if doc.docstatus == 1:
		from millitrix.finance.pnr_discount_common import get_posted_pnr_discount_accounting_lines

		return get_posted_pnr_discount_accounting_lines(doc)
	from millitrix.finance.pnr_discount_common import preview_pnr_discount_accounting_lines

	return preview_pnr_discount_accounting_lines(doc, flow=resolved_flow)


_ADVANCE_ACCOUNTING_DOCTYPES = {
	"Advance Payment": "payment",
	"Advance Receipt": "receipt",
}


@frappe.whitelist()
def get_advance_accounting_lines(doctype: str, name: str, flow: str | None = None):
	"""Return accounting lines for advance payment/receipt forms (preview or posted)."""
	if doctype == "Advance PNR":
		doc = frappe.get_doc(doctype, name)
		doc.check_permission("read")
		from millitrix.finance.advance_common import advance_flow_key

		resolved_flow = (flow or advance_flow_key(doc.advance_flow)).lower()
	elif doctype in _ADVANCE_ACCOUNTING_DOCTYPES:
		doc = frappe.get_doc(doctype, name)
		doc.check_permission("read")
		resolved_flow = (flow or _ADVANCE_ACCOUNTING_DOCTYPES[doctype]).lower()
	else:
		frappe.throw(_("Accounting is not supported for {0}").format(doctype))

	if doc.docstatus == 1:
		from millitrix.finance.advance_common import get_posted_advance_accounting_lines

		return get_posted_advance_accounting_lines(doc)
	from millitrix.finance.advance_common import preview_advance_accounting_lines

	return preview_advance_accounting_lines(doc, flow=resolved_flow)


@frappe.whitelist()
def get_hawala_accounting_lines(doctype: str, name: str, flow: str | None = None):
	"""Return accounting lines for Payment By Hawala (preview or posted)."""
	if doctype != "Payment By Hawala":
		frappe.throw(_("Accounting is not supported for {0}").format(doctype))
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	if doc.docstatus == 1:
		from millitrix.finance.payment_by_hawala import get_posted_hawala_accounting_lines

		return get_posted_hawala_accounting_lines(doc)
	from millitrix.finance.payment_by_hawala import preview_hawala_accounting_lines

	return preview_hawala_accounting_lines(doc)
