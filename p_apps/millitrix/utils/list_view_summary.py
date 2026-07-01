# Copyright (c) 2026, Millitrix and contributors
# Sync denormalized list-view fields from child tables (save / validate).

from __future__ import annotations

import frappe
from frappe.utils import flt


def sync_crashing_refine_list_fields(doc) -> None:
	"""First input item + weight + first output item for premium list."""
	inputs = doc.inputs or []
	outputs = doc.outputs or []
	primary_in = inputs[0] if inputs else None
	primary_out = outputs[0] if outputs else None

	doc.primary_item = (primary_in.critem if primary_in else "") or ""
	doc.primary_output = (primary_out.proditem if primary_out else "") or ""
	doc.input_weight = flt(primary_in.total_weight) if primary_in else 0.0


def sync_payslip_list_fields(doc) -> None:
	"""First employee + headcount + gross salary total for premium list."""
	lines = [row for row in (doc.employees or []) if row.empno]
	doc.employee_count = len(lines)
	doc.total_salary = sum(flt(row.amount) for row in lines)
	doc.primary_employee = lines[0].empno if len(lines) == 1 else ""


def sync_po_cancellation_list_fields(doc) -> None:
	"""First cancelled item + totals for premium list."""
	lines = [row for row in (doc.details or []) if row.ponumber]
	doc.line_count = len(lines)
	doc.total_cancel_qty = sum(flt(row.cancelqty) for row in lines)
	first = lines[0] if lines else None
	if first and first.itemcode:
		doc.primary_item = first.itemcode
	elif first and first.ponumber:
		doc.primary_item = frappe.db.get_value("Purchase Order", first.ponumber, "itemcode") or ""
	else:
		doc.primary_item = ""


def sync_so_cancellation_list_fields(doc) -> None:
	"""First cancelled item + totals for premium list."""
	lines = [row for row in (doc.details or []) if row.sonumber]
	doc.line_count = len(lines)
	doc.total_cancel_qty = sum(flt(row.cancelqty) for row in lines)
	first = lines[0] if lines else None
	if first and first.itemcode:
		doc.primary_item = first.itemcode
	elif first and first.sonumber:
		doc.primary_item = frappe.db.get_value("Sales Order", first.sonumber, "itemcode") or ""
	else:
		doc.primary_item = ""


def sync_stock_adjustment_list_fields(doc) -> None:
	"""First line item/store + totals for premium list."""
	lines = [row for row in (doc.details or []) if row.itemcode and row.storeid]
	doc.line_count = len(lines)
	doc.total_amount = sum(flt(row.amount) for row in lines)
	first = lines[0] if lines else None
	doc.primary_item = (first.itemcode if first else "") or ""
	doc.primary_store = (first.storeid if first else "") or ""


def sync_opening_stock_list_fields(doc) -> None:
	"""First line item/store + totals for premium list."""
	lines = [row for row in (doc.details or []) if row.itemcode and row.storeid]
	doc.line_count = len(lines)
	doc.total_stock_value = sum(flt(row.stock_value) for row in lines)
	first = lines[0] if lines else None
	doc.primary_item = (first.itemcode if first else "") or ""
	doc.primary_store = (first.storeid if first else "") or ""


def sync_closing_stock_list_fields(doc) -> None:
	"""First line item/store + closing value totals for premium list."""
	lines = [row for row in (doc.details or []) if row.itemcode and row.storeid]
	doc.line_count = len(lines)
	doc.total_stock = sum(flt(row.stock_value) for row in lines)
	first = lines[0] if lines else None
	doc.primary_item = (first.itemcode if first else "") or ""
	doc.primary_store = (first.storeid if first else "") or ""


def sync_stock_transfer_list_fields(doc) -> None:
	"""Header item + first to-store + line totals for premium list."""
	lines = [row for row in (doc.details or []) if row.tostoreid]
	doc.line_count = len(lines)
	doc.total_netweight = sum(flt(row.netweight) for row in lines)
	first = lines[0] if lines else None
	doc.primary_tostore = (first.tostoreid if first else "") or ""


def sync_unsubmit_list_fields(doc) -> None:
	from millitrix.finance.unsubmit import resolve_target_doctype
	from millitrix.utils.unsubmit_display import get_unsubmit_document_description

	target = doc.target_doctype or resolve_target_doctype(doc)
	if target and doc.documentid:
		doc.doc_description = get_unsubmit_document_description(target, doc.documentid)
	else:
		doc.doc_description = ""


def sync_advance_adjustment_list_fields(doc) -> None:
	"""PNR + invoice line count for premium list."""
	doc.line_count = len(doc.pnr_lines or []) + len(doc.invoice_lines or [])


def sync_closing_adjustment_list_fields(doc) -> None:
	"""First account + line count for premium list."""
	lines = [row for row in (doc.details or []) if row.accid]
	doc.line_count = len(lines)
	first = lines[0] if lines else None
	doc.primary_acc = (first.accid if first else "") or ""


def sync_cnb_general_list_fields(doc) -> None:
	"""First account + line count for general CNB vouchers."""
	lines = [row for row in (doc.details or []) if row.accid or row.trans_id]
	doc.line_count = len(lines)
	first = lines[0] if lines else None
	doc.primary_acc = (first.accid if first else "") or ""


def sync_cnb_party_list_fields(doc) -> None:
	"""Knockoff line count for party CNB vouchers."""
	doc.line_count = len([row for row in (doc.documents or []) if row.partyid or row.documentid])


def sync_employee_voucher_list_fields(doc) -> None:
	"""First employee + line count for employee CNB vouchers."""
	lines = [row for row in (doc.documents or []) if row.empno]
	doc.line_count = len(lines)
	doc.primary_employee = lines[0].empno if len(lines) == 1 else ""


def sync_gl_opening_list_fields(doc) -> None:
	"""First account + line count for accounts opening list."""
	lines = [row for row in (doc.details or []) if row.accid]
	doc.line_count = len(lines)
	first = lines[0] if lines else None
	doc.primary_acc = (first.accid if first else "") or ""


def sync_gl_statements_list_fields(doc) -> None:
	"""Sub-line and GL account counts for statement master list."""
	doc.line_count = len(doc.sub_statements or [])
	doc.account_count = len([row for row in (doc.gl_accounts or []) if row.accid])


def sync_pnr_discount_list_fields(doc) -> None:
	doc.line_count = len([row for row in (doc.documents or []) if row.documentid])


def sync_party_gross_margin_list_fields(doc) -> None:
	doc.line_count = len(doc.party_b_lines or []) + len(doc.invoices or [])


def sync_pnr_invoice_list_fields(doc) -> None:
	doc.line_count = len([row for row in (doc.documents or []) if row.documentid])
	instruments = [row for row in (doc.instruments or []) if row.pnrmode]
	doc.pnrmode = instruments[0].pnrmode if instruments else (doc.pnrmode or "")


def sync_voucher_transaction_list_fields(doc) -> None:
	lines = [row for row in (doc.details or []) if row.accid]
	doc.line_count = len(lines)
	first = lines[0] if lines else None
	doc.primary_acc = (first.accid if first else "") or ""


SYNC_HANDLERS = {
	"Crashing Refine": sync_crashing_refine_list_fields,
	"PaySlip": sync_payslip_list_fields,
	"PO Cancellation": sync_po_cancellation_list_fields,
	"SO Cancellation": sync_so_cancellation_list_fields,
	"Stock Adjustment": sync_stock_adjustment_list_fields,
	"Opening Stock": sync_opening_stock_list_fields,
	"Closing Stock": sync_closing_stock_list_fields,
	"Stock Transfer Note": sync_stock_transfer_list_fields,
	"Un-Submit Documents": sync_unsubmit_list_fields,
	"Paid Advance Adjustment": sync_advance_adjustment_list_fields,
	"Received Advance Adjustment": sync_advance_adjustment_list_fields,
	"Closing and Adjustment Entries": sync_closing_adjustment_list_fields,
	"Payment Voucher": sync_cnb_general_list_fields,
	"Receipt Voucher": sync_cnb_general_list_fields,
	"Expense Voucher": sync_cnb_general_list_fields,
	"Party Payment Voucher": sync_cnb_party_list_fields,
	"Party Receipt Voucher": sync_cnb_party_list_fields,
	"Employee Payment Voucher": sync_employee_voucher_list_fields,
	"Employee Receipt Voucher": sync_employee_voucher_list_fields,
	"Accounts Opening": sync_gl_opening_list_fields,
	"GL Statements": sync_gl_statements_list_fields,
	"Payable Discount Note": sync_pnr_discount_list_fields,
	"Receivable Discount Note": sync_pnr_discount_list_fields,
	"Party Gross Margin": sync_party_gross_margin_list_fields,
	"Purchase Invoice Payment": sync_pnr_invoice_list_fields,
	"Sales Invoice Receipt": sync_pnr_invoice_list_fields,
	"Broker Invoice Payment": sync_pnr_invoice_list_fields,
	"Voucher Transaction": sync_voucher_transaction_list_fields,
}


def sync_list_summary_fields(doc) -> None:
	handler = SYNC_HANDLERS.get(doc.doctype)
	if handler:
		handler(doc)
