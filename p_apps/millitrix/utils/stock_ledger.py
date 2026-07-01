# Copyright (c) 2026, Millitrix and contributors
# Immutable Stock Ledger Entry writer for P0-05

from __future__ import annotations

from contextlib import contextmanager

import frappe
from frappe.utils import flt, get_time, getdate, nowtime, today

from millitrix.utils.stock_key import StockKey


@contextmanager
def allow_stock_ledger_entry_update():
        """Temporarily allow trusted stock engine code to create Stock Ledger Entry rows."""
        old_value = getattr(frappe.flags, "allow_stock_ledger_entry_update", False)
        frappe.flags.allow_stock_ledger_entry_update = True
        try:
                yield
        finally:
                frappe.flags.allow_stock_ledger_entry_update = old_value


def make_stock_ledger_entry(
        key: StockKey,
        *,
        actual_qty: float,
        qty_after_transaction: float,
        posting_date: str | None = None,
        posting_time: str | None = None,
        movement_type: str = "ADJUST",
        voucher_type: str | None = None,
        voucher_no: str | None = None,
        voucher_detail_no: str | None = None,
        incoming_rate: float = 0,
        valuation_rate: float = 0,
        stock_value_difference: float = 0,
        is_cancelled: bool = False,
        remarks: str | None = None,
) -> str:
        """Create one immutable Stock Ledger Entry row from a stock movement."""
        doc = frappe.new_doc("Stock Ledger Entry")
        doc.posting_date = getdate(posting_date or today())
        doc.posting_time = get_time(posting_time or nowtime())
        doc.voucher_type = voucher_type or "Stock In Hand"
        doc.voucher_no = voucher_no or "SYSTEM"
        doc.voucher_detail_no = voucher_detail_no
        doc.movement_type = movement_type
        doc.storeid = key.storeid
        doc.itemcode = key.itemcode
        doc.bagitemcode = key.bagitemcode
        doc.partyid = key.partyid
        doc.bags_are = key.bags_are
        doc.actual_qty = flt(actual_qty)
        doc.qty_after_transaction = flt(qty_after_transaction)
        doc.incoming_rate = flt(incoming_rate)
        doc.valuation_rate = flt(valuation_rate)
        doc.stock_value_difference = flt(stock_value_difference)
        doc.is_cancelled = 1 if is_cancelled else 0
        doc.remarks = remarks

        with allow_stock_ledger_entry_update():
                doc.insert(ignore_permissions=True)

        return doc.name
