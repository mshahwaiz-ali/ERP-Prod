# Copyright (c) 2026, Millitrix and contributors
# Report folder name ↔ Frappe Report.name (must satisfy scrub(name) == folder).

from __future__ import annotations

import json
import re
from pathlib import Path

REPORT_ROOT = Path(__file__).resolve().parents[1] / "millitrix_erp" / "report"


def scrub(txt: str) -> str:
	return str(txt).replace(" ", "_").replace("-", "_").lower()


def folder_to_report_name(folder: str) -> str:
	return "_".join(part.capitalize() for part in folder.split("_"))


def report_name_to_folder(name: str) -> str:
	return scrub(name)


def load_report_catalog() -> dict[str, dict]:
	"""folder -> {name, json_path, py_path, js_path}."""
	catalog: dict[str, dict] = {}
	if not REPORT_ROOT.is_dir():
		return catalog
	for folder in sorted(REPORT_ROOT.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		catalog[folder.name] = {
			"name": data.get("name") or folder_to_report_name(folder.name),
			"json_path": json_path,
			"py_path": folder / f"{folder.name}.py",
			"js_path": folder / f"{folder.name}.js",
		}
	return catalog


def canonical_report_name(folder: str) -> str:
	return folder_to_report_name(folder)


def list_report_names() -> set[str]:
	return {meta["name"] for meta in load_report_catalog().values()}


# Oracle / legacy workspace ids → report folder (source of truth on disk).
REPORT_FOLDER_BY_LEGACY_ID: dict[str, str] = {
	"Trial_Balance": "trial_balance",
	"Trial_Balance_1": "trial_balance_1",
	"AccLedger": "acc_ledger",
	"GLVoucher": "gl_voucher",
	"IncomeStatement": "income_statement",
	"BalanceSheet": "balance_sheet",
	"CashBook": "cash_book",
	"BankBook": "bank_book",
	"BankLedger": "bank_ledger",
	"VoucherRegister": "voucher_register",
	"Account_Balance": "account_balance",
	"COA": "coa",
	"GJ": "gj",
	"PNL": "pnl",
	"Expanse_Register": "expanse_register",
	"CashFlow": "cash_flow",
	"CashFlowDetail": "cash_flow_detail",
	"PartyLedger": "party_ledger",
	"PartyLedgerSummary": "party_ledger_summary",
	"PartyBalance": "party_balance",
	"Party_Info": "party_info",
	"Party_Bal_Paid": "party_bal_paid",
	"PartyPRegister": "party_p_register",
	"PartyRRegister": "party_r_register",
	"Payment_Register": "payment_register",
	"Receipt_Register": "receipt_register",
	"AdvPAdjustReg": "adv_p_adjust_reg",
	"AdvRAdjustReg": "adv_r_adjust_reg",
	"AdvancePRegister": "advance_p_register",
	"AdvanceRRegister": "advance_r_register",
	"PayableDRegister": "payable_d_register",
	"ReceivableDRegister": "receivable_d_register",
	"BankStatus": "bank_status",
	"BankFinanceStatus": "bank_finance_status",
	"POPending": "po_pending",
	"PORegister": "po_register",
	"POSummary": "po_summary",
	"POInvDetail": "po_inv_detail",
	"POInvDetl": "po_inv_detail",
	"PInvRegister": "p_inv_register",
	"PIOutstanding": "pi_outstanding",
	"PISummary": "pi_summary",
	"PurchInvoice": "purch_invoice",
	"PurchInvSummary": "purch_inv_summary",
	"PurchItemSummary": "purch_item_summary",
	"PurchInvPayment": "purch_inv_payment",
	"PurchInvPayDetl": "purch_inv_pay_detl",
	"PurchInvPayDetl.rdf": "purch_inv_pay_detl",
	"DailyItemPurch": "daily_item_purch",
	"MonthlyItemPurch": "monthly_item_purch",
	"SupplierLedgerSummary": "supplier_ledger_summary",
	"SuppOrdInvDetl": "supp_ord_inv_detl",
	"SuppPayAndInv": "supp_pay_and_inv",
	"SuppInvAndPay": "supp_inv_and_pay",
	"PurchInvPayDetl_Consider": "purch_inv_pay_detl_consider",
	"BrokerInvPayment": "broker_inv_payment",
	"BrokerInvPayDetl": "broker_inv_pay_detl",
	"BrokerLedgerSummary": "broker_ledger_summary",
	"SOPending": "so_pending",
	"SORegister": "so_register",
	"SOSummary": "so_summary",
	"SOInvDetail": "so_inv_detail",
	"SInvRegister": "s_inv_register",
	"SIOutstanding": "si_outstanding",
	"SISummary": "si_summary",
	"SalesInvoice": "sales_invoice",
	"SalesInvSummary": "sales_inv_summary",
	"SalesItemSummary": "sales_item_summary",
	"SalesInvReceipt": "sales_inv_receipt",
	"SalesInvRcptDetl": "sales_inv_rcpt_detl",
	"SalesInvRcptDetl_Consider": "sales_inv_rcpt_detl_consider",
	"SIPOutstanding": "sip_outstanding",
	"DailyItemSales": "daily_item_sales",
	"MonthlyItemSales": "monthly_item_sales",
	"CustLedgerSummary": "cust_ledger_summary",
	"CustAging": "cust_aging",
	"CustOrdInvDetl": "cust_ord_inv_detl",
	"Item_Stock": "item_stock",
	"ItemLedger": "item_ledger",
	"ItemWiseStock": "item_wise_stock",
	"ItemBinCard": "item_bincard",
	"ItemDailyStock": "item_daily_stock",
	"StkRece_Summary": "stk_rece_summary",
	"TStk_Summary": "tstk_summary",
	"UnSubmit_Stock": "unsubmit_stock",
	"PartyBardana": "party_bardana",
	"PartyBardanaBincard": "party_bardana_bincard",
}


def resolve_report_name(legacy_or_name: str) -> str | None:
	folder = REPORT_FOLDER_BY_LEGACY_ID.get(legacy_or_name)
	if folder:
		catalog = load_report_catalog()
		if folder in catalog:
			return catalog[folder]["name"]
		return canonical_report_name(folder)
	if legacy_or_name in list_report_names():
		return legacy_or_name
	folder_guess = scrub(legacy_or_name)
	catalog = load_report_catalog()
	if folder_guess in catalog:
		return catalog[folder_guess]["name"]
	return None
