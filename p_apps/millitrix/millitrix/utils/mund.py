# Copyright (c) 2026, Millitrix and contributors
# Blueprint Section 5.1 — Mund Conversion

MUND_FACTORS = {
	"N": 40.0,
	"O": 37.324,
	"Q": 1.0,
}


def mund_factor(mundtype: str) -> float:
	return MUND_FACTORS.get((mundtype or "N").upper(), 40.0)


def kg_to_mund(net_weight_kg: float, mundtype: str) -> float:
	return net_weight_kg / mund_factor(mundtype)


def mund_to_kg(munds: float, mundtype: str) -> float:
	return munds * mund_factor(mundtype)


def default_bag_weight(mundtype: str) -> float:
	"""Default bardana bag weight (kg) when Item Master bag weight is blank."""
	if (mundtype or "N").upper() == "Q":
		return 1.0
	return 50.0
