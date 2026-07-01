# Copyright (c) 2026, Millitrix and contributors
# Stock Adjustment line recalc — mirrors millitrix_stock_forms.js

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.order_calc import calc_stock_adjustment_amount
from millitrix.utils.stock import get_in_store_item_name
from millitrix.utils.stock_key import StockKey


def _line_stock_key(line) -> StockKey:
	return StockKey(
		storeid=line.storeid,
		itemcode=line.itemcode,
		bagitemcode=getattr(line, "bagitemcode", None) or None,
		partyid=getattr(line, "partyid", None) or None,
		bags_are=getattr(line, "bags_are", None) or None,
	)


def recalc_adjustment_line(line) -> None:
	inc = flt(line.inc_stock)
	dec = flt(line.dec_stock)
	key = _line_stock_key(line)
	name = get_in_store_item_name(key)
	current = flt(frappe.db.get_value("Stock In Hand", name, "stock_in_hand")) if name else 0
	line.current_stock = round(flt(current), 2)
	line.adjusted_stock = round(flt(current + inc - dec), 2)
	delta = inc - dec
	if hasattr(line, "amount"):
		line.amount = calc_stock_adjustment_amount(delta, flt(line.rate), line.itemcode)


def recalc_adjustment_document(doc) -> None:
	for line in doc.details or []:
		recalc_adjustment_line(line)
