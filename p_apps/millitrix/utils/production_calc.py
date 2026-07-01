# Copyright (c) 2026, Millitrix and contributors
# Crashing / Refine — Oracle CrashRefine.fmb FORMULA-CALCULATION parity.
#
#   weight      = round(bagqty × per_bag)
#   ref_weight  = round(bagqty × (per_bag − westage_kg_per_bag))
#   ref_bags    = round(ref_weight ÷ per_bag)
#   prod_1      = round(mund_factor × dip)
#   prod_2      = round(ref_weight − prod_1)
#
# Westage (bagdust) = kg lost per bag, not percent.

from __future__ import annotations

from frappe.utils import flt

from millitrix.utils.invoice_fields import mundtype_code_from_value
from millitrix.utils.mund import mund_factor


def _mund_factor_for_line(line) -> float:
	mt = getattr(line, "mundtype", None)
	if mt in (None, "", 0):
		return mund_factor("N")
	if isinstance(mt, str) and mt.strip().upper() in ("N", "O", "Q"):
		return mund_factor(mt)
	return mund_factor(mundtype_code_from_value(mt))


def westage_kg_per_bag(line) -> float:
	return flt(getattr(line, "bagdust", 0))


def input_total_weight(line) -> float:
	return round(flt(line.bagqty) * flt(line.bagweight))


def ref_weight_qty(line) -> float:
	per = flt(line.bagweight)
	dust = westage_kg_per_bag(line)
	return round(flt(line.bagqty) * max(0.0, per - dust))


def ref_bags_qty(line) -> float:
	per = flt(line.bagweight)
	if per <= 0:
		return 0.0
	return round(ref_weight_qty(line) / per)


def wastage_kg(line) -> float:
	"""Total dust kg — Oracle CRSUBMIT: BagQty × BagDust."""
	return flt(line.bagqty) * westage_kg_per_bag(line)


def prod_1_qty(line) -> float:
	return round(_mund_factor_for_line(line) * flt(getattr(line, "dip", 0)))


def prod_2_qty(line) -> float:
	return round(ref_weight_qty(line) - prod_1_qty(line))


def input_grain_qty(line) -> float:
	"""Grain stock OUT — full input weight (Oracle checks :CRItem.Weight)."""
	return input_total_weight(line)


def input_grain_cost(line) -> float:
	return input_grain_qty(line) * flt(line.rate)


def input_bag_cost(line) -> float:
	return flt(line.bagqty) * flt(line.bagrate)


def output_product_value(line) -> float:
	return flt(line.weight) * flt(line.rate)


def recalc_input_line(line) -> None:
	line.total_weight = flt(input_total_weight(line), 2)
	line.ref_weight = flt(ref_weight_qty(line), 2)
	line.ref_bags = flt(ref_bags_qty(line), 2)
	if flt(getattr(line, "dip", 0)):
		line.prod_1 = flt(prod_1_qty(line))
		line.prod_2 = flt(prod_2_qty(line))
	else:
		line.prod_1 = 0
		line.prod_2 = 0
