# Apply full-word Select options + grid columns — run: python apps/millitrix/millitrix/patches/apply_ui_field_options.py
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

POSTED = {
	"options": "Draft\nSubmitted",
	"default": "Draft",
	"label": "Submitted",
	"hidden": 1,
	"read_only": 1,
	"reqd": 0,
}
YES_NO = {"options": "No\nYes", "default": "No"}
ACTIVE = {"options": "Inactive\nActive", "default": "Active", "label": "Active Status"}
NATURE = {"options": "Assets\nLiabilities\nCapital\nRevenue\nExpenses"}
TRANSFLAG = {"options": "No\nYes", "default": "Yes", "label": "Transaction"}
MUND_ITEM = {"options": "Old Mund\nNew Mund\nQuantity", "default": "New Mund"}
ORDER_STATUS = {"options": "Initial\nIn Progress\nComplete\nCancelled", "default": "Initial", "fieldtype": "Select"}
ORDER_TYPE = {"options": "Main Order\nSub Order", "default": "Main Order", "fieldtype": "Select"}
GATE_TYPE = {"options": "In\nOut", "default": "In", "fieldtype": "Select"}
AMNT_BY = {"options": "Mund\nBag Quantity", "default": "Mund"}
KANTA = {"options": "Total Weight\nIn Kanta\nDelivery Kanta", "default": "Total Weight"}
KANTA_SALES = {
	"options": "Total Weight\nDelivery Kanta",
	"default": "Delivery Kanta",
	"fieldtype": "Select",
}
KANTA_SALES_RETURN = {
	"options": "Total Weight\nIn Kanta\nDelivery Kanta",
	"default": "Total Weight",
	"fieldtype": "Select",
}
KANTA_RETURN = {
	"options": "Total Weight\nDelivery Kanta",
	"default": "Delivery Kanta",
	"fieldtype": "Select",
}
BROKERY = {"options": "Not Paid\nPaid", "default": "Not Paid"}
BORROW = {"options": "Delivery\nX Delivery"}
BAGS_PURCHASE = {"options": "Our\nParty\nPurchase Bardana", "default": "Our", "fieldtype": "Select"}
BAGS_SALES = {"options": "Our\nParty\nSales Bardana", "default": "Our", "fieldtype": "Select"}
BAGS_ALL = {"options": "Our\nParty\nPurchase Bardana\nSales Bardana", "default": "Our", "fieldtype": "Select"}
EMPTY_BAGS = {"options": "No\nYes", "default": "No", "fieldtype": "Select"}
PAY_MODE = {"options": "Cash\nCheque\nBank\nTravellers Cheque", "fieldtype": "Select"}
BANK_NATURE = {
	"options": "Cash Finance Account\nRunning Finance Account\nFM Finance Account",
	"fieldtype": "Select",
}
BROKERY_BASIS = {"options": "Mund\nBag\nQuantity\nTruck\nPercent", "fieldtype": "Select"}
USER_LEVEL = {"options": "Level 1\nLevel 2\nLevel 3\nLevel 4\nLevel 5", "fieldtype": "Select", "default": "Level 1"}

PERM_CHECK = {"fieldtype": "Check", "default": "0", "in_list_view": 1}
PERM_CHECK_VIEW = {**PERM_CHECK, "default": "1"}

GLOBAL_FIELD_PATCHES = {
	"posted": POSTED,
	"transflag": TRANSFLAG,
	"nature": NATURE,
	"stockable": YES_NO,
	"brokery_auto_calc": {"fieldtype": "Check", "default": "1"},
	"brokery_dr_supplier": {"fieldtype": "Check", "default": "0"},
	"emptybags": EMPTY_BAGS,
	"amntby": AMNT_BY,
	"kantatype": KANTA,
	"brokery": BROKERY,
	"borrow": BORROW,
	"pnrmode": PAY_MODE,
	"vouchmode": PAY_MODE,
	"pgmode": PAY_MODE,
	"gmmode": PAY_MODE,
	"amount_by": {**AMNT_BY, "fieldtype": "Select"},
	"activestatus": ACTIVE,
	"payslip": YES_NO,
	"resaccess": {**YES_NO, "label": "Restrict Report Access"},
	"default_store": {**YES_NO, "label": "Default Store"},
}

DOCTYPE_FIELD_PATCHES: dict[str, dict[str, dict]] = {
	"Item Setup": {"mundtype": MUND_ITEM},
	"Chart of Accounting": {"nature": NATURE, "transflag": TRANSFLAG},
	"Payment By Hawala": {
		"gmmode": {
			"options": "GL Code\nParty Code\nTransaction Code",
			"default": "GL Code",
			"label": "Mode",
			"fieldtype": "Select",
		},
		"b_gmmode": {
			"options": "GL Code\nParty Code\nTransaction Code",
			"default": "GL Code",
			"label": "Mode",
			"fieldtype": "Select",
		},
	},
	"Hawala Party B": {
		"gmmode": {
			"options": "GL Code\nParty Code\nTransaction Code",
			"default": "GL Code",
			"label": "Mode",
			"fieldtype": "Select",
		},
	},
	"Bank Account": {"ac_nature": BANK_NATURE},
	"Purchase Order": {"status": ORDER_STATUS, "potype": ORDER_TYPE},
	"Sales Order": {"status": ORDER_STATUS, "sotype": ORDER_TYPE},
	"In Out Gate Pass": {
		"gptype": GATE_TYPE,
		"kantatype": {**KANTA, "fieldtype": "Select"},
		"amount_by": {**AMNT_BY, "fieldtype": "Select"},
		"posted": POSTED,
	},
	"Stock Transfer Note": {"kantatype": KANTA_SALES},
	"Purchase Invoice Detail": {"bags_are": BAGS_PURCHASE},
	"Sales Invoice Detail": {"bags_are": BAGS_SALES},
	"Purchase Return Detail": {"bags_are": BAGS_PURCHASE},
	"Sales Return Detail": {"bags_are": BAGS_SALES},
	"Purchase Return": {"status": ORDER_STATUS, "potype": ORDER_TYPE, "kantatype": KANTA_RETURN},
	"Sales Return": {"status": ORDER_STATUS, "sotype": ORDER_TYPE, "kantatype": KANTA_SALES_RETURN},
	"Sales Invoice": {"kantatype": KANTA_SALES},
	"Gate Pass Detail": {"bags_are": BAGS_ALL},
	"Stock Transfer Detail": {"bags_are": BAGS_ALL},
	"Opening Stock Detail": {"bags_are": BAGS_ALL},
	"Stock Adjustment Detail": {"bags_are": BAGS_ALL},
	"Stock In Hand": {"bags_are": BAGS_ALL},
	"Party Item": {
		"value_type_1": BROKERY_BASIS,
		"value_type_2": BROKERY_BASIS,
	},
	"Module Permission": {
		"canview": PERM_CHECK_VIEW,
		"canadd": PERM_CHECK,
		"canedit": PERM_CHECK,
		"candelete": PERM_CHECK,
		"cansubmit": PERM_CHECK,
		"canassign": PERM_CHECK,
		"canunsubmit": PERM_CHECK,
		"resaccess": {**PERM_CHECK, "label": "Restrict Report Access"},
		"user_level": USER_LEVEL,
		"moduleid": {"in_list_view": 1},
	},
	"User Store": {
		"resaccess": {**YES_NO, "label": "Restrict Access", "in_list_view": 1},
		"default_store": {**YES_NO, "label": "Default Store", "in_list_view": 1},
	},
	"Store Setup": {"stockable": YES_NO, "trans_allow": YES_NO},
	"GL Statements": {"active": YES_NO, "operation": {"options": "Add\nSubtract", "default": "Add"}},
	"GL Sub Statement": {"active": YES_NO, "operation": {"options": "Add\nSubtract", "default": "Add"}},
}

IN_LIST_VIEW: dict[str, list[str]] = {
	"Purchase Invoice Detail": [
		"ponumber", "biltyno", "truckno", "storeid", "bagqty",
		"netweight", "mund", "rate", "discount", "totalamnt", "brokeramnt", "labouramnt",
		"cartage", "transporter",
	],
	"Sales Invoice Detail": [
		"sonumber", "biltyno", "truckno", "storeid", "bagqty",
		"netweight", "mund", "rate", "discount", "totalamnt", "brokeramnt", "labouramnt",
		"cartage", "transporter",
	],
	"Purchase Return Detail": [
		"pidetlno", "ponumber", "biltyno", "truckno", "truckqty", "cartage", "storeid",
		"emptybags", "bagid", "bagqty",
	],
	"Sales Return Detail": [
		"sidetlno", "sonumber", "biltyno", "truckno", "truckqty", "cartage", "storeid",
		"bags_are", "bagid", "bagqty",
	],
	"Gate Pass Detail": [
		"biltyno", "truckno", "truckqty", "storeid", "emptybags", "bagid", "bagqty", "bags_are",
		"bagweight", "total_weight",
	],
	"Stock Transfer Detail": [
		"truckno", "truckqty", "cartage", "tostoreid", "emptybags", "bagid", "bagqty", "bagweight",
		"total_weight", "delikanta",
	],
	"Opening Stock Detail": [
		"storeid", "itemcode", "bagitemcode", "partyid",
	],
	"Stock Adjustment Detail": [
		"storeid", "itemcode", "bagitemcode", "partyid",
	],
	"Purchase Other Bill Detail": [
		"itemcode", "quantity", "rate", "amount", "storeid",
	],
	"Sales Other Bill Detail": [
		"itemcode", "quantity", "rate", "amount", "storeid",
	],
	"Voucher Transaction Detail": [
		"accid", "debit", "credit", "detail",
	],
	"Payment and Receipt Document": [
		"documentid", "party_name", "item_name", "docbalamnt", "amount", "suspense", "balance",
	],
	"Payment and Receipt Instrument": [
		"pnrmode", "bankaccid", "referno", "referdate", "amount",
	],
	"Cash and Bank Voucher Document": [
		"partyid", "documentid", "docbalamnt", "amount", "balance",
	],
	"Cash and Bank Voucher Detail": [
		"accid", "amount", "detail",
	],
	"Expense Voucher Detail": [
		"trans_id", "transaction_description", "amount", "detail", "mill_id",
	],
	"Party Item": [
		"itemcode", "value_type_1", "value_1", "value_type_2", "value_2",
	],
	"Module Permission": [
		"moduleid", "module_name", "user_level", "canview", "canadd", "canedit", "candelete",
		"cansubmit", "canassign", "canunsubmit",
	],
	"Adjustment Invoice": [
		"documentid", "party_name", "item_name", "docbalamnt", "amount", "suspense",
	],
	"Adjustment PNR": [
		"pnrno", "pnrdate", "pnrmode", "accid", "referno", "docbalamnt", "amount",
	],
	"PaySlip Detail": ["empno", "amount"],
	"PO Cancellation Detail": ["ponumber", "itemcode", "truckqty", "cancelqty", "rate"],
	"SO Cancellation Detail": ["sonumber", "itemname", "truckqty", "cancelqty", "rate"],
	"Party Gross Margin Invoice": ["doctypeid", "documentid", "docbalamnt", "amount", "suspense"],
	"Party Gross Margin Party B": [
		"partyid", "itemcode", "accid", "trans_id", "gmmode", "amount", "referno",
	],
	"Hawala Invoice": ["documentid", "docbalamnt", "amount", "suspense"],
	"Hawala Party B": [
		"partyid", "itemcode", "accid", "gmmode", "referno", "referdate", "amount",
	],
	"Accounts Opening Detail": [
		"accid", "debit", "credit",
	],
	"Salary Increment Detail": ["empno", "amount"],
	"Purchase Other Bill Return Detail": [
		"pbdetlno", "quantity", "rate", "amount", "storeid",
	],
	"Sales Other Bill Return Detail": [
		"sbdetlno", "quantity", "rate", "amount", "storeid",
	],
	"Crash Refine Input": [
		"storeid", "critem", "crbagid", "bagqty", "bagweight", "total_weight",
		"bagdust", "ref_bags", "ref_weight", "dip", "prod_1", "prod_2",
	],
	"Crash Refine Output": ["proditem", "weight", "storeid", "rate"],
	"Bank Branch": ["branchid", "description", "address", "phno1", "phno2", "contact"],
	"Bank Account": [
		"bankaccid", "accid", "ac_nature", "amntlimit", "location_id",
	],
	"GL Sub Statement": [
		"note", "description", "operation", "active", "statement_type",
	],
	"GL Statement Account": ["accid", "show_side"],
	"User Location": ["location_id"],
	"User Store": ["storeid", "resaccess", "default_store"],
}

EDITABLE_GRID_PARENTS = {
	"Purchase Invoice",
	"Sales Invoice",
	"In Out Gate Pass",
	"Stock Transfer Note",
	"Opening Stock",
	"Closing Stock",
	"Stock Adjustment",
	"Purchase Return",
	"Sales Return",
	"Purchase Other Bill",
	"Sales Other Bill",
	"Purchase Return Other Bill",
	"Sales Return Other Bill",
	"Voucher Transaction",
	"Payment and Receipt Voucher",
	"Cash and Bank Voucher",
	"Advance Adjustment",
	"Accounts Opening",
	"Closing and Adjustment Entries",
	"Employee Payment Voucher",
	"Employee Receipt Voucher",
	"Crashing Refine",
	"Party",
	"User Rights",
	"Bank",
	"PaySlip",
	"GL Statements",
	"Party Gross Margin",
	"Pay Salary Increment",
	"Payment By Hawala",
	"PO Cancellation",
	"SO Cancellation",
}

LAYOUT_FIELDTYPES = {
	"Section Break",
	"Column Break",
	"Tab Break",
	"HTML",
	"Button",
	"Table",
	"Fold",
	"Heading",
}


def _patch_field(field: dict, patch: dict) -> None:
	for key, val in patch.items():
		field[key] = val
	if field.get("fieldname") in ("nature", "transflag", "mundtype"):
		field.pop("description", None)


def apply() -> None:
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		doctype = data.get("name") or folder.name.replace("_", " ").title()
		changed = False
		grid_cols = set(IN_LIST_VIEW.get(doctype, []))
		specific = DOCTYPE_FIELD_PATCHES.get(doctype, {})
		has_table = any(f.get("fieldtype") == "Table" for f in data.get("fields", []))
		if doctype in EDITABLE_GRID_PARENTS or has_table:
			data["editable_grid"] = 1
			changed = True
		for field in data.get("fields", []):
			fname = field.get("fieldname")
			if fname in GLOBAL_FIELD_PATCHES:
				_patch_field(field, GLOBAL_FIELD_PATCHES[fname])
				changed = True
			if fname in specific:
				_patch_field(field, specific[fname])
				changed = True
			if doctype in IN_LIST_VIEW and fname:
				if fname in grid_cols:
					if not field.get("in_list_view"):
						field["in_list_view"] = 1
						changed = True
					if field.get("columns") != 1:
						field["columns"] = 1
						changed = True
				elif field.get("hidden") and field.get("in_list_view"):
					field["in_list_view"] = 0
					changed = True
				elif (
					not field.get("hidden")
					and field.get("fieldtype") not in LAYOUT_FIELDTYPES
					and field.get("in_list_view")
				):
					field["in_list_view"] = 0
					changed = True
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			print("updated", doctype)


if __name__ == "__main__":
	apply()
