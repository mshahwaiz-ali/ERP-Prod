# Blueprint.md field rules — mandatory, read-only, hidden, link options.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

# Client screenshots omit Location on finance / GL screens — stored from user session (Oracle LOCATION_ID in DB).
LOCATION_UI_HIDDEN_DOCTYPES = frozenset(
	{
		"Advance PNR",
		"Advance Payment",
		"Advance Receipt",
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
		"Employee Payment Voucher",
		"Employee Receipt Voucher",
		"Paid Advance Adjustment",
		"Received Advance Adjustment",
		"Payment By Hawala",
		"Party Gross Margin",
		"Accounts Opening",
		"Opening Stock",
		"Closing Stock",
		"Crashing Refine",
		"Closing and Adjustment Entries",
		"Voucher Transaction",
		"Un-Submit Documents",
		"PaySlip",
		"Payment and Receipt Voucher",
		"Cash and Bank Voucher",
		"Advance Adjustment",
		"PO Cancellation",
		"SO Cancellation",
		"Purchase Invoice",
		"Sales Invoice",
		"Purchase Order",
		"Sales Order",
		"Purchase Return",
		"Sales Return",
		"Purchase Other Bill",
		"Purchase Return Other Bill",
		"Sales Other Bill",
		"Sales Return Other Bill",
		"Stock Adjustment",
		"Stock Transfer Note",
		"In Out Gate Pass",
		"Item Price List",
	}
)

# Internal / system fields — always hidden from client UI.
HIDDEN_FIELDS: dict[str, list[str]] = {
	# posted = legacy Oracle POSTED flag; Frappe docstatus + Submit button handle lifecycle.
	"*": ["doctypeid", "posted"],
	"Payment and Receipt Voucher": ["pnr_type"],
	"Advance Payment": ["instruments"],
	"Advance Receipt": ["instruments"],
	"Advance PNR": ["instruments"],
	"Purchase Invoice Payment": ["balance", "bankaccid", "referno", "referdate", "pnrmode", "amount"],
	"Sales Invoice Receipt": ["balance", "bankaccid", "referno", "referdate", "pnrmode", "amount"],
	"Broker Invoice Payment": ["balance", "bankaccid", "referno", "referdate", "pnrmode", "amount"],
	"Closing and Adjustment Entries": [
		"vouchertype_id",
		"documentid",
		"instrument",
		"referdate",
	],
	"Purchase Return": ["brokerypayable", "brokeramnt", "mundtype"],
	"Sales Return": ["brokerypayable", "brokeramnt"],
	"Purchase Other Bill": ["amount"],
	"Purchase Return Other Bill": ["amount"],
	"Sales Return Other Bill": ["amount"],
}

# Remove from DocType JSON entirely — not on Oracle UI and not needed in schema.
REMOVED_FIELDS: dict[str, list[str]] = {
	"Payable Discount Note": ["bankaccid", "pnrmode", "balance"],
	"Receivable Discount Note": ["bankaccid", "pnrmode", "balance"],
	"Payment Voucher": ["documents", "vouchmode"],
	"Receipt Voucher": ["documents", "vouchmode"],
	"Expense Voucher": ["documents", "vouchmode"],
	"Party Payment Voucher": ["details", "vouchmode"],
	"Party Receipt Voucher": ["details", "vouchmode"],
	"Employee Payment Voucher": ["details", "vouchmode"],
	"Employee Receipt Voucher": ["details", "vouchmode"],
	"Payment By Hawala": ["trans_id", "instrument"],
	"Purchase Return Detail": ["discount", "truckadv"],
	"Sales Return Detail": ["truckadv"],
	"Purchase Invoice Detail": ["emptybags"],
	"Hawala Party B": ["gmdetlid", "trans_id", "instrument"],
}


def removed_for(doctype: str, fieldname: str) -> bool:
	if fieldname in REMOVED_FIELDS.get("*", []):
		return True
	return fieldname in REMOVED_FIELDS.get(doctype, [])

# Calculated totals — read-only (blueprint Sections 5–7).
READ_ONLY_FIELDS: dict[str, list[str]] = {
	"Purchase Order": ["amount", "payable", "truckreceived", "weightreceived", "truckqtycancel"],
	"Sales Order": ["amount", "receivable", "truckissued", "weightissued", "truckqtycancel"],
	"Purchase Invoice": ["amount", "payable", "brokerypayable", "brokeramnt"],
	"Sales Invoice": ["amount", "receivable", "brokerypayable", "brokeramnt"],
	"Purchase Return": ["amount", "receivable", "brokerypayable", "brokeramnt"],
	"Sales Return": ["amount", "payable", "brokerypayable", "brokeramnt"],
	"Purchase Invoice Detail": [
		"total_weight", "mund", "brokery_mund", "bagamnt", "bardana", "netweight", "totalamnt", "order_rate",
	],
	"Sales Invoice Detail": [
		"total_weight", "mund", "bagamnt", "bardana", "netweight", "totalamnt", "order_rate",
	],
	"Purchase Return Detail": [
		"total_weight", "mund", "brokery_mund", "bagamnt", "bardana", "netweight", "totalamnt", "order_rate",
	],
	"Sales Return Detail": ["total_weight", "mund", "bagamnt", "bardana", "netweight", "totalamnt", "brokeramnt", "order_rate"],
	"Sales Other Bill Return Detail": ["item_name", "rate", "amount", "storeid"],
	"Gate Pass Detail": ["netweight", "total_weight", "totalamnt", "brokeramnt"],
	"Stock Transfer Detail": ["total_weight", "netweight", "totalamnt"],
	"Stock Adjustment Detail": [
		"store_name", "item_name", "filled_item_name", "party_name",
		"current_stock", "adjusted_stock", "amount",
	],
	"Payment and Receipt Voucher": ["amount", "balance"],
	"Payment and Receipt Document": ["party_name", "item_name", "docbalamnt", "balance"],
	"Payment and Receipt Instrument": ["balance"],
	"Cash and Bank Voucher Document": ["party_name", "docbalamnt", "balance"],
	"Cash and Bank Voucher Detail": ["balance"],
	"Purchase Invoice Payment": ["amount", "balance"],
	"Sales Invoice Receipt": ["amount", "balance"],
	"Broker Invoice Payment": ["amount", "balance"],
	"Payable Discount Note": ["amount", "balance"],
	"Receivable Discount Note": ["amount", "balance"],
	"Advance Payment": ["balance"],
	"Advance Receipt": ["balance"],
	"Advance PNR": ["balance"],
	"Advance Adjustment": ["amount"],
	"Paid Advance Adjustment": ["amount"],
	"Received Advance Adjustment": ["amount"],
	"Accounts Opening": ["total_debit", "total_credit"],
	"Closing and Adjustment Entries": ["total_debit", "total_credit"],
	"Closing Stock": ["total_stock"],
	"Cash and Bank Voucher": ["amount"],
	"Payment Voucher": ["amount"],
	"Receipt Voucher": ["amount"],
	"Expense Voucher": ["amount"],
	"Party Payment Voucher": ["amount"],
	"Party Receipt Voucher": ["amount"],
	"Employee Payment Voucher": ["amount"],
	"Employee Receipt Voucher": ["amount"],
	"PaySlip Detail": ["balance"],
	"Purchase Other Bill": ["amount"],
	"Sales Other Bill": ["amount"],
	"Purchase Other Bill Detail": ["item_name", "amount"],
	"Sales Other Bill Detail": ["item_name", "amount"],
	"Purchase Other Bill Return Detail": ["item_name", "rate", "amount"],
	"Party Gross Margin": ["amount"],
	"Party Gross Margin Invoice": ["docbalamnt", "party_name", "item_name"],
	"Party Gross Margin Party B": ["party_name"],
	"Adjustment Invoice": ["party_name", "item_name", "docbalamnt"],
	"Adjustment PNR": ["balance"],
	"Hawala Invoice": ["party_name"],
	"Hawala Party B": ["party_name"],
	"Salary Increment Detail": ["employee_name", "balance"],
	"Crash Refine Input": [
		"item_name", "total_weight", "ref_bags", "ref_weight", "prod_1", "prod_2",
	],
	"Crash Refine Output": ["item_name", "weight", "storeid"],
}

# Required header fields per client form (blueprint).
MANDATORY_FIELDS: dict[str, list[str]] = {
	"Purchase Order": [
		"podate", "supplierid", "brokerid", "itemcode",
	],
	"Sales Order": [
		"sodate", "customerid", "brokerid", "itemcode",
	],
	"Purchase Invoice": [
		"location_id", "invdate", "supplierid", "brokerid", "itemcode",
	],
	"Sales Invoice": [
		"location_id", "invdate", "customerid", "brokerid", "itemcode",
	],
	"PO Cancellation": ["partyid", "candate"],
	"SO Cancellation": ["partyid", "candate"],
	"Purchase Return": ["retdate", "purchinvno"],
	"Sales Return": ["location_id", "retdate", "salesinvno"],
	"Opening Stock": ["location_id", "opendate"],
	"Closing Stock": ["location_id", "opendate"],
	"Un-Submit Documents": ["usdate", "usdoctype", "documentid"],
	"Stock Adjustment": ["location_id", "sadate"],
	"Stock Transfer Note": ["location_id", "tdate", "fromstoreid", "itemcode"],
	"In Out Gate Pass": ["location_id", "gpdate", "partyid", "itemcode"],
	"Crashing Refine": ["crdate", "mill_id"],
	"Advance Payment": ["pnrdate", "partyid", "pnrmode", "amount"],
	"Advance Receipt": ["pnrdate", "partyid", "pnrmode", "amount"],
	"Advance PNR": ["pnrdate", "partyid", "pnrmode", "amount"],
	"Purchase Invoice Payment": ["pnrdate", "partyid"],
	"Sales Invoice Receipt": ["pnrdate", "partyid"],
	"Broker Invoice Payment": ["pnrdate", "partyid"],
	"Payable Discount Note": ["pnrdate", "partyid"],
	"Receivable Discount Note": ["pnrdate", "partyid"],
	"Payment Voucher": ["vouchdate", "paymode"],
	"Receipt Voucher": ["vouchdate", "paymode"],
	"Expense Voucher": ["vouchdate", "paymode"],
	"Party Payment Voucher": ["vouchdate", "partyid", "paymode"],
	"Party Receipt Voucher": ["vouchdate", "partyid", "paymode"],
	"Employee Payment Voucher": ["vouchdate", "paymode"],
	"Employee Receipt Voucher": ["vouchdate", "paymode"],
	"Paid Advance Adjustment": ["partyid", "adjdate"],
	"Received Advance Adjustment": ["partyid", "adjdate"],
	"Accounts Opening": ["opening_date"],
	"Voucher Transaction": ["vouchdate"],
	"Party": ["partyid", "name", "pcat_id"],
	"Other Contact Setup": ["name", "cityid", "pcat_id"],
	"Item Setup": ["itemcode", "itemname"],
	"Store Setup": ["storeid", "location_id", "store_name"],
	"Employee Setup": ["location_id", "ename", "deptid", "desigid", "ecatid", "salary"],
	"Chart of Accounting": ["accid", "description", "nature", "chartlevel"],
}

# Link field → target DocType (blueprint Section 4).
LINK_OPTIONS: dict[str, dict[str, str]] = {
	"*": {
		"location_id": "Location",
		"partyid": "Party",
		"brokerid": "Party",
		"supplierid": "Party",
		"customerid": "Party",
		"sub_partyid": "Party",
		"itemcode": "Item Setup",
		"storeid": "Store Setup",
		"tostoreid": "Store Setup",
		"fromstoreid": "Store Setup",
		"cityid": "City Setup",
		"accid": "Chart of Accounting",
		"bankaccid": "Chart of Accounting",
		"empno": "Employee Setup",
		"trans_id": "Transaction List",
		"tcategory": "Transaction Category",
		"pcat_id": "Party Category",
		"iclassid": "Item Class",
		"company_id": "Mill Information",
		"bagid": "Item Setup",
		"bagitemcode": "Item Setup",
		"critem": "Item Setup",
		"proditem": "Item Setup",
		"dustitemid": "Item Setup",
		"mill_id": "Location",
		"vouchertype_id": "Voucher Type",
		"userid": "User Rights",
		"moduleid": "Module",
		"menuid": "Menu",
		"branchid": "Bank Branch",
	},
	"Advance Payment": {"bankaccid": "Chart of Accounting"},
	"Advance Receipt": {"bankaccid": "Chart of Accounting"},
	"Advance PNR": {"bankaccid": "Chart of Accounting"},
}

# Party link filters by field (pcat_id).
PARTY_LINK_FILTERS: dict[str, list[str]] = {
	"brokerid": ["11"],
	"supplierid": ["12"],
	"customerid": ["13"],
	"partyid": [],  # set per form in JS
}

# Chart of Accounting filters for posting accounts.
COA_POSTING_FILTER = {"chartlevel": 5, "transflag": "Yes"}


def location_ui_hidden(doctype: str) -> bool:
	return doctype in LOCATION_UI_HIDDEN_DOCTYPES


def hidden_for(doctype: str, fieldname: str) -> bool:
	if fieldname == "location_id" and location_ui_hidden(doctype):
		return True
	if fieldname in HIDDEN_FIELDS.get("*", []):
		return True
	return fieldname in HIDDEN_FIELDS.get(doctype, [])


def read_only_for(doctype: str, fieldname: str) -> bool:
	if fieldname == "location_id" and location_ui_hidden(doctype):
		return True
	return fieldname in READ_ONLY_FIELDS.get(doctype, [])


def mandatory_for(doctype: str, fieldname: str) -> bool | None:
	if fieldname == "location_id" and location_ui_hidden(doctype):
		return False
	if fieldname in MANDATORY_FIELDS.get(doctype, []):
		return True
	return None


def should_not_be_mandatory_ui(
	doctype: str,
	fieldname: str,
	field: dict,
	*,
	autoname_id: str | None = None,
) -> bool:
	"""Auto-filled / calculated fields must not block save with mandatory errors."""
	if field.get("read_only") or read_only_for(doctype, fieldname):
		return True
	if field.get("hidden") or hidden_for(doctype, fieldname):
		return True
	if fieldname == "location_id" and location_ui_hidden(doctype):
		return True
	if autoname_id and fieldname == autoname_id:
		return True
	if field.get("fetch_from"):
		return True
	return False


def link_options_for(doctype: str, fieldname: str) -> str | None:
	return LINK_OPTIONS.get(doctype, {}).get(fieldname) or LINK_OPTIONS.get("*", {}).get(fieldname)
