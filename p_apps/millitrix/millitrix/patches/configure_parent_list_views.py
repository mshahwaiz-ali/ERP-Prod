# Parent DocType list view columns — table-first daily use.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

from millitrix.utils.list_view_plan import PARENT_LIST_COLUMNS, STANDARD_FILTERS, TITLE_FIELDS

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

PARENT_IN_LIST_VIEW: dict[str, list[str]] = {
	"Purchase Invoice": [
		"invdate",
		"itemcode",
		"supplierid",
		"brokerid",
		"kantatype",
		"amount",
		"payable",
		"purchinvno",
	],
	"Sales Invoice": [
		"invdate",
		"itemcode",
		"customerid",
		"brokerid",
		"kantatype",
		"amount",
		"receivable",
		"salesinvno",
	],
	"Purchase Order": [
		"podate",
		"itemcode",
		"supplierid",
		"brokerid",
		"rate",
		"amount",
		"status",
		"ponumber",
	],
	"Purchase Other Bill": [
		"billdate",
		"partyid",
		"amount",
		"pbillno",
	],
	"Sales Order": [
		"sodate",
		"itemcode",
		"customerid",
		"brokerid",
		"rate",
		"amount",
		"status",
		"sonumber",
	],
	"Purchase Invoice Payment": ["pnrdate", "partyid", "pnrmode", "amount", "line_count", "narration", "pnrno"],
	"Sales Invoice Receipt": ["pnrdate", "partyid", "pnrmode", "amount", "line_count", "narration", "pnrno"],
	"Broker Invoice Payment": ["pnrdate", "partyid", "pnrmode", "amount", "line_count", "narration", "pnrno"],
	"Advance Payment": ["pnrdate", "partyid", "pnrmode", "amount", "narration", "pnrno"],
	"Advance Receipt": ["pnrdate", "partyid", "pnrmode", "amount", "narration", "pnrno"],
	"Payable Discount Note": ["pnrdate", "partyid", "amount", "line_count", "narration", "pnrno"],
	"Receivable Discount Note": ["pnrdate", "partyid", "amount", "line_count", "narration", "pnrno"],
	"Party Gross Margin": ["pgdate", "partyid", "itemcode", "amount", "line_count", "pgmode", "narration", "pgmid"],
	"Party Payment Voucher": [
		"vouchdate",
		"partyid",
		"paymode",
		"amount",
		"line_count",
		"narration",
		"cnbvno",
	],
	"Party Receipt Voucher": [
		"vouchdate",
		"partyid",
		"paymode",
		"amount",
		"line_count",
		"narration",
		"cnbvno",
	],
	"Payment Voucher": [
		"vouchdate",
		"primary_acc",
		"paymode",
		"amount",
		"line_count",
		"narration",
		"cnbvno",
	],
	"Receipt Voucher": [
		"vouchdate",
		"primary_acc",
		"paymode",
		"amount",
		"line_count",
		"narration",
		"cnbvno",
	],
	"Expense Voucher": [
		"vouchdate",
		"primary_acc",
		"paymode",
		"amount",
		"line_count",
		"narration",
		"cnbvno",
	],
	"Employee Payment Voucher": [
		"vouchdate",
		"primary_employee",
		"paymode",
		"amount",
		"line_count",
		"narration",
		"empvno",
	],
	"Employee Receipt Voucher": [
		"vouchdate",
		"primary_employee",
		"paymode",
		"amount",
		"line_count",
		"narration",
		"empvno",
	],
	"Accounts Opening": [
		"opening_date",
		"primary_acc",
		"line_count",
		"total_debit",
		"total_credit",
		"glopenid",
	],
	"GL Statements": [
		"statement",
		"description",
		"active",
		"operation",
		"line_count",
		"account_count",
		"statementid",
	],
	"In Out Gate Pass": ["gpdate", "gptype", "itemcode", "partyid", "gatepassno"],
	"Purchase Return": [
		"retdate",
		"itemcode",
		"supplierid",
		"brokerid",
		"purchinvno",
		"amount",
		"purchretno",
	],
	"Purchase Return Other Bill": ["brdate", "partyid", "pbillno", "amount", "prbillno"],
	"Sales Return": ["retdate", "itemcode", "customerid", "brokerid", "salesinvno", "amount", "salesretno"],
	"Sales Return Other Bill": ["brdate", "partyid", "sbillno", "amount", "srbillno"],
	"Sales Other Bill": ["billdate", "partyid", "amount", "sbillno"],
	"SO Cancellation": [
		"candate",
		"partyid",
		"primary_item",
		"total_cancel_qty",
		"line_count",
		"remarks",
		"socid",
	],
	"Stock Adjustment": [
		"sadate",
		"primary_item",
		"primary_store",
		"line_count",
		"total_amount",
		"remarks",
		"stkadjid",
	],
	"Item Price List": [
		"ipdate",
		"location_id",
		"itemcode",
		"iclassid",
		"purchrate",
		"salesrate",
		"westage",
	],
	"Bank": ["bankname", "shortname", "branch_count", "account_count", "bankid"],
	"Location": ["description", "short_name", "company_id", "cityid", "phno1", "address", "location_id"],
	"Mill Information": ["description", "short_name", "phno1", "address", "company_id"],
	"City Setup": ["cityname", "cityid"],
	"Departments": ["description", "deptid"],
	"Designation": ["description", "desigid"],
	"Employee Setup": [
		"ename",
		"location_id",
		"deptid",
		"desigid",
		"ecatid",
		"salary",
		"phno1",
		"empno",
	],
	"Store Setup": [
		"store_name",
		"trans_allow",
		"storetypeid",
		"location_id",
		"store_address",
		"storeid",
	],
	"Store Types": ["description", "storetypeid"],
	"Party": ["party_name", "cityid", "mobileno", "phno1", "creditlimit", "pcat_id", "partyid"],
	"Chart of Accounting": ["description", "nature", "chartlevel", "parentid", "transflag", "accid"],
	"Item Setup": ["itemname", "iclassid", "mundtype", "stockable", "itemcode"],
	"Item Class": ["description", "iclassid"],
	"Other Contact Setup": ["name", "cityid", "pcat_id", "mobileno", "phno1", "address", "contactid"],
	"Party Category": ["description", "accid", "account_description", "pcat_id"],
	"Employee Category": ["description", "accid", "account_description", "payslip", "ecatid"],
	"Transaction Category": ["description", "accid", "account_description", "tcat_id"],
	"Transaction List": ["description", "tcat_id", "category_description", "trans_id"],
	"User Rights": ["username", "erp_user", "location_id", "empno", "employee_name", "activestatus", "userid"],
	"Crashing Refine": ["crdate", "mill_id", "primary_item", "primary_output", "input_weight", "crashid"],
	"PaySlip": ["paymonth", "pdate", "primary_employee", "employee_count", "total_salary", "remarks", "pslipid"],
	"PO Cancellation": [
		"candate",
		"partyid",
		"primary_item",
		"total_cancel_qty",
		"line_count",
		"remarks",
		"pocid",
	],
	"Menu": ["description", "parentid", "sortby", "menuid"],
	"Module": ["module", "menuid", "nature", "moduletype", "runtimefile", "moduleid"],
	"Paid Advance Adjustment": ["adjdate", "partyid", "amount", "line_count", "narration", "adjid"],
	"Received Advance Adjustment": ["adjdate", "partyid", "amount", "line_count", "narration", "adjid"],
	"Closing and Adjustment Entries": [
		"vouchdate",
		"narration",
		"reference",
		"primary_acc",
		"line_count",
		"total_debit",
		"total_credit",
		"voucherno",
	],
	"Voucher Transaction": [
		"vouchdate",
		"narration",
		"reference",
		"primary_acc",
		"line_count",
		"total_debit",
		"total_credit",
		"voucherno",
	],
}

PARENT_IN_LIST_VIEW.update(PARENT_LIST_COLUMNS)


def apply_json() -> None:
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		if data.get("istable"):
			continue
		doctype = data.get("name") or folder.name.replace("_", " ").title()
		cols = PARENT_IN_LIST_VIEW.get(doctype)
		if not cols:
			continue
		col_set = set(cols)
		changed = False
		for field in data.get("fields", []):
			fname = field.get("fieldname")
			if not fname:
				continue
			want = fname in col_set
			if field.get("hidden") and want and fname == "posted":
				continue
			if want:
				if not field.get("in_list_view"):
					field["in_list_view"] = 1
					changed = True
				if field.get("columns") != 1:
					field["columns"] = 1
					changed = True
			elif field.get("in_list_view") and not field.get("hidden"):
				field["in_list_view"] = 0
				changed = True
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			print("parent list columns", doctype)


def apply_title_and_standard_filters() -> None:
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		if data.get("istable"):
			continue
		doctype = data.get("name") or folder.name.replace("_", " ").title()
		changed = False
		want_title = TITLE_FIELDS.get(doctype)
		if want_title and data.get("title_field") != want_title:
			data["title_field"] = want_title
			changed = True
		filter_set = set(STANDARD_FILTERS.get(doctype, []))
		if filter_set:
			for field in data.get("fields", []):
				fname = field.get("fieldname")
				if not fname:
					continue
				want_filter = fname in filter_set
				has_filter = bool(field.get("in_standard_filter"))
				if want_filter and not has_filter:
					field["in_standard_filter"] = 1
					changed = True
				elif not want_filter and has_filter:
					field["in_standard_filter"] = 0
					changed = True
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n",encoding="utf-8")
			print("title/filters", doctype)


def _sync_title_and_filters_db() -> None:
	for doctype, title_field in TITLE_FIELDS.items():
		if frappe.db.exists("DocType", doctype):
			frappe.db.set_value("DocType", doctype, "title_field", title_field, update_modified=False)
	for doctype, fieldnames in STANDARD_FILTERS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		for fieldname in fieldnames:
			if frappe.db.exists(
				"DocField",
				{"parent": doctype, "fieldname": fieldname, "parenttype": "DocType"},
			):
				frappe.db.set_value(
					"DocField",
					{"parent": doctype, "fieldname": fieldname, "parenttype": "DocType"},
					"in_standard_filter",
					1,
					update_modified=False,
				)
	frappe.db.commit()


def _hide_posted_from_list_view() -> None:
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		if not data.get("is_submittable"):
			continue
		changed = False
		for field in data.get("fields", []):
			if field.get("fieldname") == "posted" and field.get("in_list_view"):
				field["in_list_view"] = 0
				changed = True
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			print("hide posted list col", data.get("name"))


def _sync_db() -> None:
	for doctype, fieldnames in PARENT_IN_LIST_VIEW.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		for fieldname in fieldnames:
			if not frappe.db.exists(
				"DocField",
				{"parent": doctype, "fieldname": fieldname, "parenttype": "DocType"},
			):
				continue
			updates = {"in_list_view": 1, "columns": 1}
			if fieldname == "posted":
				continue
			frappe.db.set_value(
				"DocField",
				{"parent": doctype, "fieldname": fieldname, "parenttype": "DocType"},
				updates,
				update_modified=False,
			)
	for doctype in frappe.get_all(
		"DocType", filters={"module": "Millitrix ERP", "is_submittable": 1}, pluck="name"
	):
		if frappe.db.exists(
			"DocField",
			{"parent": doctype, "fieldname": "posted", "parenttype": "DocType"},
		):
			frappe.db.set_value(
				"DocField",
				{"parent": doctype, "fieldname": "posted", "parenttype": "DocType"},
				"in_list_view",
				0,
				update_modified=False,
			)
	frappe.db.commit()


def execute() -> None:
	apply_json()
	apply_title_and_standard_filters()
	_hide_posted_from_list_view()
	_sync_db()
	_sync_title_and_filters_db()
	frappe.clear_cache(doctype="DocType")


if __name__ == "__main__":
	apply_json()
