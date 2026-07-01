# Copyright (c) 2026, Millitrix and contributors
# Client menu: root = all sections with count badges; sidebar modules = filtered cards only.

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from millitrix.utils.client_doctype_map import client_display_name, report_display_name
from millitrix.utils.report_registry import resolve_report_name

WORKSPACE_ROOT = Path(__file__).resolve().parents[1] / "millitrix_erp" / "workspace"

Item = tuple[str, str, str]  # label, link_to, type

OBSOLETE_WORKSPACE_LABELS = (
	"Millitrix System",
	"Millitrix Supply Chain",
	"Millitrix Purchase",
	"Millitrix Sales",
	"Millitrix Stock",
	"Millitrix Accounts",
	"Millitrix HR",
	"Millitrix Reports",
	"Accounts and Finance",
	"Purchase",
)

MODULE_SEQUENCE: dict[str, float] = {
	"Millitrix": 0.0,
	"System Controls": 1.0,
	"Human Resource": 2.0,
	"Production": 3.0,
	"Supply Chain Management": 4.0,
	"Financial": 5.0,
	"Stock": 6.0,
	"Procurement": 7.0,
	"Sales": 8.0,
	"Reports": 9.0,
}

ROOT_TITLE = "Millitrix"


def _folder_slug(label: str) -> str:
	return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def _dt(doctype: str, label: str | None = None) -> Item:
	return (label or client_display_name(doctype), doctype, "DocType")


def _pg(label: str, page: str) -> Item:
	return (label, page, "Page")


def _party_setup(label: str) -> Item:
	"""Oracle All_Party split — opens filtered Party list (no redirect page)."""
	return (label, "Party", "DocType")


def _rp(report_legacy: str, label: str | None = None) -> Item | None:
	canonical = resolve_report_name(report_legacy)
	if not canonical:
		return None
	return (label or report_display_name(report_legacy), canonical, "Report")


def _pair(doctype: str, report_legacy: str | None = None, *, dt_label: str | None = None) -> list[Item]:
	"""DocType list link followed by its register report (when provided)."""
	items: list[Item] = [_dt(doctype, dt_label)]
	if report_legacy and (reg := _rp(report_legacy)):
		items.append((f"Register · {reg[0]}", reg[1], "Report"))
	return items


REPORT_CATEGORY_RULES: dict[str, tuple[str, ...]] = {
	"General Ledger": (
		"Trial_Balance", "Trial_Balance_1", "AccLedger", "GLVoucher", "IncomeStatement", "BalanceSheet",
		"CashBook", "BankBook", "BankLedger", "VoucherRegister", "Account_Balance", "COA", "GJ", "PNL",
		"Expanse_Register", "CashFlow", "CashFlowDetail",
	),
	"Party and Registers": (
		"PartyLedger", "PartyLedgerSummary", "PartyBalance", "Party_Info", "Party_Bal_Paid",
		"PartyPRegister", "PartyRRegister", "Payment_Register", "Receipt_Register",
		"AdvPAdjustReg", "AdvRAdjustReg", "AdvancePRegister", "AdvanceRRegister",
		"PayableDRegister", "ReceivableDRegister", "BankStatus", "BankFinanceStatus",
	),
	"Purchase Reports": (
		"POPending", "PORegister", "POSummary", "POInvDetail", "PInvRegister", "PIOutstanding",
		"PISummary", "PurchInvoice", "PurchInvSummary", "PurchItemSummary", "PurchInvPayment",
		"PurchInvPayDetl", "PurchInvPayDetl_Consider", "DailyItemPurch", "MonthlyItemPurch", "SupplierLedgerSummary",
		"SuppOrdInvDetl", "SuppPayAndInv", "BrokerInvPayment", "BrokerInvPayDetl", "BrokerLedgerSummary",
	),
	"Sales Reports": (
		"SOPending", "SORegister", "SOSummary", "SOInvDetail", "SInvRegister", "SIOutstanding",
		"SISummary", "SalesInvoice", "SalesInvSummary", "SalesItemSummary", "SalesInvReceipt",
		"SalesInvRcptDetl", "SalesInvRcptDetl_Consider", "SIPOutstanding", "DailyItemSales", "MonthlyItemSales",
		"SuppInvAndPay",
		"CustLedgerSummary", "CustAging", "CustOrdInvDetl",
	),
	"Stock Reports": (
		"Item_Stock", "ItemLedger", "ItemWiseStock", "ItemBinCard", "ItemDailyStock",
		"StkRece_Summary", "TStk_Summary", "UnSubmit_Stock", "PartyBardana", "PartyBardanaBincard",
		"CrashRefine",
	),
}


def _report_section(title: str, legacy_ids: tuple[str, ...]) -> dict | None:
	items = [item for rid in legacy_ids if (item := _rp(rid))]
	if not items:
		return None
	return {"title": title, "items": items}


def _report_sections(*titles: str) -> list[dict]:
	sections: list[dict] = []
	for title in titles:
		legacy_ids = REPORT_CATEGORY_RULES.get(title, ())
		section = _report_section(title, legacy_ids)
		if section:
			sections.append(section)
	return sections


REPORT_CATEGORIES = _report_sections(*REPORT_CATEGORY_RULES.keys())

# Oracle client tree — Business Management → Millitrix (root).
SYSTEM_CONTROLS_CARD = {
	"title": "System Controls",
	"items": [
		_dt("Location", "Locations"),
		_dt("User Rights", "User Management"),
		_pg("Change User Password", "change-user-password"),
		_pg("Database Backup", "database-backup"),
		_dt("Un-Submit Documents"),
		_dt("Report Parameter"),
	],
}

HR_MASTER_CARD = {
	"title": "HR Master Setups",
	"items": [
		_dt("Departments"),
		_dt("Designation"),
		_dt("Employee Category"),
		_dt("Employee Setup"),
	],
}

HR_PAYROLL_CARD = {
	"title": "Payroll",
	"items": [
		_dt("PaySlip"),
		_dt("Employee Payment Voucher", "Payment"),
		_dt("Employee Receipt Voucher", "Receipt"),
		_dt("Pay Salary Increment"),
	],
}

PRODUCTION_CARD = {
	"title": "Production",
	"items": [
		_dt("Crashing Refine", "Crashing / Refine"),
		_dt("Report Parameter"),
	],
}

SCM_MASTERS_CARD = {
	"title": "Supply Chain Master Setups",
	"items": [
		_dt("City Setup"),
		_dt("Store Types"),
		_dt("Store Setup"),
		_dt("Item Class"),
		_dt("Item Setup"),
		_dt("Item Price List"),
		_dt("Party Category"),
		_party_setup("Broker Setup"),
		_party_setup("Supplier Setup"),
		_party_setup("Customer Setup"),
		_rp("PartyBalance", "Party Balance"),
		_rp("Item_Stock", "Item Stock"),
		_dt("Other Contact Setup"),
		_dt("Report Parameter"),
	],
}

STOCK_CARD = {
	"title": "Stock",
	"items": [
		_dt("Opening Stock", "Stock Opening"),
		_dt("Closing Stock", "Stock Closing"),
		_dt("Stock Transfer Note", "Transfer Note"),
		_dt("In Out Gate Pass", "Gate Pass"),
		_dt("Stock Adjustment"),
		_pg("Report Parameter", "stock-parameter-form"),
	],
}

PROCUREMENT_CARD = {
	"title": "Procurement",
	"items": [
		_pg("Report Parameter", "purch-parameter-form"),
		*_pair("Purchase Order", "PORegister"),
		_dt("PO Cancellation", "Order Cancellation"),
		*_pair("Purchase Invoice", "PInvRegister"),
		_dt("Purchase Return"),
		_dt("Purchase Other Bill"),
		_dt("Purchase Return Other Bill"),
	],
}

SALES_CARD = {
	"title": "Sales",
	"items": [
		_pg("Report Parameter", "sales-parameter-form"),
		*_pair("Sales Order", "SORegister"),
		_dt("SO Cancellation", "Order Cancellation"),
		*_pair("Sales Invoice", "SInvRegister"),
		_dt("Sales Return"),
		_dt("Sales Other Bill"),
		_dt("Sales Return Other Bill"),
	],
}

FINANCIAL_MASTER_CARD = {
	"title": "Financial Master Setups",
	"items": [
		_pg("Chart Of Accounting", "chart-of-accounting-setup"),
		_dt("Bank", "Bank & Account"),
		_dt("Transaction Category"),
		_dt("Transaction List", "Transaction Setup"),
		_dt("GL Statements", "GL Statement"),
	],
}

RECEIVABLE_CARD = {
	"title": "Receivable",
	"items": [
		_pg("Report Parameter", "receivable-parameter-form"),
		*_pair("Sales Invoice Receipt", "SalesInvReceipt"),
		_dt("Received Advance Adjustment", "Advance Adjustment"),
		_dt("Receivable Discount Note", "Discount Note"),
		_dt("Advance Receipt"),
		*_pair("Party Receipt Voucher", "Receipt_Register", dt_label="Party Receipt"),
	],
}

PAYABLE_CARD = {
	"title": "Payable",
	"items": [
		_pg("Report Parameter", "payable-parameter-form"),
		*_pair("Purchase Invoice Payment", "PurchInvPayment"),
		_dt("Paid Advance Adjustment", "Advance Adjustment"),
		_dt("Broker Invoice Payment", "Broker Payment"),
		_dt("Payable Discount Note", "Discount Note"),
		_dt("Advance Payment"),
		*_pair("Party Payment Voucher", "Payment_Register", dt_label="Party Payment"),
		_dt("Payment By Hawala"),
	],
}

GL_CARD = {
	"title": "GL",
	"items": [
		_pg("Report Parameter", "gl-parameter-form"),
		_dt("Accounts Opening", "GL Opening"),
		*_pair("Receipt Voucher", "Receipt_Register"),
		*_pair("Payment Voucher", "Payment_Register"),
		_dt("Expense Voucher"),
		_dt("Voucher Transaction", "Voucher"),
		_dt("Party Gross Margin"),
		_dt("Closing and Adjustment Entries", "Closing Voucher"),
		_pg("Year End Closing", "year-end-closing"),
		_rp("Trial_Balance", "Trial Balance"),
	],
}

# Admin-only extras on the Millitrix home page (not in Oracle client sidebar modules).
ADMIN_EXTENDED_CARD = {
	"title": "Administration",
	"items": [
		_pg("GL Parameter Form", "gl-parameter-form"),
		_pg("Financial Parameter Form", "financial-parameter-form"),
		_dt("GL Parameter", "Mill GL Settings"),
		_dt("Mill Information"),
		_dt("Document Type"),
		_dt("Voucher Type"),
		_dt("Menu"),
		_dt("Module"),
		_dt("Document Transaction"),
		_dt("Stock In Hand"),
	],
}

QUICK_REPORTS_CARD = {
	"title": "Quick Reports",
	"items": [item for rid in (
		"Trial_Balance", "AccLedger", "PInvRegister", "SInvRegister",
		"POPending", "SOPending", "PartyBalance", "Payment_Register",
	) if (item := _rp(rid))],
}

# Top shortcuts per sidebar module (Frappe workspace bar).
WORKSPACE_SHORTCUTS: dict[str, list[dict]] = {
	"Millitrix": [
		{"label": "Purchase Invoice", "link_to": "Purchase Invoice", "type": "DocType", "doc_view": "New"},
		{"label": "Sales Invoice", "link_to": "Sales Invoice", "type": "DocType", "doc_view": "New"},
		{"label": "Crashing / Refine", "link_to": "Crashing Refine", "type": "DocType", "doc_view": "New"},
		{"label": "Trial Balance", "link_to": "Trial_Balance", "type": "Report"},
	],
	"System Controls": [
		{"label": "Locations", "link_to": "Location", "type": "DocType"},
		{"label": "User Management", "link_to": "User Rights", "type": "DocType"},
		{"label": "Change User Password", "link_to": "change-user-password", "type": "Page"},
		{"label": "Un-Submit Documents", "link_to": "Un-Submit Documents", "type": "DocType", "doc_view": "New"},
	],
	"Human Resource": [
		{"label": "Employee Setup", "link_to": "Employee Setup", "type": "DocType", "doc_view": "New"},
		{"label": "PaySlip", "link_to": "PaySlip", "type": "DocType", "doc_view": "New"},
		{"label": "Payment", "link_to": "Employee Payment Voucher", "type": "DocType", "doc_view": "New"},
		{"label": "Receipt", "link_to": "Employee Receipt Voucher", "type": "DocType", "doc_view": "New"},
	],
	"Production": [
		{"label": "Crashing / Refine", "link_to": "Crashing Refine", "type": "DocType", "doc_view": "New"},
	],
	"Supply Chain Management": [
		{"label": "Item Setup", "link_to": "Item Setup", "type": "DocType", "doc_view": "New"},
		{"label": "Item Price List", "link_to": "Item Price List", "type": "DocType", "doc_view": "New"},
		{"label": "Store Setup", "link_to": "Store Setup", "type": "DocType", "doc_view": "New"},
		{"label": "Supplier Setup", "link_to": "Party", "type": "DocType"},
	],
	"Financial": [
		{"label": "Chart Of Accounting", "link_to": "chart-of-accounting-setup", "type": "Page"},
		{"label": "GL Opening", "link_to": "Accounts Opening", "type": "DocType", "doc_view": "New"},
		{"label": "Payment Voucher", "link_to": "Payment Voucher", "type": "DocType", "doc_view": "New"},
		{"label": "Receipt Voucher", "link_to": "Receipt Voucher", "type": "DocType", "doc_view": "New"},
		{"label": "Trial Balance", "link_to": "Trial_Balance", "type": "Report"},
	],
	"Stock": [
		{"label": "Gate Pass", "link_to": "In Out Gate Pass", "type": "DocType", "doc_view": "New"},
		{"label": "Transfer Note", "link_to": "Stock Transfer Note", "type": "DocType", "doc_view": "New"},
		{"label": "Stock Adjustment", "link_to": "Stock Adjustment", "type": "DocType", "doc_view": "New"},
		{"label": "Item Stock", "link_to": "Item_Stock", "type": "Report"},
	],
	"Procurement": [
		{"label": "Purchase Order", "link_to": "Purchase Order", "type": "DocType", "doc_view": "New"},
		{"label": "Purchase Invoice", "link_to": "Purchase Invoice", "type": "DocType", "doc_view": "New"},
		{"label": "PO Pending", "link_to": "Po_Pending", "type": "Report"},
	],
	"Sales": [
		{"label": "Sales Order", "link_to": "Sales Order", "type": "DocType", "doc_view": "New"},
		{"label": "Sales Invoice", "link_to": "Sales Invoice", "type": "DocType", "doc_view": "New"},
		{"label": "SO Pending", "link_to": "So_Pending", "type": "Report"},
	],
	"Reports": [
		{"label": "Trial Balance", "link_to": "Trial_Balance", "type": "Report"},
		{"label": "Account Ledger", "link_to": "Acc_Ledger", "type": "Report"},
		{"label": "Purchase Invoice Register", "link_to": "P_Inv_Register", "type": "Report"},
		{"label": "Sales Invoice Register", "link_to": "S_Inv_Register", "type": "Report"},
	],
}

# Millitrix home = full Oracle tree + admin extras + all reports.
ROOT_CARDS: list[dict] = [
	SYSTEM_CONTROLS_CARD,
	HR_MASTER_CARD,
	HR_PAYROLL_CARD,
	PRODUCTION_CARD,
	SCM_MASTERS_CARD,
	FINANCIAL_MASTER_CARD,
	RECEIVABLE_CARD,
	PAYABLE_CARD,
	GL_CARD,
	STOCK_CARD,
	PROCUREMENT_CARD,
	SALES_CARD,
	QUICK_REPORTS_CARD,
	ADMIN_EXTENDED_CARD,
] + REPORT_CATEGORIES

CHILD_WORKSPACES: dict[str, dict] = {
	"System Controls": {
		"title": "System Controls",
		"icon": "setting",
		"cards": [SYSTEM_CONTROLS_CARD],
	},
	"Human Resource": {
		"title": "Human Resource",
		"icon": "hr",
		"cards": [HR_MASTER_CARD, HR_PAYROLL_CARD],
	},
	"Production": {
		"title": "Production",
		"icon": "retail",
		"cards": [PRODUCTION_CARD],
	},
	"Supply Chain Management": {
		"title": "Supply Chain Management",
		"icon": "stock",
		"cards": [SCM_MASTERS_CARD],
	},
	"Financial": {
		"title": "Financial",
		"icon": "accounting",
		"cards": [FINANCIAL_MASTER_CARD, RECEIVABLE_CARD, PAYABLE_CARD, GL_CARD, QUICK_REPORTS_CARD]
		+ _report_sections("General Ledger", "Party and Registers"),
	},
	"Stock": {
		"title": "Stock",
		"icon": "inventory",
		"cards": [STOCK_CARD, QUICK_REPORTS_CARD] + _report_sections("Stock Reports"),
	},
	"Procurement": {
		"title": "Procurement",
		"icon": "buying",
		"cards": [PROCUREMENT_CARD, QUICK_REPORTS_CARD] + _report_sections("Purchase Reports"),
	},
	"Sales": {
		"title": "Sales",
		"icon": "sell",
		"cards": [SALES_CARD, QUICK_REPORTS_CARD] + _report_sections("Sales Reports"),
	},
	"Reports": {
		"title": "Reports",
		"icon": "report",
		"cards": REPORT_CATEGORIES,
	},
}


def _block(block_id: str, block_type: str, data: dict) -> dict:
	return {"id": block_id, "type": block_type, "data": data}


def build_content(cards: list[dict]) -> str:
	blocks: list[dict] = []
	seen_titles: set[str] = set()
	if cards:
		blocks.append(_block("hdr_cards", "header", {"text": '<span class="h4"><b>Modules</b></span>', "col": 12}))
		for i, section in enumerate(cards):
			if section.get("items"):
				title = section["title"]
				if title in seen_titles:
					raise ValueError(f"Duplicate workspace card title: {title!r}")
				seen_titles.add(title)
				blocks.append(_block(f"card_{i}", "card", {"card_name": title, "col": 4}))
	return json.dumps(blocks)


def build_links(cards: list[dict]) -> list[dict]:
	links: list[dict] = []
	for section in cards:
		items = section.get("items", [])
		if not items:
			continue
		links.append(
			{
				"hidden": 0,
				"is_query_report": 0,
				"label": section["title"],
				"link_count": len(items),
				"link_type": "DocType",
				"onboard": 0,
				"type": "Card Break",
			}
		)
		for label, link_to, link_type in items:
			links.append(
				{
					"hidden": 0,
					"is_query_report": 1 if link_type == "Report" else 0,
					"label": label,
					"link_count": 0,
					"link_to": link_to,
					"link_type": link_type,
					"onboard": 0,
					"type": "Link",
				}
			)
	return links


def build_workspace_doc(
	label: str,
	title: str,
	icon: str,
	parent_page: str,
	cards: list[dict],
	*,
	sequence_id: float | None = None,
	shortcuts: list[dict] | None = None,
) -> dict:
	return {
		"charts": [],
		"content": build_content(cards),
		"custom_blocks": [],
		"docstatus": 0,
		"doctype": "Workspace",
		"for_user": "",
		"hide_custom": 0,
		"icon": icon,
		"idx": 0,
		"is_hidden": 0,
		"label": label,
		"links": build_links(cards),
		"modified": "2026-06-14 22:00:00.000000",
		"modified_by": "Administrator",
		"module": "Millitrix ERP",
		"name": label,
		"owner": "Administrator",
		"parent_page": parent_page,
		"public": 1,
		"restrict_to_domain": "",
		"roles": [],
		"sequence_id": sequence_id if sequence_id is not None else MODULE_SEQUENCE.get(label, 1.0),
		"shortcuts": shortcuts if shortcuts is not None else WORKSPACE_SHORTCUTS.get(label, []),
		"title": title,
	}


def _remove_obsolete_workspace_files() -> None:
	if not WORKSPACE_ROOT.is_dir():
		return
	keep_slugs = {_folder_slug("Millitrix")}
	keep_slugs.update(_folder_slug(label) for label in CHILD_WORKSPACES)
	for child in WORKSPACE_ROOT.iterdir():
		if not child.is_dir():
			continue
		if child.name not in keep_slugs:
			shutil.rmtree(child, ignore_errors=True)


def write_all() -> None:
	_remove_obsolete_workspace_files()

	root = build_workspace_doc(
		label="Millitrix",
		title=ROOT_TITLE,
		icon="organization",
		parent_page="",
		cards=ROOT_CARDS,
		sequence_id=MODULE_SEQUENCE["Millitrix"],
	)
	folder = WORKSPACE_ROOT / "millitrix"
	folder.mkdir(parents=True, exist_ok=True)
	(folder / "millitrix.json").write_text(json.dumps(root, indent=1) + "\n", encoding="utf-8")
	print("wrote", folder / "millitrix.json")

	for label, spec in CHILD_WORKSPACES.items():
		doc = build_workspace_doc(
			label=label,
			title=spec.get("title", label),
			icon=spec.get("icon", "folder-normal"),
			parent_page=ROOT_TITLE,
			cards=spec.get("cards", []),
			sequence_id=MODULE_SEQUENCE.get(label, 1.0),
		)
		child_folder = WORKSPACE_ROOT / _folder_slug(label)
		child_folder.mkdir(parents=True, exist_ok=True)
		path = child_folder / f"{_folder_slug(label)}.json"
		path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
		print("wrote", path)


if __name__ == "__main__":
	write_all()
