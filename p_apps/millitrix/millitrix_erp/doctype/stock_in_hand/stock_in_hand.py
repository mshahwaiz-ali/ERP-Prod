# Copyright (c) 2026, Millitrix and contributors
# For license information, see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from millitrix.utils.stock_key import make_stock_key_from_values


def _stock_in_hand_update_allowed(doc=None) -> bool:
        """Allow Stock In Hand mutation only from trusted stock posting code."""
        if getattr(frappe.flags, "allow_stock_in_hand_update", False):
                return True
        if doc is not None and getattr(getattr(doc, "flags", None), "allow_stock_in_hand_update", False):
                return True
        return False


def _block_direct_stock_in_hand_update(doc=None) -> None:
        if _stock_in_hand_update_allowed(doc):
                return
        frappe.throw(
                _(
                        "Stock In Hand is system-managed. Use Opening Stock, Stock Adjustment, "
                        "Stock Transfer, Gate Pass, Purchase/Sales documents, or approved stock posting flows."
                ),
                title=_("Direct Stock Balance Update Blocked"),
        )


class StockInHand(Document):
        def _set_stock_key(self):
                """Compute stable unique identity for Stock In Hand balance rows."""
                if not self.bags_are:
                        self.bags_are = "Our"
                self.stock_key = make_stock_key_from_values(
                        storeid=self.storeid,
                        itemcode=self.itemcode,
                        bagitemcode=self.bagitemcode,
                        partyid=self.partyid,
                        bags_are=self.bags_are,
                )

        def validate(self):
                self._set_stock_key()

        def before_insert(self):
                self._set_stock_key()
                _block_direct_stock_in_hand_update(self)

        def before_save(self):
                self._set_stock_key()
                _block_direct_stock_in_hand_update(self)

        def before_delete(self):
                _block_direct_stock_in_hand_update(self)
