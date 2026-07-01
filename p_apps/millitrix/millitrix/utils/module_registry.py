# Copyright (c) 2026, Millitrix and contributors
"""Blueprint menu + module registry for Oracle PROJECTMENU / PROJECTMODULES seed."""

from __future__ import annotations

from millitrix.utils.report_registry import REPORT_FOLDER_BY_LEGACY_ID

# Root + major branches (blueprint §3.2)
MENU_ROWS: tuple[dict, ...] = (
	{"menuid": 1, "parentid": 0, "description": "Business Management", "sortby": 1},
	{"menuid": 10, "parentid": 1, "description": "System Controls", "sortby": 1},
	{"menuid": 20, "parentid": 1, "description": "Human Resource", "sortby": 2},
	{"menuid": 30, "parentid": 1, "description": "Production", "sortby": 3},
	{"menuid": 40, "parentid": 1, "description": "Supply Chain Management", "sortby": 4},
	{"menuid": 50, "parentid": 1, "description": "Purchase", "sortby": 5},
	{"menuid": 60, "parentid": 1, "description": "Sales", "sortby": 6},
	{"menuid": 70, "parentid": 1, "description": "Stock", "sortby": 7},
	{"menuid": 80, "parentid": 1, "description": "Financial", "sortby": 8},
)

# Form modules: runtime .fmx basename (no ext) → Frappe DocType
FORM_MODULES: tuple[dict, ...] = (
	{"moduleid": 101, "menuid": 10, "module": "Locations", "runtimefile": "All_Location", "doctypeid": "Location", "nature": "Assets"},
	{"moduleid": 102, "menuid": 10, "module": "User Management", "runtimefile": "User_Management", "doctypeid": "User Rights", "nature": "Assets"},
	{"moduleid": 103, "menuid": 10, "module": "Un-Submit Documents", "runtimefile": "UnSubmit", "doctypeid": "Un-Submit Documents", "nature": "Assets"},
	{"moduleid": 104, "menuid": 10, "module": "Change User Password", "runtimefile": "Change_User_Pwd", "doctypeid": "change-user-password", "nature": "Assets"},
	{"moduleid": 105, "menuid": 10, "module": "Database Backup", "runtimefile": "BACKUP", "doctypeid": "database-backup", "nature": "Assets"},
	{"moduleid": 201, "menuid": 20, "module": "Departments", "runtimefile": "All_Departments", "doctypeid": "Departments", "nature": "Expenses"},
	{"moduleid": 202, "menuid": 20, "module": "Designation", "runtimefile": "All_Designation", "doctypeid": "Designation", "nature": "Expenses"},
	{"moduleid": 203, "menuid": 20, "module": "Employee Category", "runtimefile": "Pay_EmpCategory", "doctypeid": "Employee Category", "nature": "Expenses"},
	{"moduleid": 204, "menuid": 20, "module": "Employee Setup", "runtimefile": "Employee", "doctypeid": "Employee Setup", "nature": "Expenses"},
	{"moduleid": 205, "menuid": 20, "module": "PaySlip", "runtimefile": "Pay_PaySlip", "doctypeid": "PaySlip", "nature": "Expenses"},
	{"moduleid": 206, "menuid": 20, "module": "Employee Payment", "runtimefile": "CNBEmpVoucher", "doctypeid": "Employee Payment Voucher", "nature": "Expenses"},
	{"moduleid": 207, "menuid": 20, "module": "Employee Receipt", "runtimefile": "CNBEmpVoucher", "doctypeid": "Employee Receipt Voucher", "nature": "Expenses"},
	{"moduleid": 301, "menuid": 30, "module": "Crashing Refine", "runtimefile": "CrashRefine", "doctypeid": "Crashing Refine", "nature": "Expenses"},
	{"moduleid": 401, "menuid": 40, "module": "City Setup", "runtimefile": "CityMaster", "doctypeid": "City Setup", "nature": "Assets"},
	{"moduleid": 402, "menuid": 40, "module": "Store Types", "runtimefile": "IN_Store_Types", "doctypeid": "Store Types", "nature": "Assets"},
	{"moduleid": 403, "menuid": 40, "module": "Store Setup", "runtimefile": "IN_Stores", "doctypeid": "Store Setup", "nature": "Assets"},
	{"moduleid": 404, "menuid": 40, "module": "Item Class", "runtimefile": "Item_Class", "doctypeid": "Item Class", "nature": "Assets"},
	{"moduleid": 405, "menuid": 40, "module": "Item Setup", "runtimefile": "Item_Master", "doctypeid": "Item Setup", "nature": "Assets"},
	{"moduleid": 406, "menuid": 40, "module": "Item Price List", "runtimefile": "Item_Price_List", "doctypeid": "Item Price List", "nature": "Assets"},
	{"moduleid": 407, "menuid": 40, "module": "Party Category", "runtimefile": "Party_Category", "doctypeid": "Party Category", "nature": "Assets"},
	{"moduleid": 408, "menuid": 40, "module": "Broker Setup", "runtimefile": "All_Party", "doctypeid": "Party", "nature": "Assets"},
	{"moduleid": 409, "menuid": 40, "module": "Supplier Setup", "runtimefile": "All_Party", "doctypeid": "Party", "nature": "Assets"},
	{"moduleid": 410, "menuid": 40, "module": "Customer Setup", "runtimefile": "All_Party", "doctypeid": "Party", "nature": "Assets"},
	{"moduleid": 411, "menuid": 40, "module": "Other Contact Setup", "runtimefile": "Other_Contacts", "doctypeid": "Other Contact Setup", "nature": "Assets"},
	{"moduleid": 501, "menuid": 50, "module": "Purchase Order", "runtimefile": "PurchOrder", "doctypeid": "Purchase Order", "nature": "Expenses"},
	{"moduleid": 502, "menuid": 50, "module": "Purchase Invoice", "runtimefile": "PurchInvoice", "doctypeid": "Purchase Invoice", "nature": "Expenses"},
	{"moduleid": 503, "menuid": 50, "module": "Purchase Return", "runtimefile": "PurchReturn", "doctypeid": "Purchase Return", "nature": "Expenses"},
	{"moduleid": 504, "menuid": 50, "module": "Purchase Other Bill", "runtimefile": "PurchOtherBill", "doctypeid": "Purchase Other Bill", "nature": "Expenses"},
	{"moduleid": 505, "menuid": 50, "module": "Purchase Return Other Bill", "runtimefile": "PurchRetOtherBill", "doctypeid": "Purchase Return Other Bill", "nature": "Expenses"},
	{"moduleid": 506, "menuid": 50, "module": "PO Cancellation", "runtimefile": "POCancel", "doctypeid": "PO Cancellation", "nature": "Expenses"},
	{"moduleid": 507, "menuid": 50, "module": "In Out Gate Pass", "runtimefile": "GatePass", "doctypeid": "In Out Gate Pass", "nature": "Assets"},
	{"moduleid": 601, "menuid": 60, "module": "Sales Order", "runtimefile": "SalesOrder", "doctypeid": "Sales Order", "nature": "Revenue"},
	{"moduleid": 602, "menuid": 60, "module": "Sales Invoice", "runtimefile": "SalesInvoice", "doctypeid": "Sales Invoice", "nature": "Revenue"},
	{"moduleid": 603, "menuid": 60, "module": "Sales Return", "runtimefile": "SalesReturn", "doctypeid": "Sales Return", "nature": "Revenue"},
	{"moduleid": 604, "menuid": 60, "module": "Sales Other Bill", "runtimefile": "SalesOtherBill", "doctypeid": "Sales Other Bill", "nature": "Revenue"},
	{"moduleid": 605, "menuid": 60, "module": "Sales Return Other Bill", "runtimefile": "SalesRetOtherBill", "doctypeid": "Sales Return Other Bill", "nature": "Revenue"},
	{"moduleid": 606, "menuid": 60, "module": "SO Cancellation", "runtimefile": "SOCancel", "doctypeid": "SO Cancellation", "nature": "Revenue"},
	{"moduleid": 701, "menuid": 70, "module": "Opening Stock", "runtimefile": "Stock_Opening", "doctypeid": "Opening Stock", "nature": "Assets"},
	{"moduleid": 702, "menuid": 70, "module": "Closing Stock", "runtimefile": "Stock_Closing", "doctypeid": "Closing Stock", "nature": "Assets"},
	{"moduleid": 703, "menuid": 70, "module": "Stock Adjustment", "runtimefile": "Stock_Adjustment", "doctypeid": "Stock Adjustment", "nature": "Assets"},
	{"moduleid": 704, "menuid": 70, "module": "Stock Transfer Note", "runtimefile": "StockTransfer", "doctypeid": "Stock Transfer Note", "nature": "Assets"},
	{"moduleid": 801, "menuid": 80, "module": "Chart Of Accounting", "runtimefile": "ChartOfAccount", "doctypeid": "Chart of Accounting", "nature": "Assets"},
	{"moduleid": 802, "menuid": 80, "module": "Transaction Category", "runtimefile": "Transaction_Category", "doctypeid": "Transaction Category", "nature": "Assets"},
	{"moduleid": 803, "menuid": 80, "module": "Transaction List", "runtimefile": "Transaction_setup", "doctypeid": "Transaction List", "nature": "Assets"},
	{"moduleid": 804, "menuid": 80, "module": "Bank Account Information", "runtimefile": "Banks", "doctypeid": "Bank", "nature": "Assets"},
	{"moduleid": 805, "menuid": 80, "module": "Accounts Opening", "runtimefile": "GL_Opening", "doctypeid": "Accounts Opening", "nature": "Assets"},
	{"moduleid": 806, "menuid": 80, "module": "Voucher Transaction", "runtimefile": "Transaction", "doctypeid": "Voucher Transaction", "nature": "Assets"},
	{"moduleid": 807, "menuid": 80, "module": "Payment Voucher", "runtimefile": "CNBVoucher", "doctypeid": "Payment Voucher", "nature": "Assets"},
	{"moduleid": 808, "menuid": 80, "module": "Receipt Voucher", "runtimefile": "CNBVoucher", "doctypeid": "Receipt Voucher", "nature": "Assets"},
	{"moduleid": 809, "menuid": 80, "module": "Expense Voucher", "runtimefile": "CNBVoucher", "doctypeid": "Expense Voucher", "nature": "Expenses"},
	{"moduleid": 810, "menuid": 80, "module": "Party Payment Voucher", "runtimefile": "CNBPartyVoucher", "doctypeid": "Party Payment Voucher", "nature": "Assets"},
	{"moduleid": 811, "menuid": 80, "module": "Party Receipt Voucher", "runtimefile": "CNBPartyVoucher", "doctypeid": "Party Receipt Voucher", "nature": "Assets"},
	{"moduleid": 812, "menuid": 80, "module": "Purchase Invoice Payment", "runtimefile": "PNRVoucher", "doctypeid": "Purchase Invoice Payment", "nature": "Assets"},
	{"moduleid": 813, "menuid": 80, "module": "Sales Invoice Receipt", "runtimefile": "PNRVoucher", "doctypeid": "Sales Invoice Receipt", "nature": "Assets"},
	{"moduleid": 814, "menuid": 80, "module": "Broker Invoice Payment", "runtimefile": "PNRVoucher", "doctypeid": "Broker Invoice Payment", "nature": "Assets"},
	{"moduleid": 815, "menuid": 80, "module": "Advance Payment", "runtimefile": "PNRAdvance", "doctypeid": "Advance Payment", "nature": "Assets"},
	{"moduleid": 816, "menuid": 80, "module": "Advance Receipt", "runtimefile": "PNRAdvance", "doctypeid": "Advance Receipt", "nature": "Assets"},
	{"moduleid": 817, "menuid": 80, "module": "Payable Discount Note", "runtimefile": "PNRDiscount", "doctypeid": "Payable Discount Note", "nature": "Assets"},
	{"moduleid": 818, "menuid": 80, "module": "Receivable Discount Note", "runtimefile": "PNRDiscount", "doctypeid": "Receivable Discount Note", "nature": "Assets"},
	{"moduleid": 819, "menuid": 80, "module": "Paid Advance Adjustment", "runtimefile": "AdvanceAdjustment", "doctypeid": "Paid Advance Adjustment", "nature": "Assets"},
	{"moduleid": 820, "menuid": 80, "module": "Received Advance Adjustment", "runtimefile": "AdvanceAdjustment", "doctypeid": "Received Advance Adjustment", "nature": "Assets"},
	{"moduleid": 821, "menuid": 80, "module": "Party Gross Margin", "runtimefile": "Party_GM", "doctypeid": "Party Gross Margin", "nature": "Assets"},
	{"moduleid": 822, "menuid": 80, "module": "Closing and Adjustment Entries", "runtimefile": "Closing_Transaction", "doctypeid": "Closing and Adjustment Entries", "nature": "Assets"},
	{"moduleid": 823, "menuid": 80, "module": "Payment By Hawala", "runtimefile": "PaymentByHawala", "doctypeid": "Payment By Hawala", "nature": "Assets"},
	{"moduleid": 824, "menuid": 80, "module": "GL Statements", "runtimefile": "GL_Statements", "doctypeid": "GL Statements", "nature": "Assets"},
)

REPORT_MODULE_START = 9000


def report_modules() -> list[dict]:
	rows: list[dict] = []
	for idx, (legacy_id, folder) in enumerate(sorted(REPORT_FOLDER_BY_LEGACY_ID.items()), start=1):
		rows.append(
			{
				"moduleid": REPORT_MODULE_START + idx,
				"menuid": 80,
				"module": legacy_id.replace("_", " "),
				"runtimefile": f"{legacy_id}.rep",
				"doctypeid": "",
				"nature": "Assets",
				"moduletype": "R",
				"rep_allies": folder,
				"no_of_days": 30,
			}
		)
	return rows


def all_form_modules() -> list[dict]:
	return [{**row, "moduletype": "F", "rep_allies": "", "no_of_days": 0} for row in FORM_MODULES]


def all_module_rows() -> list[dict]:
	return all_form_modules() + report_modules()


def frappe_doctype_for_module(row: dict) -> str | None:
	dt = (row.get("doctypeid") or "").strip()
	return dt or None
