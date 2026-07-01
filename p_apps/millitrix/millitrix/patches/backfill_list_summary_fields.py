# Backfill denormalized list-view fields on existing documents.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.list_view_summary import (
	sync_advance_adjustment_list_fields,
	sync_closing_adjustment_list_fields,
	sync_cnb_general_list_fields,
	sync_cnb_party_list_fields,
	sync_closing_stock_list_fields,
	sync_employee_voucher_list_fields,
	sync_gl_opening_list_fields,
	sync_gl_statements_list_fields,
	sync_party_gross_margin_list_fields,
	sync_pnr_discount_list_fields,
	sync_pnr_invoice_list_fields,
	sync_voucher_transaction_list_fields,
	sync_crashing_refine_list_fields,
	sync_opening_stock_list_fields,
	sync_payslip_list_fields,
	sync_po_cancellation_list_fields,
	sync_so_cancellation_list_fields,
	sync_stock_adjustment_list_fields,
	sync_stock_transfer_list_fields,
	sync_unsubmit_list_fields,
)
from millitrix.trading.purchase_return import sync_purchase_return_header_from_invoice
from millitrix.trading.sales_return import sync_sales_return_header_from_invoice


def _backfill_crashing_refine() -> None:
	if not frappe.db.table_exists("tabCrashing Refine"):
		return
	if not frappe.db.has_column("tabCrashing Refine", "primary_item"):
		return

	for name in frappe.get_all("Crashing Refine", pluck="name"):
		doc = frappe.get_doc("Crashing Refine", name)
		sync_crashing_refine_list_fields(doc)
		frappe.db.set_value(
			"Crashing Refine",
			name,
			{
				"primary_item": doc.primary_item or None,
				"primary_output": doc.primary_output or None,
				"input_weight": doc.input_weight,
			},
			update_modified=False,
		)


def _backfill_payslip() -> None:
	if not frappe.db.table_exists("tabPaySlip"):
		return
	if not frappe.db.has_column("tabPaySlip", "employee_count"):
		return

	for name in frappe.get_all("PaySlip", pluck="name"):
		doc = frappe.get_doc("PaySlip", name)
		sync_payslip_list_fields(doc)
		frappe.db.set_value(
			"PaySlip",
			name,
			{
				"primary_employee": doc.primary_employee or None,
				"employee_count": doc.employee_count,
				"total_salary": doc.total_salary,
			},
			update_modified=False,
		)


def _backfill_po_cancellation() -> None:
	if not frappe.db.table_exists("tabPO Cancellation"):
		return
	if not frappe.db.has_column("tabPO Cancellation", "primary_item"):
		return

	for name in frappe.get_all("PO Cancellation", pluck="name"):
		doc = frappe.get_doc("PO Cancellation", name)
		sync_po_cancellation_list_fields(doc)
		frappe.db.set_value(
			"PO Cancellation",
			name,
			{
				"primary_item": doc.primary_item or None,
				"total_cancel_qty": doc.total_cancel_qty,
				"line_count": doc.line_count,
			},
			update_modified=False,
		)


def _backfill_purchase_return() -> None:
	if not frappe.db.table_exists("tabPurchase Return"):
		return
	if not frappe.db.has_column("tabPurchase Return", "itemcode"):
		return

	for name in frappe.get_all("Purchase Return", pluck="name"):
		doc = frappe.get_doc("Purchase Return", name)
		if not doc.purchinvno or not frappe.db.exists("Purchase Invoice", doc.purchinvno):
			continue
		pi = frappe.get_doc("Purchase Invoice", doc.purchinvno)
		sync_purchase_return_header_from_invoice(doc, pi)
		frappe.db.set_value(
			"Purchase Return",
			name,
			{
				"itemcode": doc.itemcode or None,
				"supplierid": doc.supplierid or None,
				"brokerid": doc.brokerid or None,
				"sub_partyid": doc.sub_partyid or None,
			},
			update_modified=False,
		)


def _backfill_purchase_return_other_bill() -> None:
	if not frappe.db.table_exists("tabPurchase Return Other Bill"):
		return
	if not frappe.db.has_column("tabPurchase Return Other Bill", "partyid"):
		return

	for name in frappe.get_all("Purchase Return Other Bill", pluck="name"):
		doc = frappe.get_doc("Purchase Return Other Bill", name)
		if not doc.pbillno or not frappe.db.exists("Purchase Other Bill", doc.pbillno):
			continue
		partyid = frappe.db.get_value("Purchase Other Bill", doc.pbillno, "partyid")
		if partyid:
			frappe.db.set_value(
				"Purchase Return Other Bill",
				name,
				{"partyid": partyid},
				update_modified=False,
			)


def _backfill_sales_return() -> None:
	if not frappe.db.table_exists("tabSales Return"):
		return
	if not frappe.db.has_column("tabSales Return", "itemcode"):
		return

	for name in frappe.get_all("Sales Return", pluck="name"):
		doc = frappe.get_doc("Sales Return", name)
		if not doc.salesinvno or not frappe.db.exists("Sales Invoice", doc.salesinvno):
			continue
		si = frappe.get_doc("Sales Invoice", doc.salesinvno)
		sync_sales_return_header_from_invoice(doc, si)
		frappe.db.set_value(
			"Sales Return",
			name,
			{
				"itemcode": doc.itemcode or None,
				"customerid": doc.customerid or None,
				"brokerid": doc.brokerid or None,
				"sub_partyid": doc.sub_partyid or None,
			},
			update_modified=False,
		)


def _backfill_sales_return_other_bill() -> None:
	if not frappe.db.table_exists("tabSales Return Other Bill"):
		return
	if not frappe.db.has_column("tabSales Return Other Bill", "partyid"):
		return

	for name in frappe.get_all("Sales Return Other Bill", pluck="name"):
		doc = frappe.get_doc("Sales Return Other Bill", name)
		if not doc.sbillno or not frappe.db.exists("Sales Other Bill", doc.sbillno):
			continue
		partyid = frappe.db.get_value("Sales Other Bill", doc.sbillno, "partyid")
		if partyid:
			frappe.db.set_value(
				"Sales Return Other Bill",
				name,
				{"partyid": partyid},
				update_modified=False,
			)


def _backfill_so_cancellation() -> None:
	if not frappe.db.table_exists("tabSO Cancellation"):
		return
	if not frappe.db.has_column("tabSO Cancellation", "primary_item"):
		return

	for name in frappe.get_all("SO Cancellation", pluck="name"):
		doc = frappe.get_doc("SO Cancellation", name)
		sync_so_cancellation_list_fields(doc)
		frappe.db.set_value(
			"SO Cancellation",
			name,
			{
				"primary_item": doc.primary_item or None,
				"total_cancel_qty": doc.total_cancel_qty,
				"line_count": doc.line_count,
			},
			update_modified=False,
		)


def _backfill_stock_adjustment() -> None:
	if not frappe.db.table_exists("tabStock Adjustment"):
		return
	if not frappe.db.has_column("tabStock Adjustment", "primary_item"):
		return

	for name in frappe.get_all("Stock Adjustment", pluck="name"):
		doc = frappe.get_doc("Stock Adjustment", name)
		sync_stock_adjustment_list_fields(doc)
		frappe.db.set_value(
			"Stock Adjustment",
			name,
			{
				"primary_item": doc.primary_item or None,
				"primary_store": doc.primary_store or None,
				"line_count": doc.line_count,
				"total_amount": doc.total_amount,
			},
			update_modified=False,
		)


def _backfill_opening_stock() -> None:
	if not frappe.db.table_exists("tabOpening Stock"):
		return
	if not frappe.db.has_column("tabOpening Stock", "primary_item"):
		return

	for name in frappe.get_all("Opening Stock", pluck="name"):
		doc = frappe.get_doc("Opening Stock", name)
		sync_opening_stock_list_fields(doc)
		frappe.db.set_value(
			"Opening Stock",
			name,
			{
				"primary_item": doc.primary_item or None,
				"primary_store": doc.primary_store or None,
				"line_count": doc.line_count,
				"total_stock_value": doc.total_stock_value,
			},
			update_modified=False,
		)


def _backfill_closing_stock() -> None:
	if not frappe.db.table_exists("tabClosing Stock"):
		return
	if not frappe.db.has_column("tabClosing Stock", "primary_item"):
		return

	for name in frappe.get_all("Closing Stock", pluck="name"):
		doc = frappe.get_doc("Closing Stock", name)
		sync_closing_stock_list_fields(doc)
		frappe.db.set_value(
			"Closing Stock",
			name,
			{
				"primary_item": doc.primary_item or None,
				"primary_store": doc.primary_store or None,
				"line_count": doc.line_count,
				"total_stock": doc.total_stock,
			},
			update_modified=False,
		)


def _backfill_stock_transfer() -> None:
	if not frappe.db.table_exists("tabStock Transfer Note"):
		return
	if not frappe.db.has_column("tabStock Transfer Note", "primary_tostore"):
		return

	for name in frappe.get_all("Stock Transfer Note", pluck="name"):
		doc = frappe.get_doc("Stock Transfer Note", name)
		sync_stock_transfer_list_fields(doc)
		frappe.db.set_value(
			"Stock Transfer Note",
			name,
			{
				"primary_tostore": doc.primary_tostore or None,
				"line_count": doc.line_count,
				"total_netweight": doc.total_netweight,
			},
			update_modified=False,
		)


def _backfill_unsubmit() -> None:
	if not frappe.db.table_exists("tabUn-Submit Documents"):
		return
	if not frappe.db.has_column("tabUn-Submit Documents", "doc_description"):
		return

	for name in frappe.get_all("Un-Submit Documents", pluck="name"):
		doc = frappe.get_doc("Un-Submit Documents", name)
		sync_unsubmit_list_fields(doc)
		frappe.db.set_value(
			"Un-Submit Documents",
			name,
			{"doc_description": doc.doc_description or None},
			update_modified=False,
		)


def _backfill_advance_adjustment(doctype: str) -> None:
	table = f"tab{doctype}"
	if not frappe.db.table_exists(table):
		return
	if not frappe.db.has_column(table, "line_count"):
		return

	for name in frappe.get_all(doctype, pluck="name"):
		doc = frappe.get_doc(doctype, name)
		sync_advance_adjustment_list_fields(doc)
		frappe.db.set_value(
			doctype,
			name,
			{"line_count": doc.line_count},
			update_modified=False,
		)


def _backfill_closing_adjustment() -> None:
	if not frappe.db.table_exists("tabClosing and Adjustment Entries"):
		return
	if not frappe.db.has_column("tabClosing and Adjustment Entries", "primary_acc"):
		return

	for name in frappe.get_all("Closing and Adjustment Entries", pluck="name"):
		doc = frappe.get_doc("Closing and Adjustment Entries", name)
		sync_closing_adjustment_list_fields(doc)
		frappe.db.set_value(
			"Closing and Adjustment Entries",
			name,
			{
				"primary_acc": doc.primary_acc or None,
				"line_count": doc.line_count,
			},
			update_modified=False,
		)


def _backfill_cnb_general(doctype: str) -> None:
	table = f"tab{doctype}"
	if not frappe.db.table_exists(table):
		return
	if not frappe.db.has_column(table, "primary_acc"):
		return

	for name in frappe.get_all(doctype, pluck="name"):
		doc = frappe.get_doc(doctype, name)
		sync_cnb_general_list_fields(doc)
		frappe.db.set_value(
			doctype,
			name,
			{
				"primary_acc": doc.primary_acc or None,
				"line_count": doc.line_count,
			},
			update_modified=False,
		)


def _backfill_cnb_party(doctype: str) -> None:
	table = f"tab{doctype}"
	if not frappe.db.table_exists(table):
		return
	if not frappe.db.has_column(table, "line_count"):
		return

	for name in frappe.get_all(doctype, pluck="name"):
		doc = frappe.get_doc(doctype, name)
		sync_cnb_party_list_fields(doc)
		frappe.db.set_value(
			doctype,
			name,
			{"line_count": doc.line_count},
			update_modified=False,
		)


def _backfill_employee_voucher(doctype: str) -> None:
	table = f"tab{doctype}"
	if not frappe.db.table_exists(table):
		return
	if not frappe.db.has_column(table, "primary_employee"):
		return

	for name in frappe.get_all(doctype, pluck="name"):
		doc = frappe.get_doc(doctype, name)
		sync_employee_voucher_list_fields(doc)
		frappe.db.set_value(
			doctype,
			name,
			{
				"primary_employee": doc.primary_employee or None,
				"line_count": doc.line_count,
			},
			update_modified=False,
		)


def _backfill_gl_opening() -> None:
	if not frappe.db.table_exists("tabAccounts Opening"):
		return
	if not frappe.db.has_column("tabAccounts Opening", "primary_acc"):
		return

	for name in frappe.get_all("Accounts Opening", pluck="name"):
		doc = frappe.get_doc("Accounts Opening", name)
		sync_gl_opening_list_fields(doc)
		frappe.db.set_value(
			"Accounts Opening",
			name,
			{
				"primary_acc": doc.primary_acc or None,
				"line_count": doc.line_count,
			},
			update_modified=False,
		)


def _backfill_gl_statements() -> None:
	if not frappe.db.table_exists("tabGL Statements"):
		return
	if not frappe.db.has_column("tabGL Statements", "line_count"):
		return

	for name in frappe.get_all("GL Statements", pluck="name"):
		doc = frappe.get_doc("GL Statements", name)
		sync_gl_statements_list_fields(doc)
		frappe.db.set_value(
			"GL Statements",
			name,
			{
				"line_count": doc.line_count,
				"account_count": doc.account_count,
			},
			update_modified=False,
		)


def _backfill_pnr_discount(doctype: str) -> None:
	if not frappe.db.table_exists(f"tab{doctype}"):
		return
	if not frappe.db.has_column(f"tab{doctype}", "line_count"):
		return

	for name in frappe.get_all(doctype, pluck="name"):
		doc = frappe.get_doc(doctype, name)
		sync_pnr_discount_list_fields(doc)
		frappe.db.set_value(
			doctype,
			name,
			{"line_count": doc.line_count},
			update_modified=False,
		)


def _backfill_party_gross_margin() -> None:
	if not frappe.db.table_exists("tabParty Gross Margin"):
		return
	if not frappe.db.has_column("tabParty Gross Margin", "line_count"):
		return

	for name in frappe.get_all("Party Gross Margin", pluck="name"):
		doc = frappe.get_doc("Party Gross Margin", name)
		sync_party_gross_margin_list_fields(doc)
		frappe.db.set_value(
			"Party Gross Margin",
			name,
			{"line_count": doc.line_count},
			update_modified=False,
		)


def _backfill_pnr_invoice(doctype: str) -> None:
	if not frappe.db.table_exists(f"tab{doctype}"):
		return
	if not frappe.db.has_column(f"tab{doctype}", "line_count"):
		return

	for name in frappe.get_all(doctype, pluck="name"):
		doc = frappe.get_doc(doctype, name)
		sync_pnr_invoice_list_fields(doc)
		frappe.db.set_value(
			doctype,
			name,
			{
				"line_count": doc.line_count,
				"pnrmode": doc.pnrmode or None,
			},
			update_modified=False,
		)


def _backfill_voucher_transaction() -> None:
	if not frappe.db.table_exists("tabVoucher Transaction"):
		return
	if not frappe.db.has_column("tabVoucher Transaction", "line_count"):
		return

	for name in frappe.get_all("Voucher Transaction", pluck="name"):
		doc = frappe.get_doc("Voucher Transaction", name)
		doc.total_debit = sum(flt(line.debit) for line in doc.details or [])
		doc.total_credit = sum(flt(line.credit) for line in doc.details or [])
		sync_voucher_transaction_list_fields(doc)
		frappe.db.set_value(
			"Voucher Transaction",
			name,
			{
				"line_count": doc.line_count,
				"primary_acc": doc.primary_acc or None,
				"total_debit": doc.total_debit,
				"total_credit": doc.total_credit,
			},
			update_modified=False,
		)


def execute() -> None:
	_backfill_crashing_refine()
	_backfill_payslip()
	_backfill_po_cancellation()
	_backfill_purchase_return()
	_backfill_purchase_return_other_bill()
	_backfill_sales_return()
	_backfill_sales_return_other_bill()
	_backfill_so_cancellation()
	_backfill_stock_adjustment()
	_backfill_opening_stock()
	_backfill_closing_stock()
	_backfill_stock_transfer()
	_backfill_unsubmit()
	_backfill_advance_adjustment("Paid Advance Adjustment")
	_backfill_advance_adjustment("Received Advance Adjustment")
	_backfill_closing_adjustment()
	for dt in ("Payment Voucher", "Receipt Voucher", "Expense Voucher"):
		_backfill_cnb_general(dt)
	for dt in ("Party Payment Voucher", "Party Receipt Voucher"):
		_backfill_cnb_party(dt)
	for dt in ("Employee Payment Voucher", "Employee Receipt Voucher"):
		_backfill_employee_voucher(dt)
	_backfill_gl_opening()
	_backfill_gl_statements()
	for dt in ("Payable Discount Note", "Receivable Discount Note"):
		_backfill_pnr_discount(dt)
	_backfill_party_gross_margin()
	for dt in (
		"Purchase Invoice Payment",
		"Sales Invoice Receipt",
		"Broker Invoice Payment",
	):
		_backfill_pnr_invoice(dt)
	_backfill_voucher_transaction()
	frappe.db.commit()
