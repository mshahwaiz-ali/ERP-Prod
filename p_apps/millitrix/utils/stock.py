# Copyright (c) 2026, Millitrix and contributors
# Blueprint Section 11 — IN_STORE_ITEMS stock engine

from __future__ import annotations

from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

from millitrix.utils.field_normalizers import bags_are_db_value
from millitrix.utils.stock_key import StockKey, make_stock_key, normalized_bags_are_for_stock_key
from millitrix.utils.stock_ledger import make_stock_ledger_entry


@contextmanager
def allow_stock_in_hand_update():
        """Temporarily allow trusted stock engine code to mutate Stock In Hand."""
        old_value = getattr(frappe.flags, "allow_stock_in_hand_update", False)
        frappe.flags.allow_stock_in_hand_update = True
        try:
                yield
        finally:
                frappe.flags.allow_stock_in_hand_update = old_value


def _bags_are_db_value(code: str | None, key: StockKey | None = None) -> str | None:
        is_bardana = bool(key and key.bagitemcode)
        return bags_are_db_value(code, is_bardana=is_bardana)


def calc_moving_rate(old_stock: float, old_rate: float, in_qty: float, in_rate: float) -> float:
        """Blueprint Section 11.2 / 22."""
        old_stock = flt(old_stock)
        old_rate = flt(old_rate)
        in_qty = flt(in_qty)
        in_rate = flt(in_rate)
        if in_qty <= 0:
                return old_rate
        total_qty = old_stock + in_qty
        if total_qty <= 0:
                return in_rate
        return round(flt(((old_stock * old_rate) + (in_qty * in_rate)) / total_qty), 2)


def _filters_for_key(key: StockKey) -> dict:
        """Legacy fallback filters for rows created before stock_key existed."""
        filters: dict = {"storeid": key.storeid, "itemcode": key.itemcode}
        for field, val in (
                ("bagitemcode", key.bagitemcode),
                ("partyid", key.partyid),
        ):
                if val:
                        filters[field] = val
                else:
                        filters[field] = ["is", "not set"]

        db_bags = _bags_are_db_value(normalized_bags_are_for_stock_key(key), key)
        filters["bags_are"] = db_bags or "Our"
        return filters


def get_in_store_item_name(key: StockKey) -> str | None:
        stock_key = make_stock_key(key)
        name = frappe.db.get_value("Stock In Hand", {"stock_key": stock_key}, "name")
        if name:
                return name
        return frappe.db.get_value("Stock In Hand", _filters_for_key(key), "name")


def get_or_create_in_store_item(
        key: StockKey,
        *,
        bagweight: float | None = None,
        for_update: bool = False,
) -> frappe.model.document.Document:
        name = get_in_store_item_name(key)
        if name:
                doc = frappe.get_doc("Stock In Hand", name, for_update=for_update)
                return doc

        doc = frappe.new_doc("Stock In Hand")
        doc.storeid = key.storeid
        doc.itemcode = key.itemcode
        if key.bagitemcode:
                doc.bagitemcode = key.bagitemcode
        if key.partyid:
                doc.partyid = key.partyid
        db_bags = _bags_are_db_value(normalized_bags_are_for_stock_key(key), key)
        doc.bags_are = db_bags or "Our"
        doc.stock_key = make_stock_key(key)
        doc.stock_in_hand = 0
        doc.opening_stock = 0
        doc.movingrate = 0
        if bagweight is not None:
                doc.bagweight = bagweight
        with allow_stock_in_hand_update():
                doc.insert(ignore_permissions=True)
        return doc


def apply_stock_in(
        key: StockKey,
        qty: float,
        *,
        rate: float = 0,
        movement_date: str | None = None,
        bagweight: float | None = None,
        set_absolute: bool = False,
        absolute_qty: float | None = None,
) -> None:
        """Stock IN — updates moving average on incremental receipt (Blueprint 11.2)."""
        qty = flt(qty)
        if qty <= 0 and not set_absolute:
                return

        row = get_or_create_in_store_item(key, bagweight=bagweight, for_update=True)
        movement_date = movement_date or today()

        if set_absolute and absolute_qty is not None:
                row.stock_in_hand = flt(absolute_qty)
                if rate:
                        row.movingrate = flt(rate)
        else:
                row.stock_in_hand = flt(row.stock_in_hand) + qty
                row.movingrate = calc_moving_rate(row.stock_in_hand - qty, row.movingrate, qty, rate)

        if bagweight is not None and flt(bagweight) > 0:
                old_bw = flt(row.bagweight)
                if set_absolute:
                        row.bagweight = flt(bagweight)
                elif old_bw and row.stock_in_hand > qty:
                        row.bagweight = calc_moving_rate(row.stock_in_hand - qty, old_bw, qty, bagweight)
                else:
                        row.bagweight = flt(bagweight)

        row.ltdate = getdate(movement_date)
        with allow_stock_in_hand_update():
                row.save(ignore_permissions=True)

        actual_qty = flt(row.stock_in_hand) if set_absolute and absolute_qty is not None else qty
        make_stock_ledger_entry(
                key,
                actual_qty=actual_qty,
                qty_after_transaction=row.stock_in_hand,
                posting_date=movement_date,
                movement_type="ADJUST" if set_absolute else "IN",
                incoming_rate=rate,
                valuation_rate=row.movingrate,
                stock_value_difference=flt(actual_qty) * flt(row.movingrate),
                remarks="Stock IN" if not set_absolute else "Stock absolute adjustment",
        )


def apply_stock_out(
        key: StockKey,
        qty: float,
        *,
        movement_date: str | None = None,
        check_reserved: bool = True,
        exclude_doctype: str | None = None,
        exclude_name: str | None = None,
) -> None:
        """Stock OUT — decrements stock_in_hand; optional VIEW_US_STOCK check (Blueprint 11.3)."""
        qty = flt(qty)
        if qty <= 0:
                return

        name = get_in_store_item_name(key)
        if not name:
                frappe.throw(
                        _("No stock record for Store {0}, Item {1}").format(key.storeid, key.itemcode)
                )

        row = frappe.get_doc("Stock In Hand", name, for_update=True)
        available = flt(row.stock_in_hand)

        if check_reserved:
                from millitrix.utils.reserved_stock import get_reserved_qty

                reserved = get_reserved_qty(
                        key,
                        exclude_doctype=exclude_doctype,
                        exclude_name=exclude_name,
                )
                available -= reserved

        if qty > available + 1e-9:
                frappe.throw(
                        _("Insufficient stock for Store {0}, Item {1}. Available {2}, required {3}").format(
                                key.storeid, key.itemcode, available, qty
                        )
                )

        row.stock_in_hand = flt(row.stock_in_hand) - qty
        row.ltdate = getdate(movement_date or today())
        with allow_stock_in_hand_update():
                row.save(ignore_permissions=True)

        make_stock_ledger_entry(
                key,
                actual_qty=-qty,
                qty_after_transaction=row.stock_in_hand,
                posting_date=movement_date or today(),
                movement_type="OUT",
                valuation_rate=row.movingrate,
                stock_value_difference=-flt(qty) * flt(row.movingrate),
                remarks="Stock OUT",
        )


def is_out_gptype(gptype: str) -> bool:
        """Blueprint J.4 — OUT decreases stock; IN increases."""
        return (gptype or "").upper() in ("OUT", "SALES", "O")


def is_in_gptype(gptype: str) -> bool:
        return (gptype or "").upper() in ("IN", "PURCHASE", "P")


def grain_key_from_gate_line(doc, line) -> StockKey:
        from millitrix.utils.trading_stock_keys import trading_grain_key

        return trading_grain_key(itemcode=doc.itemcode, storeid=line.storeid)


def bardana_key_from_gate_line(doc, line) -> StockKey | None:
        if not line.bagid:
                return None
        from millitrix.utils.field_normalizers import is_yes

        # Oracle GPSUBMIT: decode(EmptyBags,'No', header ItemCode, null)
        bagitemcode = None if is_yes(line.emptybags) else doc.itemcode
        return StockKey(
                storeid=line.storeid,
                itemcode=line.bagid,
                bagitemcode=bagitemcode,
                partyid=doc.partyid or None,
                bags_are=line.bags_are or None,
        )


def line_grain_qty(line) -> float:
        """Weight qty for grain movement — prefer netweight."""
        qty = flt(line.netweight)
        if qty > 0:
                return qty
        return flt(line.truckqty)


def check_bag_stock(
        key: StockKey,
        qty: float,
        *,
        exclude_doctype: str | None = None,
        exclude_name: str | None = None,
) -> None:
        """Blueprint CHECK_BAGSTOCK / Section 11.3."""
        qty = flt(qty)
        if qty <= 0:
                return

        name = get_in_store_item_name(key)
        stock = flt(frappe.db.get_value("Stock In Hand", name, "stock_in_hand")) if name else 0
        from millitrix.utils.reserved_stock import get_reserved_qty

        reserved = get_reserved_qty(key, exclude_doctype=exclude_doctype, exclude_name=exclude_name)
        available = stock - reserved
        if qty > available + 1e-9:
                frappe.throw(
                        _("Insufficient Bardana stock. Available {0}, required {1}").format(available, qty)
                )


def mark_posted(doc) -> None:
        from millitrix.utils.field_normalizers import normalize_posted

        doc.db_set("posted", normalize_posted("Submitted"))
        if frappe.get_meta(doc.doctype).has_field("posted_by"):
                doc.db_set("posted_by", frappe.session.user)


def mark_unposted(doc) -> None:
        doc.db_set("posted", "Draft")
        if frappe.get_meta(doc.doctype).has_field("posted_by"):
                doc.db_set("posted_by", None)
