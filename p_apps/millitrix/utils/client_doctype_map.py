# Canonical DocType names = client Oracle form titles (no Millitrix prefix; module is Millitrix ERP).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import re

MILLITRIX_PREFIX = "Millitrix "

# Legacy internal name → canonical client title (unprefixed).
CLIENT_NAMES: dict[str, str] = {
	"Millitrix Adjustment Invoice": "Adjustment Invoice",
	"Millitrix Adjustment PNR": "Adjustment PNR",
	"Millitrix Bank Account": "Bank Account",
	"Millitrix Bank Branch": "Bank Branch",
	"Millitrix CNB Voucher Detail": "Cash and Bank Voucher Detail",
	"Millitrix CNB Voucher Document": "Cash and Bank Voucher Document",
	"Millitrix Crash Refine Input": "Crash Refine Input",
	"Millitrix Crash Refine Output": "Crash Refine Output",
	"Millitrix Gate Pass Detail": "Gate Pass Detail",
	"Millitrix GL Open Detail": "Accounts Opening Detail",
	"Millitrix GL Statement Account": "GL Statement Account",
	"Millitrix Hawala Invoice": "Hawala Invoice",
	"Millitrix Hawala Party B": "Hawala Party B",
	"Millitrix Module Permission": "Module Permission",
	"Millitrix Party Gross Margin Invoice": "Party Gross Margin Invoice",
	"Millitrix Party Gross Margin Party B": "Party Gross Margin Party B",
	"Millitrix Party Item": "Party Item",
	"Millitrix Payslip Detail": "PaySlip Detail",
	"Millitrix PNR Document": "Payment and Receipt Document",
	"Millitrix PNR Instrument": "Payment and Receipt Instrument",
	"Millitrix PO Cancel Detail": "PO Cancellation Detail",
	"Millitrix Purchase Bill Detail": "Purchase Other Bill Detail",
	"Millitrix Purchase Bill Return Detail": "Purchase Other Bill Return Detail",
	"Millitrix Purchase Invoice Detail": "Purchase Invoice Detail",
	"Millitrix Purchase Return Detail": "Purchase Return Detail",
	"Millitrix Salary Increment Detail": "Salary Increment Detail",
	"Millitrix Sales Bill Detail": "Sales Other Bill Detail",
	"Millitrix Sales Bill Return Detail": "Sales Other Bill Return Detail",
	"Millitrix Sales Invoice Detail": "Sales Invoice Detail",
	"Millitrix Sales Return Detail": "Sales Return Detail",
	"Millitrix SO Cancel Detail": "SO Cancellation Detail",
	"Millitrix Stock Adjustment Detail": "Stock Adjustment Detail",
	"Millitrix Stock Open Detail": "Opening Stock Detail",
	"Millitrix Stock Transfer Detail": "Stock Transfer Detail",
	"Millitrix User Location": "User Location",
	"Millitrix User Store": "User Store",
	"Millitrix Voucher Detail": "Voucher Transaction Detail",
	"Millitrix Advance Adjustment": "Advance Adjustment",
	"Millitrix Bank": "Bank",
	"Millitrix Chart of Accounts": "Chart of Accounting",
	"Millitrix City": "City Setup",
	"Millitrix Closing Adjustment Entry": "Closing and Adjustment Entries",
	"Millitrix CNB Voucher": "Cash and Bank Voucher",
	"Millitrix Company": "Mill Information",
	"Millitrix Crashing Refine": "Crashing Refine",
	"Millitrix Department": "Departments",
	"Millitrix Designation": "Designation",
	"Millitrix Doc Transaction": "Document Transaction",
	"Millitrix Document Type": "Document Type",
	"Millitrix Employee": "Employee Setup",
	"Millitrix Employee Category": "Employee Category",
	"Millitrix Employee Payment Voucher": "Employee Payment Voucher",
	"Millitrix Employee Payslip": "PaySlip",
	"Millitrix Employee Receipt Voucher": "Employee Receipt Voucher",
	"Millitrix Gate Pass": "In Out Gate Pass",
	"Millitrix GL Opening": "Accounts Opening",
	"Millitrix GL Statement Template": "GL Statements",
	"Millitrix In Store Item": "Stock In Hand",
	"Millitrix Item": "Item Setup",
	"Millitrix Item Class": "Item Class",
	"Millitrix Item Price List": "Item Price List",
	"Millitrix Location": "Location",
	"Millitrix Menu": "Menu",
	"Millitrix Module": "Module",
	"Millitrix Other Contact": "Other Contact Setup",
	"Millitrix Party": "Party",
	"Millitrix Party Category": "Party Category",
	"Millitrix Party Gross Margin": "Party Gross Margin",
	"Millitrix Payment By Hawala": "Payment By Hawala",
	"Millitrix Pay Salary Increment": "Pay Salary Increment",
	"Millitrix PNR Voucher": "Payment and Receipt Voucher",
	"Millitrix PO Cancellation": "PO Cancellation",
	"Millitrix Purchase Invoice": "Purchase Invoice",
	"Millitrix Purchase Order": "Purchase Order",
	"Millitrix Purchase Other Bill": "Purchase Other Bill",
	"Millitrix Purchase Other Bill Return": "Purchase Return Other Bill",
	"Millitrix Purchase Return": "Purchase Return",
	"Millitrix Report Parameter": "Report Parameter",
	"Millitrix Sales Invoice": "Sales Invoice",
	"Millitrix Sales Order": "Sales Order",
	"Millitrix Sales Order Cancellation": "SO Cancellation",
	"Millitrix Sales Other Bill": "Sales Other Bill",
	"Millitrix Sales Other Bill Return": "Sales Return Other Bill",
	"Millitrix Sales Return": "Sales Return",
	"Millitrix Settings": "GL Parameter",
	"Millitrix Stock Adjustment": "Stock Adjustment",
	"Millitrix Stock Closing": "Closing Stock",
	"Millitrix Stock Opening": "Opening Stock",
	"Millitrix Stock Transfer": "Stock Transfer Note",
	"Millitrix Store": "Store Setup",
	"Millitrix Store Type": "Store Types",
	"Millitrix Transaction Category": "Transaction Category",
	"Millitrix Transaction Setup": "Transaction List",
	"Millitrix Unsubmit Document": "Un-Submit Documents",
	"Millitrix User": "User Rights",
	"Millitrix Voucher": "Voucher Transaction",
	"Millitrix Voucher Type": "Voucher Type",
}

# Split finance DocTypes (1:1 client screens — no legacy Millitrix prefix).
SPLIT_FINANCE_DOCTYPES: tuple[str, ...] = (
	"Advance Payment",
	"Advance Receipt",
	"Advance PNR",
	"Purchase Invoice Payment",
	"Sales Invoice Receipt",
	"Broker Invoice Payment",
	"Payable Discount Note",
	"Receivable Discount Note",
	"Payment Voucher",
	"Receipt Voucher",
	"Expense Voucher",
	"Party Payment Voucher",
	"Party Receipt Voucher",
	"Paid Advance Adjustment",
	"Received Advance Adjustment",
)


def with_millitrix_prefix(name: str) -> str:
	"""Return canonical DocType name (prefix removed). Kept for call-site compatibility."""
	return strip_millitrix_prefix(name)


def strip_millitrix_prefix(name: str) -> str:
	if name.startswith(MILLITRIX_PREFIX):
		return name[len(MILLITRIX_PREFIX) :]
	return name


_DOUBLE_PREFIX = re.compile(r"^(?:Millitrix )+")


def normalize_doctype_name(name: str) -> str:
	"""Canonical unprefixed DocType name."""
	name = _DOUBLE_PREFIX.sub("", name.strip())
	return strip_millitrix_prefix(name)


# Legacy internal name → canonical Frappe DocType name (unprefixed).
RENAME_MAP: dict[str, str] = dict(CLIENT_NAMES)

# Identity map — DocTypes are stored without Millitrix prefix.
PREFIX_RENAME_MAP: dict[str, str] = {
	client: client for client in CLIENT_NAMES.values()
}

REVERSE_MAP = {v: k for k, v in RENAME_MAP.items()}

CLIENT_DOCTYPES = frozenset(CLIENT_NAMES.values()) | frozenset(SPLIT_FINANCE_DOCTYPES)


STRIP_RENAME_MAP: dict[str, str] = {
	MILLITRIX_PREFIX + client: client for client in CLIENT_NAMES.values()
}


def strip_rename_map() -> dict[str, str]:
	return dict(STRIP_RENAME_MAP)


# Dashboard labels (may differ slightly from DocType name).
DOCTYPE_DISPLAY_OVERRIDES: dict[str, str] = {
	"GL Parameter": "GL Parameter",
	"Chart of Accounting": "Chart of Accounts",
	"User Rights": "User Management",
	"Location": "Locations",
	"Transaction List": "Transaction List",
	"Employee Payment Voucher": "Payment",
	"Employee Receipt Voucher": "Receipt",
	"In Out Gate Pass": "Gate Pass",
	"purchase-invoice-entry": "Purchase Invoice",  # legacy route — use List/Form
}


REPORT_DISPLAY_OVERRIDES: dict[str, str] = {
	"Trial_Balance": "Trial Balance",
	"Trial_Balance_1": "Trial Balance (Location)",
	"AccLedger": "Account Ledger",
	"Account_Balance": "Account Balance",
	"BalanceSheet": "Balance Sheet",
	"IncomeStatement": "Income Statement",
	"CashBook": "Cash Book",
	"BankBook": "Bank Book",
	"BankLedger": "Bank Ledger",
	"VoucherRegister": "Voucher Register",
	"COA": "Chart of Accounts",
	"GJ": "General Journal",
	"PNL": "Profit and Loss",
	"Expanse_Register": "Expense Register",
	"CashFlow": "Cash Flow",
	"CashFlowDetail": "Cash Flow Detail",
	"GLVoucher": "GL Voucher",
	"PartyLedger": "Party Ledger",
	"PartyLedgerSummary": "Party Ledger Summary",
	"PartyBalance": "Party Balance",
	"Party_Info": "Party Information",
	"Party_Bal_Paid": "Party Balance Paid",
	"PartyPRegister": "Party Payment Register",
	"PartyRRegister": "Party Receipt Register",
	"Payment_Register": "Payment Register",
	"Receipt_Register": "Receipt Register",
	"AdvPAdjustReg": "Advance Payment Adjustment Register",
	"AdvRAdjustReg": "Advance Receipt Adjustment Register",
	"AdvancePRegister": "Advance Payment Register",
	"AdvanceRRegister": "Advance Receipt Register",
	"PayableDRegister": "Payable Discount Register",
	"ReceivableDRegister": "Receivable Discount Register",
	"BankStatus": "Bank Status",
	"BankFinanceStatus": "Bank Finance Status",
	"POPending": "PO Pending",
	"PORegister": "PO Register",
	"POSummary": "PO Summary",
	"POInvDetail": "PO Invoice Detail",
	"PInvRegister": "Purchase Invoice Register",
	"PIOutstanding": "Purchase Invoice Outstanding",
	"PISummary": "PI Summary",
	"PurchInvoice": "Purchase Invoice",
	"PurchInvSummary": "Purchase Invoice Summary",
	"PurchItemSummary": "Purchase Item Summary",
	"PurchInvPayment": "Purchase Invoice Payment",
	"PurchInvPayDetl": "Purchase Invoice Payment Detail",
	"PurchInvPayDetl_Consider": "Purchase Invoice Payment Detail (Consider)",
	"DailyItemPurch": "Daily Item Purchase",
	"MonthlyItemPurch": "Monthly Item Purchase",
	"SupplierLedgerSummary": "Supplier Ledger Summary",
	"SuppOrdInvDetl": "Supplier Order Invoice Detail",
	"SuppPayAndInv": "Supplier Payment and Invoice",
	"BrokerInvPayment": "Broker Invoice Payment",
	"BrokerInvPayDetl": "Broker Invoice Payment Detail",
	"BrokerLedgerSummary": "Broker Ledger Summary",
	"SOPending": "SO Pending",
	"SORegister": "SO Register",
	"SOSummary": "SO Summary",
	"SOInvDetail": "SO Invoice Detail",
	"SInvRegister": "Sales Invoice Register",
	"SIOutstanding": "Sales Invoice Outstanding",
	"SISummary": "SI Summary",
	"SalesInvoice": "Sales Invoice",
	"SalesInvSummary": "Sales Invoice Summary",
	"SalesItemSummary": "Sales Item Summary",
	"SalesInvReceipt": "Sales Invoice Receipt",
	"SalesInvRcptDetl": "Sales Invoice Receipt Detail",
	"SalesInvRcptDetl_Consider": "Sales Invoice Receipt Detail (Consider)",
	"SuppInvAndPay": "Customer Invoice and Payment",
	"SIPOutstanding": "Sales Invoice Payment Outstanding",
	"DailyItemSales": "Daily Item Sales",
	"MonthlyItemSales": "Monthly Item Sales",
	"CustLedgerSummary": "Customer Ledger Summary",
	"CustAging": "Customer Aging",
	"CustOrdInvDetl": "Customer Order Invoice Detail",
	"Item_Stock": "Item Stock",
	"ItemLedger": "Item Ledger",
	"ItemWiseStock": "Item Wise Stock",
	"ItemBinCard": "Item Bin Card",
	"ItemDailyStock": "Item Daily Stock",
	"StkRece_Summary": "Stock Receipt Summary",
	"TStk_Summary": "Total Stock Summary",
	"UnSubmit_Stock": "Un-Submit Stock",
	"PartyBardana": "Party Bardana",
	"PartyBardanaBincard": "Party Bardana Bin Card",
	"CrashRefine": "Crash Refine",
}


def client_display_name(doctype: str) -> str:
	"""Client menu / dashboard label for a Frappe DocType or custom page route."""
	if doctype in DOCTYPE_DISPLAY_OVERRIDES:
		return DOCTYPE_DISPLAY_OVERRIDES[doctype]
	if doctype.startswith(MILLITRIX_PREFIX):
		return doctype[len(MILLITRIX_PREFIX) :]
	return doctype


def report_display_name(report_id: str) -> str:
	if report_id in REPORT_DISPLAY_OVERRIDES:
		return REPORT_DISPLAY_OVERRIDES[report_id]
	name = report_id
	if name.startswith(MILLITRIX_PREFIX):
		name = name[len(MILLITRIX_PREFIX) :]
	name = name.replace("_", " ")
	name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
	name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)
	return name


def slug(name: str) -> str:
	return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def replacements_longest_first(mapping: dict[str, str] | None = None) -> list[tuple[str, str]]:
	items = mapping or PREFIX_RENAME_MAP
	return sorted(items.items(), key=lambda item: len(item[0]), reverse=True)
