# Set default Today on transaction date fields (Oracle SYSDATE parity).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import json
from pathlib import Path

import frappe

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

# Keep in sync with millitrix_default_dates.js TRANSACTION_DOCTYPES
TRANSACTION_DATE_FIELDS: dict[str, str] = {
	"Purchase Order": "podate",
	"Sales Order": "sodate",
	"Purchase Invoice": "invdate",
	"Sales Invoice": "invdate",
	"Purchase Return": "retdate",
	"Sales Return": "retdate",
	"Purchase Other Bill": "billdate",
	"Sales Other Bill": "billdate",
	"Purchase Return Other Bill": "brdate",
	"Sales Return Other Bill": "brdate",
	"In Out Gate Pass": "gpdate",
	"Stock Adjustment": "sadate",
	"Stock Transfer Note": "tdate",
	"Opening Stock": "opendate",
	"Closing Stock": "opendate",
	"Crashing Refine": "crdate",
	"PO Cancellation": "candate",
	"SO Cancellation": "candate",
	"Un-Submit Documents": "usdate",
	"Accounts Opening": "opening_date",
	"Voucher Transaction": "vouchdate",
	"Closing and Adjustment Entries": "vouchdate",
	"Advance Payment": "pnrdate",
	"Advance Receipt": "pnrdate",
	"Advance PNR": "pnrdate",
	"Purchase Invoice Payment": "pnrdate",
	"Sales Invoice Receipt": "pnrdate",
	"Broker Invoice Payment": "pnrdate",
	"Payable Discount Note": "pnrdate",
	"Receivable Discount Note": "pnrdate",
	"Paid Advance Adjustment": "adjdate",
	"Received Advance Adjustment": "adjdate",
	"Payment Voucher": "vouchdate",
	"Receipt Voucher": "vouchdate",
	"Expense Voucher": "vouchdate",
	"Party Payment Voucher": "vouchdate",
	"Party Receipt Voucher": "vouchdate",
	"Employee Payment Voucher": "vouchdate",
	"Employee Receipt Voucher": "vouchdate",
	"Party Gross Margin": "pgdate",
	"Payment By Hawala": "gmdate",
	"PaySlip": "pdate",
	"Item Price List": "ipdate",
	"Pay Salary Increment": "indate",
	"Cash and Bank Voucher": "vouchdate",
	"Payment and Receipt Voucher": "pnrdate",
}


def execute() -> None:
	updated: list[str] = []
	for doctype, date_field in TRANSACTION_DATE_FIELDS.items():
		folder = frappe.scrub(doctype)
		json_path = BASE / folder / f"{folder}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		changed = False
		for field in data.get("fields", []):
			if field.get("fieldname") != date_field:
				continue
			if field.get("fieldtype") not in ("Date", "Datetime"):
				continue
			if field.get("default") != "Today":
				field["default"] = "Today"
				changed = True
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			updated.append(doctype)

	for doctype in updated:
		frappe.reload_doc("millitrix_erp", "doctype", frappe.scrub(doctype))

	if updated:
		frappe.clear_cache(doctype="DocType")
	print(f"set default Today on {len(updated)} doctypes")
