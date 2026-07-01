# Copyright (c) 2026, Millitrix and contributors
# Appendix J — bardana GL rows (PU on PI, SA on SI).

from __future__ import annotations

from collections import defaultdict

from frappe.utils import flt

from millitrix.utils.borrow import is_x_delivery, should_move_our_bardana_stock
from millitrix.utils.invoice_calc import calc_bagamnt
from millitrix.utils.mill_setting import get_setting_account


def bag_amnt_for_lines(lines, doc, *, is_purchase: bool) -> tuple[float, dict[str, float]]:
	"""Return total bag amount and per-bagid groups for GL posting."""
	if is_x_delivery(doc):
		return 0.0, {}

	expected_bags_are = "PU" if is_purchase else "SA"
	groups: dict[str, float] = defaultdict(float)

	for line in lines or []:
		if not line.bagid or flt(line.bagqty) <= 0:
			continue
		bags_are = (getattr(line, "bags_are", None) or expected_bags_are).upper()
		if bags_are not in (expected_bags_are,):
			continue
		groups[line.bagid] += calc_bagamnt(line, is_purchase=is_purchase)

	return sum(groups.values()), dict(groups)


def append_bardana_gl(
	batch, lines, doc, *, is_purchase: bool, truckno: str = "", reverse: bool = False
) -> float:
	"""Post bardana inventory GL; returns bag total posted."""
	_, groups = bag_amnt_for_lines(lines, doc, is_purchase=is_purchase)
	if not groups:
		return 0.0

	item_stock = get_setting_account("Item Stock GL")
	trade = get_setting_account("Trade Purchase" if is_purchase else "Trade Sales")
	acc = item_stock or trade
	suffix = f" truck.# {truckno}" if truckno else ""

	for bagid, amnt in groups.items():
		if amnt <= 0:
			continue
		detail = f"Bardana {bagid}{suffix}"
		if reverse:
			if is_purchase:
				batch.cr(acc, amnt, itemcode=bagid, detail=detail)
			else:
				batch.dr(acc, amnt, itemcode=bagid, detail=detail)
		elif is_purchase:
			batch.dr(acc, amnt, itemcode=bagid, detail=detail)
		else:
			batch.cr(acc, amnt, itemcode=bagid, detail=detail)

	return sum(groups.values())


def skip_bardana_stock_check(doc) -> bool:
	return not should_move_our_bardana_stock(doc)
