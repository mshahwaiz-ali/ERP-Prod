# Copyright (c) 2026, Millitrix and contributors
# Map user-facing full-word Select values ↔ Oracle codes used in logic.

from __future__ import annotations


def is_yes(value) -> bool:
	key = (str(value or "").strip().upper())
	return key in ("Y", "YES", "1", "TRUE", "SUBMITTED", "ACTIVE")


def is_no(value) -> bool:
	return not is_yes(value)


def normalize_posted(value) -> str:
	return "Submitted" if is_yes(value) else "Draft"


def normalize_nature_code(value) -> str:
	key = (str(value or "Assets").strip().upper())
	mapping = {
		"A": "A",
		"ASSETS": "A",
		"ASSET": "A",
		"L": "L",
		"LIABILITIES": "L",
		"LIABILITY": "L",
		"Libilities": "L",
		"C": "C",
		"CAPITAL": "C",
		"R": "R",
		"REVENUE": "R",
		"E": "E",
		"EXPENSES": "E",
		"EXPENSE": "E",
	}
	if key in mapping:
		return mapping[key]
	for code, aliases in (
		("A", ("ASSET",)),
		("L", ("LIABIL",)),
		("C", ("CAP",)),
		("R", ("REV",)),
		("E", ("EXP",)),
	):
		if any(alias in key for alias in aliases):
			return code
	return key[:1] if key else "A"


def nature_matches(value, *codes: str) -> bool:
	return normalize_nature_code(value) in {c.upper() for c in codes}


def normalize_order_status(value) -> str:
	key = (str(value or "In Progress").strip().upper())
	if key in ("CA", "CANCELLED", "CANCEL"):
		return "CA"
	if key in ("CO", "COMPLETE", "COMPLETED"):
		return "CO"
	if key in ("IP", "IN PROGRESS", "IN-PROGRESS"):
		return "IP"
	if key in ("IN", "INITIAL"):
		return "IN"
	if "COMPLETE" in key:
		return "CO"
	if "PROGRESS" in key:
		return "IP"
	return "IN"


def order_status_label(code: str) -> str:
	mapping = {
		"IN": "Initial",
		"IP": "In Progress",
		"CO": "Complete",
		"CA": "Cancelled",
	}
	return mapping.get((code or "IP").upper(), "In Progress")


def normalize_bags_are_code(value) -> str:
	key = (str(value or "Our").strip().upper())
	if key in ("OUR", "O", "OUR BARADANA", "OUR BARDANA"):
		return "OUR"
	if key in ("PARTY", "PA", "P", "PARTY BARADANA", "PARTY BARDANA"):
		return "PA"
	if key in ("PU", "PURCHASE BARDAANA", "PURCHASE BARDANA", "PURCHASE WITH ITEM"):
		return "PU"
	if key in ("SA", "SALES BARDAANA", "SALES BARDANA", "SALE WITH ITEM"):
		return "SA"
	return key


def bags_are_db_value(code: str | None, *, is_bardana: bool = False) -> str | None:
	"""Map legacy stock keys (PU/SA/PA) to Stock In Hand select labels."""
	if not code:
		return None
	norm = normalize_bags_are_code(code)
	if norm in ("PU", "SA") and not is_bardana:
		return "Our"
	label_map = {
		"OUR": "Our",
		"PA": "Party",
		"PU": "Purchase Bardana",
		"SA": "Sales Bardana",
	}
	if norm in label_map:
		return label_map[norm]
	if code in label_map.values():
		return code
	return None


def bags_are_label(value, *, is_purchase: bool = False) -> str:
	return bags_are_db_value(value) or "Our"


def normalize_gate_pass_type(value) -> str:
	key = (str(value or "In").strip().upper())
	if key in ("OUT", "O"):
		return "OUT"
	return "IN"


def gate_pass_type_label(value) -> str:
	return "Out" if normalize_gate_pass_type(value) == "OUT" else "In"


def normalize_payment_mode(value) -> str:
	key = (str(value or "").strip().upper())
	mapping = {
		"CA": "CA",
		"CASH": "CA",
		"CH": "CH",
		"CHEQUE": "CH",
		"CHECK": "CH",
		"BK": "BK",
		"BANK": "BK",
		"TC": "TC",
		"TRAVELLERS CHEQUE": "TC",
		"TRAVELERS CHEQUE": "TC",
	}
	return mapping.get(key, key[:2] if key else "")
