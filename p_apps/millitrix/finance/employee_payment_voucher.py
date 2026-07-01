# Copyright (c) 2026, Millitrix and contributors
# Blueprint — CNBEmpVoucher.fmx (payment mode)

from __future__ import annotations

from millitrix.finance.employee_voucher_common import (
	cancel_employee_voucher,
	submit_employee_voucher,
	validate_employee_voucher,
)
from millitrix.utils.doctype_ids import EMPLOYEE_PAYMENT_VOUCHER

_FIXED_MODE = "Payment"


def validate(doc, method=None):
	validate_employee_voucher(
		doc,
		doctype_id=EMPLOYEE_PAYMENT_VOUCHER,
		voucher_mode=_FIXED_MODE,
	)


def on_submit(doc, method=None):
	submit_employee_voucher(doc, narration_prefix="Employee Payment Voucher")


def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)