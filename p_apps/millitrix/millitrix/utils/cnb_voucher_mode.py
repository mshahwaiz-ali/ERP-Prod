# CNB voucher direction — derived from DocType when vouchmode field is absent.
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

CNB_RECEIPT_DOCTYPES = frozenset(
	{
		"Receipt Voucher",
		"Party Receipt Voucher",
		"Employee Receipt Voucher",
	}
)

CNB_PAYMENT_DOCTYPES = frozenset(
	{
		"Payment Voucher",
		"Party Payment Voucher",
		"Employee Payment Voucher",
	}
)


def cnb_voucher_mode(doctype: str | None) -> str:
	if doctype in CNB_RECEIPT_DOCTYPES:
		return "Receipt"
	if doctype in CNB_PAYMENT_DOCTYPES:
		return "Payment"
	return ""


def resolve_vouchmode(doc) -> str:
	mode = (getattr(doc, "vouchmode", None) or "").strip()
	if mode:
		return mode
	return cnb_voucher_mode(getattr(doc, "doctype", None))


def is_cnb_receipt(doc) -> bool:
	return resolve_vouchmode(doc).upper() in ("R", "RECEIPT")
