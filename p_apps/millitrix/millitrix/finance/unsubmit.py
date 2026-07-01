# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.6 — UNSUBMIT / Section 12

from __future__ import annotations

import frappe
from frappe import _

from millitrix.utils.document_display import resolve_document_name
from millitrix.utils.doctype_ids import UNSUBMIT_DOCUMENT
from millitrix.utils.field_normalizers import is_yes
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.user_permissions import check_unsubmit_permission
from millitrix.utils.stock import mark_posted, mark_unposted

# on_cancel handlers reverse stock / GL / order balances for each module.
_REVERSE_HANDLERS: dict[str, str] = {
	"In Out Gate Pass": "millitrix.stock.gate_pass.on_cancel",
	"Opening Stock": "millitrix.stock.stock_opening.on_cancel",
	"Closing Stock": "millitrix.stock.stock_closing.on_cancel",
	"Stock Adjustment": "millitrix.stock.stock_adjustment.on_cancel",
	"Stock Transfer Note": "millitrix.stock.stock_transfer.on_cancel",
	"Purchase Order": "millitrix.trading.purchase_order.on_cancel",
	"PO Cancellation": "millitrix.trading.po_cancellation.on_cancel",
	"Purchase Invoice": "millitrix.trading.purchase_invoice.on_cancel",
	"Purchase Return": "millitrix.trading.purchase_return.on_cancel",
	"Purchase Other Bill": "millitrix.trading.purchase_other_bill.on_cancel",
	"Sales Order": "millitrix.trading.sales_order.on_cancel",
	"SO Cancellation": "millitrix.trading.sales_order_cancellation.on_cancel",
	"Sales Invoice": "millitrix.trading.sales_invoice.on_cancel",
	"Sales Return": "millitrix.trading.sales_return.on_cancel",
	"Sales Other Bill": "millitrix.trading.sales_other_bill.on_cancel",
	"Voucher Transaction": "millitrix.finance.mill_voucher.on_cancel",
	"Payment and Receipt Voucher": "millitrix.finance.pnr_voucher.on_cancel",
	"Cash and Bank Voucher": "millitrix.finance.cnb_voucher.on_cancel",
	"Accounts Opening": "millitrix.finance.gl_opening.on_cancel",
	"Crashing Refine": "millitrix.production.crashing_refine.on_cancel",
	"PaySlip": "millitrix.hr.employee_payslip.on_cancel",
	"Advance Adjustment": "millitrix.finance.advance_adjustment.on_cancel",
	"Payment By Hawala": "millitrix.finance.payment_by_hawala.on_cancel",
	"Party Gross Margin": "millitrix.finance.party_gross_margin.on_cancel",
	"Purchase Return Other Bill": "millitrix.trading.purchase_other_bill_return.on_cancel",
	"Sales Return Other Bill": "millitrix.trading.sales_other_bill_return.on_cancel",
	"Advance PNR": "millitrix.finance.advance_common.cancel_advance_doc",
	"Advance Payment": "millitrix.finance.advance_common.cancel_advance_doc",
	"Advance Receipt": "millitrix.finance.advance_common.cancel_advance_doc",
	"Purchase Invoice Payment": "millitrix.finance.pnr_invoice_common.cancel_pnr_invoice_doc",
	"Sales Invoice Receipt": "millitrix.finance.pnr_invoice_common.cancel_pnr_invoice_doc",
	"Broker Invoice Payment": "millitrix.finance.pnr_invoice_common.cancel_pnr_invoice_doc",
	"Payable Discount Note": "millitrix.finance.pnr_discount_common.cancel_pnr_discount_doc",
	"Receivable Discount Note": "millitrix.finance.pnr_discount_common.cancel_pnr_discount_doc",
	"Payment Voucher": "millitrix.finance.cnb_general_common.cancel_cnb_general_doc",
	"Receipt Voucher": "millitrix.finance.cnb_general_common.cancel_cnb_general_doc",
	"Expense Voucher": "millitrix.finance.cnb_general_common.cancel_cnb_general_doc",
	"Party Payment Voucher": "millitrix.finance.cnb_party_common.cancel_cnb_party_doc",
	"Party Receipt Voucher": "millitrix.finance.cnb_party_common.cancel_cnb_party_doc",
	"Paid Advance Adjustment": "millitrix.finance.advance_adjustment_common.cancel_adjustment_doc",
	"Received Advance Adjustment": "millitrix.finance.advance_adjustment_common.cancel_adjustment_doc",
	"Closing and Adjustment Entries": "millitrix.finance.closing_adjustment_entry.on_cancel",
	"Pay Salary Increment": "millitrix.hr.pay_salary_increment.on_cancel",
}

SUPPORTED_UNSUBMIT_DOCTYPES = frozenset(_REVERSE_HANDLERS)


def resolve_target_doctype(doc) -> str | None:
	"""Oracle USDOCTYPE — Module link (code + name) or legacy DocType name."""
	val = doc.get("usdoctype")
	if not val:
		return None
	if frappe.db.exists("DocType", val):
		return val
	return frappe.db.get_value("Module", val, "doctypeid")


def validate(doc, method=None):
	check_unsubmit_permission()
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = UNSUBMIT_DOCUMENT
	validate_fiscal_period(doc.usdate)
	target_doctype = resolve_target_doctype(doc)
	doc.target_doctype = target_doctype
	if not target_doctype:
		frappe.throw(_("Select document type to unsubmit"))
	if not doc.documentid:
		frappe.throw(_("Enter document ID to unsubmit"))
	if target_doctype not in _REVERSE_HANDLERS:
		frappe.throw(_("Unsubmit not supported for {0}").format(target_doctype))

	source_name = resolve_document_name(target_doctype, doc.documentid)
	if not source_name:
		frappe.throw(_("{0} {1} does not exist").format(target_doctype, doc.documentid))

	source = frappe.get_doc(target_doctype, source_name)
	if source.docstatus != 1:
		frappe.throw(_("Only submitted documents can be unsubmitted"))
	if not is_yes(source.posted):
		frappe.throw(_("Source document is not posted"))

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def on_submit(doc, method=None):
	target_doctype = resolve_target_doctype(doc)
	if not target_doctype:
		frappe.throw(_("Select document type to unsubmit"))
	source_name = resolve_document_name(target_doctype, doc.documentid)
	if not source_name:
		frappe.throw(_("{0} {1} does not exist").format(target_doctype, doc.documentid))
	reverse_posted_document(target_doctype, source_name)
	mark_posted(doc)


def on_cancel(doc, method=None):
	mark_unposted(doc)


def reverse_posted_document(doctype: str, name: str) -> None:
	"""Reverse side-effects and return document to editable draft (legacy UNSUBMIT)."""
	if doctype not in _REVERSE_HANDLERS:
		frappe.throw(_("Unsubmit not supported for {0}").format(doctype))

	frappe.db.sql(
		f"SELECT name FROM `tab{doctype}` WHERE name = %s FOR UPDATE",
		(name,),
	)
	source = frappe.get_doc(doctype, name)
	source.check_permission("cancel")
	from millitrix.utils.user_permissions import validate_location_access, validate_store_access

	validate_location_access(source)
	validate_store_access(source)
	if source.docstatus != 1:
		frappe.throw(_("Document {0} is not submitted").format(name))

	frappe.flags.in_unsubmit = True
	try:
		handler = frappe.get_attr(_REVERSE_HANDLERS[doctype])
		handler(source)
		current_status = int(frappe.db.get_value(doctype, name, "docstatus") or 0)
		if current_status != 1:
			frappe.throw(_("Document {0} is no longer submitted").format(name))
		frappe.db.set_value(
			doctype,
			name,
			{"docstatus": 0, "posted": "Draft", "posted_by": None},
			update_modified=False,
		)
	finally:
		frappe.flags.in_unsubmit = False
