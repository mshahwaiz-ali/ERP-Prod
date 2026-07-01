# Copyright (c) 2026, Millitrix and contributors
"""Mark legacy merged finance DocTypes as deprecated (hidden from global search)."""

from __future__ import annotations

import json
from pathlib import Path

LEGACY_DOCTYPES = (
	"payment_and_receipt_voucher",
	"cash_and_bank_voucher",
	"advance_adjustment",
	"advance_payment",
	"advance_receipt",
)

REPORT_REF_DOCTYPE = {
	"advance_p_register": "Advance PNR",
	"advance_r_register": "Advance PNR",
	"payable_d_register": "Payable Discount Note",
	"receivable_d_register": "Receivable Discount Note",
	"party_p_register": "Party Payment Voucher",
	"party_r_register": "Party Receipt Voucher",
	"payment_register": "Payment Voucher",
	"receipt_register": "Receipt Voucher",
	"adv_p_adjust_reg": "Paid Advance Adjustment",
	"adv_r_adjust_reg": "Received Advance Adjustment",
}


def execute() -> None:
	base = Path(__file__).resolve().parents[1] / "millitrix_erp"
	for folder in LEGACY_DOCTYPES:
		jp = base / "doctype" / folder / f"{folder}.json"
		if not jp.exists():
			continue
		data = json.loads(jp.read_text(encoding="utf-8"))
		data["show_name_in_global_search"] = 0
		data["allow_import"] = 0
		jp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

	for folder, ref in REPORT_REF_DOCTYPE.items():
		jp = base / "report" / folder / f"{folder}.json"
		if not jp.exists():
			continue
		data = json.loads(jp.read_text(encoding="utf-8"))
		data["ref_doctype"] = ref
		jp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

	print("deprecated legacy finance doctypes + updated report ref_doctype")
