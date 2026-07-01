# Copyright (c) 2026, Millitrix and contributors
# Blueprint — BORROW D (Delivery) vs X (X-Delivery) bardana rules.

from __future__ import annotations


def is_x_delivery(doc) -> bool:
	"""True when party supplies bags (X-Delivery); mill bags on Delivery."""
	borrow = (getattr(doc, "borrow", None) or "").strip().upper()
	if not borrow:
		return False
	if borrow in ("X", "X DELIVERY", "X-DELIVERY"):
		return True
	return borrow.startswith("X")


def should_move_our_bardana_stock(doc) -> bool:
	"""Our bardana stock (PU/SA) moves only on Delivery."""
	return not is_x_delivery(doc)


def effective_bardana_bags_are(doc, line, *, is_purchase: bool) -> str:
	"""X-Delivery uses party bardana (PA); Delivery uses PU/SA."""
	from millitrix.utils.field_normalizers import normalize_bags_are_code

	if is_x_delivery(doc):
		return "PA"
	current = normalize_bags_are_code(getattr(line, "bags_are", None))
	if current:
		return current
	return "PU" if is_purchase else "SA"
