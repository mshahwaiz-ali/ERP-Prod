# Copyright (c) 2026, Millitrix and contributors
# Normalise invoice Select labels ↔ Oracle codes for calculations.

from __future__ import annotations

import frappe
from frappe.utils import flt


def normalize_amntby(value) -> str:
	key = (str(value or "Mund").strip().upper() if value not in (None, "") else "MUND")
	if key in ("B", "BAG", "BAG QUANTITY", "BAGS", "BAG QTY"):
		return "B"
	if key in ("M", "MUND", "MUNDS"):
		return "M"
	return key[:1] if key else "M"


def normalize_kantatype(value) -> str:
	key = (str(value or "Total Weight").strip().upper() if value not in (None, "") else "T")
	mapping = {
		"T": "T",
		"W": "W",
		"TOTAL WEIGHT": "T",
		"TOTAL": "T",
		"I": "I",
		"IN KANTA": "I",
		"D": "D",
		"DELIVERY KANTA": "D",
		"DELI KANTA": "D",
		"Q": "Q",
		"QUANTITY": "Q",
		"TRUCK QUANTITY": "Q",
	}
	return mapping.get(key, key[:1] if key else "T")


def normalize_brokery_status(value) -> str:
	key = (str(value or "Not Paid").strip().upper() if value not in (None, "") else "NOT PAID")
	if key in ("P", "PAID", "Y", "YES"):
		return "Paid"
	if key in ("NP", "NOT PAID", "N", "NO", "NOTPAID"):
		return "Not Paid"
	if flt(value) > 0 and key not in ("PAID", "NOT PAID"):
		# Legacy bad data: numeric brokery treated as Not Paid.
		return "Not Paid"
	return "Not Paid" if not value else str(value).strip()


def is_brokery_paid(value) -> bool:
	return normalize_brokery_status(value) == "Paid"


def is_yes(value) -> bool:
	from millitrix.utils.field_normalizers import is_yes as _is_yes

	return _is_yes(value)


def normalize_bags_are(value) -> str:
	from millitrix.utils.field_normalizers import normalize_bags_are_code

	return normalize_bags_are_code(value)


def mundtype_code_from_value(value) -> str:
	if value is None or value == "":
		return "N"
	if isinstance(value, str):
		text = value.strip().upper()
		if text in ("N", "O", "Q"):
			return text
		if "OLD" in text:
			return "O"
		if "NEW" in text:
			return "N"
		if "QUANT" in text:
			return "Q"
	mt_f = flt(value)
	if mt_f == 37.324:
		return "O"
	if mt_f == 1:
		return "Q"
	return "N"


def mundtype_code_from_item(itemcode: str | None) -> str | None:
	if not itemcode:
		return None
	mt = frappe.db.get_value("Item Setup", itemcode, "mundtype")
	if not mt:
		return None
	return mundtype_code_from_value(mt)


def normalize_mundtype_code(header) -> str:
	itemcode = getattr(header, "itemcode", None)
	from_item = mundtype_code_from_item(itemcode)
	if from_item:
		return from_item
	mt = getattr(header, "mundtype", None)
	if mt not in (None, ""):
		return mundtype_code_from_value(mt)
	return "N"


def mundtype_select_default() -> str:
	return "New Mund"
