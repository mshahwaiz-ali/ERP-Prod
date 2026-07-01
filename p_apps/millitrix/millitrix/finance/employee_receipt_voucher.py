# Copyright (c) 2026, Millitrix and contributors
# Blueprint — CNBEmpVoucher.fmx (receipt mode)

from __future__ import annotations

from millitrix.finance.employee_voucher_common import (
	cancel_employee_voucher,
	submit_employee_voucher,
	validate_employee_voucher,
)
from millitrix.utils.doctype_ids import EMPLOYEE_RECEIPT_VOUCHER

_FIXED_MODE = "Receipt"


def validate(doc, method=None):
	validate_employee_voucher(
		doc,
		doctype_id=EMPLOYEE_RECEIPT_VOUCHER,
		voucher_mode=_FIXED_MODE,
	)


def on_submit(doc, method=None):
	submit_employee_voucher(doc, narration_prefix="Employee Receipt Voucher")


def on_cancel(doc, method=None):
	cancel_employee_voucher(doc)
