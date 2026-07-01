# Copyright (c) 2026, Millitrix and contributors
# Brokery auto-calc from Party → Party Items child table.

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.invoice_calc import calc_bagamnt, calc_net_weight
from millitrix.utils.invoice_fields import is_brokery_paid, is_yes, normalize_kantatype, normalize_mundtype_code
from millitrix.utils.mund import kg_to_mund

BROKERY_BASIS = {
	"M": "Mund",
	"MUND": "Mund",
	"B": "Bag",
	"BAG": "Bag",
	"BAGS": "Bag",
	"Q": "Quantity",
	"QTY": "Quantity",
	"KG": "Quantity",
	"K": "Quantity",
	"T": "Truck",
	"TRUCK": "Truck",
	"P": "Percent",
	"PERCENT": "Percent",
	"%": "Percent",
}


def normalize_brokery_basis(value: str | None) -> str:
	if not value:
		return ""
	key = str(value).strip().upper()
	return BROKERY_BASIS.get(key, key)


def validate_party_item_row(row) -> None:
	if not row.itemcode:
		frappe.throw("Item is required on Party Item row")
	for field, label in (("value_type_1", "Brokery By 1"), ("value_type_2", "Brokery By 2")):
		basis = normalize_brokery_basis(getattr(row, field, None))
		if basis and basis not in ("Mund", "Bag", "Quantity", "Percent", "Truck"):
			frappe.throw(f"{label} must be Mund, Bag, Quantity, Truck, or Percent")
		rate_field = "value_1" if field == "value_type_1" else "value_2"
		if basis and flt(getattr(row, rate_field, 0)) <= 0:
			frappe.throw(f"Value is required when {label} is set")


def validate_unique_party_items(rows) -> None:
	seen: set[str] = set()
	for row in rows or []:
		if not row.itemcode:
			continue
		if row.itemcode in seen:
			frappe.throw(f"Duplicate item {row.itemcode} in Party Items")
		seen.add(row.itemcode)


def _party_item_row(partyid: str, itemcode: str) -> dict | None:
	party_name = frappe.db.get_value("Party", {"partyid": partyid}, "name") or partyid
	rows = frappe.get_all(
		"Party Item",
		filters={"parent": party_name, "itemcode": itemcode},
		fields=["value_type_1", "value_1", "value_type_2", "value_2"],
		limit=1,
	)
	return rows[0] if rows else None


def _brokery_from_basis(
	basis: str,
	rate: float,
	*,
	net_weight: float = 0,
	bagqty: float = 0,
	truckqty: float = 0,
	mundtype: str = "N",
	line_total: float = 0,
	discount: float = 0,
	bardana: float = 0,
	dust: float = 0,
	less_weight: float = 0,
	is_purchase: bool = False,
) -> float:
	if not basis or rate <= 0:
		return 0.0
	if basis == "Bag":
		return flt(bagqty) * rate
	if basis == "Truck":
		return flt(truckqty) * rate
	if basis == "Mund":
		mund_kg = flt(net_weight)
		if is_purchase:
			mund_kg += flt(dust) + flt(less_weight)
		return kg_to_mund(mund_kg, mundtype or "N") * rate
	if basis == "Quantity":
		return flt(net_weight) * rate
	if basis == "Percent":
		base = flt(line_total) + flt(discount) - flt(bardana)
		return flt(base * rate / 100, 2)
	return rate


def calc_brokery_amount(
	partyid: str,
	itemcode: str,
	*,
	net_weight: float = 0,
	bagqty: float = 0,
	truckqty: float = 0,
	mundtype: str = "N",
	brokery_by: str | None = None,
	brokery_rate: float | None = None,
	line_total: float = 0,
	discount: float = 0,
	bardana: float = 0,
	dust: float = 0,
	less_weight: float = 0,
	is_purchase: bool = False,
	rule_index: int = 1,
) -> float:
	"""Return brokery amount from party item row (rule 1 = value_type_1, rule 2 = value_type_2)."""
	if not partyid or not itemcode:
		return 0.0

	row = _party_item_row(partyid, itemcode)
	if not row:
		return 0.0

	if rule_index == 2:
		rate = flt(brokery_rate if brokery_rate is not None else row.value_2)
		basis = normalize_brokery_basis(brokery_by or row.value_type_2)
	else:
		rate = flt(brokery_rate if brokery_rate is not None else row.value_1)
		basis = normalize_brokery_basis(brokery_by or row.value_type_1)

	return _brokery_from_basis(
		basis,
		rate,
		net_weight=net_weight,
		bagqty=bagqty,
		truckqty=truckqty,
		mundtype=mundtype,
		line_total=line_total,
		discount=discount,
		bardana=bardana,
		dust=dust,
		less_weight=less_weight,
		is_purchase=is_purchase,
	)


def calc_header_party_brokery(doc, *, is_purchase: bool = False) -> float:
	"""Oracle Party_Brokery from Brk_value_2 when Brokery Debit Supplier = Yes."""
	if not is_purchase or not is_yes(getattr(doc, "brokery_dr_supplier", None)):
		return 0.0
	partyid = getattr(doc, "brokerid", None)
	if not partyid or not getattr(doc, "itemcode", None):
		return 0.0

	row = _party_item_row(partyid, doc.itemcode)
	if not row or not normalize_brokery_basis(row.value_type_2):
		return 0.0

	mundtype = normalize_mundtype_code(doc)
	kantatype = normalize_kantatype(getattr(doc, "kantatype", "Total Weight"))
	total_net = 0.0
	total_bagqty = 0.0
	total_truckqty = 0.0
	total_dust = 0.0
	total_less = 0.0
	line_total = 0.0
	total_discount = 0.0
	total_bardana = 0.0
	for line in doc.details or []:
		net = flt(line.netweight) or calc_net_weight(line, kantatype, is_purchase=is_purchase)
		bagamnt = flt(line.bagamnt) or calc_bagamnt(line, is_purchase=is_purchase)
		line_before_broker = flt(line.totalamnt) or (
			flt(line.rate) * flt(net) - flt(line.discount) + bagamnt
		)
		total_net += net
		total_bagqty += flt(line.bagqty)
		total_truckqty += flt(line.truckqty)
		total_dust += flt(getattr(line, "dust", 0))
		total_less += flt(getattr(line, "lessweight", 0))
		line_total += line_before_broker
		total_discount += flt(line.discount)
		total_bardana += bagamnt

	return round(
		calc_brokery_amount(
			partyid,
			doc.itemcode,
			net_weight=total_net,
			bagqty=total_bagqty,
			truckqty=total_truckqty,
			mundtype=mundtype,
			line_total=line_total,
			discount=total_discount,
			bardana=total_bardana,
			dust=total_dust,
			less_weight=total_less,
			is_purchase=True,
			rule_index=2,
		)
	)


def _round_broker_line(amount: float, *, is_purchase: bool) -> float:
	"""Oracle rounds sales line broker; purchase keeps 2dp."""
	return flt(amount) if is_purchase else round(flt(amount))


def apply_brokery_auto(doc, *, is_purchase: bool = False) -> None:
	if not is_yes(getattr(doc, "brokery_auto_calc", None)):
		return

	partyid = getattr(doc, "brokerid", None)
	if not partyid:
		return

	mundtype = normalize_mundtype_code(doc)

	total_brokery = 0.0
	kantatype = normalize_kantatype(getattr(doc, "kantatype", "Total Weight"))
	for line in doc.details or []:
		net = flt(line.netweight) or calc_net_weight(line, kantatype, is_purchase=is_purchase)
		bagamnt = flt(line.bagamnt) or calc_bagamnt(line, is_purchase=is_purchase)
		line_before_broker = flt(line.totalamnt) or (
			flt(line.rate) * flt(net) - flt(line.discount) + bagamnt
		)
		line_brokery = calc_brokery_amount(
			partyid,
			doc.itemcode,
			net_weight=net,
			bagqty=flt(line.bagqty),
			truckqty=flt(line.truckqty),
			mundtype=mundtype,
			line_total=line_before_broker,
			discount=flt(line.discount),
			bardana=bagamnt,
			dust=flt(getattr(line, "dust", 0)),
			less_weight=flt(getattr(line, "lessweight", 0)),
			is_purchase=is_purchase,
		)
		if hasattr(line, "brokeramnt"):
			line.brokeramnt = _round_broker_line(line_brokery, is_purchase=is_purchase)
		total_brokery += line_brokery

	if hasattr(doc, "brokeramnt"):
		doc.brokeramnt = flt(total_brokery, 2) if is_purchase else round(flt(total_brokery))


def apply_sales_return_brokery(doc) -> None:
	"""Oracle SalesReturn.fmb — broker from Customer Party_Items (value_type_1 / value_1)."""
	customerid = getattr(doc, "customerid", None)
	itemcode = getattr(doc, "itemcode", None)
	if getattr(doc, "salesinvno", None):
		if not customerid:
			customerid = frappe.db.get_value("Sales Invoice", doc.salesinvno, "customerid")
		if not itemcode:
			itemcode = frappe.db.get_value("Sales Invoice", doc.salesinvno, "itemcode")
	if not customerid or not itemcode:
		return

	if not _party_item_row(customerid, itemcode):
		return

	mundtype = normalize_mundtype_code(doc)
	kantatype = normalize_kantatype(getattr(doc, "kantatype", "Total Weight"))
	total_brokery = 0.0
	for line in doc.details or []:
		net = flt(line.netweight) or calc_net_weight(line, kantatype, is_purchase=False)
		bagamnt = flt(line.bagamnt) or calc_bagamnt(line, is_purchase=False)
		line_before_broker = flt(line.totalamnt) or (
			flt(line.rate) * flt(net) - flt(line.discount) + bagamnt
		)
		line_brokery = calc_brokery_amount(
			customerid,
			itemcode,
			net_weight=net,
			bagqty=flt(line.bagqty),
			truckqty=flt(line.truckqty),
			mundtype=mundtype,
			line_total=line_before_broker,
			discount=flt(line.discount),
			bardana=bagamnt,
			is_purchase=False,
		)
		if hasattr(line, "brokeramnt"):
			line.brokeramnt = _round_broker_line(line_brokery, is_purchase=False)
		total_brokery += line_brokery

	if hasattr(doc, "brokeramnt"):
		doc.brokeramnt = flt(total_brokery, 2)
	if hasattr(doc, "brokerypayable"):
		doc.brokerypayable = 0 if is_brokery_paid(getattr(doc, "brokery", None)) else flt(total_brokery, 2)
