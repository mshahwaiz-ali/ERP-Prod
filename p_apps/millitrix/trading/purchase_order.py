# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doctype_ids import PURCHASE_ORDER
from millitrix.utils.field_normalizers import normalize_order_status, order_status_label
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.order_balance import SIDE_PURCHASE, validate_split_child_order
from millitrix.utils.order_calc import calc_order_amount
from millitrix.utils.stock import mark_posted, mark_unposted


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = PURCHASE_ORDER
	validate_fiscal_period(doc.podate)
	if not doc.status:
		doc.status = order_status_label("IN")
	validate_split_child_order(doc, SIDE_PURCHASE)
	doc.amount = calc_order_amount(doc)
	doc.payable = doc.amount


def on_submit(doc, method=None):
	if normalize_order_status(doc.status) not in ("IN", "IP"):
		doc.db_set("status", order_status_label("IN"))
	mark_posted(doc)


from millitrix.finance.unsubmit import on_cancel as unified_cancel

def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)