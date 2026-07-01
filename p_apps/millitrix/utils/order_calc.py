# Copyright (c) 2026, Millitrix and contributors
# Purchase / Sales Order amount — Oracle PurchOrder.fmb / SalesOrder.fmb

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.invoice_fields import mundtype_code_from_value
from millitrix.utils.mund import mund_factor


def calc_order_qty(truckqty: float, weight: float, mundtype: str = "N") -> float:
	"""NVL(Weight/MundType, TruckQty) — weight in kg converted to order qty via mund factor."""
	if flt(weight) > 0:
		return flt(weight) / mund_factor(mundtype or "N")
	return flt(truckqty)


def item_mundtype(itemcode: str | None) -> str:
	if not itemcode:
		return "N"
	raw = frappe.db.get_value("Item Setup", itemcode, "mundtype")
	return mundtype_code_from_value(raw) if raw else "N"


def calc_order_amount(doc) -> float:
	mundtype = item_mundtype(getattr(doc, "itemcode", None))
	qty = calc_order_qty(getattr(doc, "truckqty", 0), getattr(doc, "weight", 0), mundtype)
	return round(flt(qty) * flt(getattr(doc, "rate", 0)))


def calc_stock_adjustment_amount(delta_kg: float, rate: float, itemcode: str | None = None) -> float:
	"""Oracle STKADJDETL.AMOUNT = -(Inc_Stock − Dec_Stock) × Rate (kg × rate)."""
	return round(flt(-flt(delta_kg) * flt(rate)), 2)
