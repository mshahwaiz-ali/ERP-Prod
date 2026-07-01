# Copyright (c) 2026, Millitrix and contributors
# For license information, see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


def _stock_ledger_update_allowed(doc=None) -> bool:
        """Allow Stock Ledger Entry mutation only from trusted stock posting code."""
        if getattr(frappe.flags, "allow_stock_ledger_entry_update", False):
                return True
        if doc is not None and getattr(getattr(doc, "flags", None), "allow_stock_ledger_entry_update", False):
                return True
        return False


def _block_direct_stock_ledger_update(doc=None) -> None:
        if _stock_ledger_update_allowed(doc):
                return
        frappe.throw(
                _(
                        "Stock Ledger Entry is system-generated. Use source stock documents "
                        "and submit/cancel flows instead of editing ledger rows directly."
                ),
                title=_("Direct Stock Ledger Update Blocked"),
        )


class StockLedgerEntry(Document):
        def before_insert(self):
                _block_direct_stock_ledger_update(self)

        def before_save(self):
                _block_direct_stock_ledger_update(self)

        def before_delete(self):
                _block_direct_stock_ledger_update(self)
