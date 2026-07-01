# Copyright (c) 2026, Millitrix and contributors
# Blueprint Sections 5.2, 5.3, 22

from __future__ import annotations

import frappe
from frappe.utils import flt, round_based_on_smallest_currency_fraction

from millitrix.utils.bardana_items import is_bardana_item
from millitrix.utils.invoice_fields import (
	is_brokery_paid,
	is_yes,
	normalize_amntby,
	normalize_bags_are,
	normalize_kantatype,
	normalize_mundtype_code,
)
from millitrix.utils.mund import kg_to_mund


def _round_money(amount, doc=None) -> float:
	currency = (getattr(doc, "currency", None) if doc else None) or "PKR"
	try:
		return round_based_on_smallest_currency_fraction(amount, currency)
	except RuntimeError:
		return round(flt(amount), 2)


def _line_total_weight_kg(line) -> float:
	"""Oracle TOTALWEIGHT — BagQty × BagWeight (fallback TruckQty × BagWeight)."""
	if flt(line.bagweight) > 0 and flt(line.bagqty) > 0:
		return flt(line.bagqty) * flt(line.bagweight)
	if flt(line.bagweight) > 0 and flt(line.truckqty) > 0:
		return flt(line.truckqty) * flt(line.bagweight)
	return 0.0


def _doctype_flags(header, is_purchase: bool) -> tuple[bool, bool, bool]:
	"""Return (use_purchase_bags, apply_dust, use_inkanta) for line calcs."""
	dt = getattr(header, "doctype", "") or ""
	if dt == "Purchase Invoice":
		return True, True, True
	if dt == "Purchase Return":
		return True, False, False
	if dt == "Sales Return":
		return False, False, True
	if dt == "Sales Invoice":
		return False, False, False
	return is_purchase, is_purchase, is_purchase


def kanta_weight(line, kantatype: str, *, is_purchase: bool = False, header=None) -> float:
	kt = normalize_kantatype(kantatype)
	_, _, use_inkanta = _doctype_flags(header, is_purchase) if header else (is_purchase, is_purchase, is_purchase)
	if kt in ("T", "W"):
		tw = _line_total_weight_kg(line)
		if tw > 0:
			return tw
		return flt(line.delikanta)
	if kt == "I":
		return flt(getattr(line, "inkanta", 0)) if use_inkanta else 0.0
	if kt == "D":
		return flt(line.delikanta)
	return flt(line.truckqty)


def display_total_weight(line, kantatype: str, *, header=None) -> float:
	"""Oracle TOTALWEIGHT — BagQty × BagWeight when bags set, else kanta sum."""
	tw = _line_total_weight_kg(line)
	if tw > 0:
		return tw
	return kanta_weight(line, kantatype, header=header)


def calc_net_weight(line, kantatype: str, *, is_purchase: bool = False, header=None) -> float:
	_, apply_dust, _ = _doctype_flags(header, is_purchase) if header else (is_purchase, is_purchase, is_purchase)
	weight = kanta_weight(line, kantatype, is_purchase=is_purchase, header=header) - flt(
		getattr(line, "lessweight", 0)
	)
	if apply_dust:
		weight -= flt(getattr(line, "dust", 0))
	return max(flt(weight), 0)


def calc_bagamnt(line, *, is_purchase: bool = False) -> float:
	"""Oracle Bardana — PU on purchase, SA on sales; else zero."""
	bags_are = normalize_bags_are(getattr(line, "bags_are", None))
	if is_purchase:
		if bags_are != "PU":
			return 0.0
	else:
		if bags_are != "SA":
			return 0.0
	return flt(line.bagqty) * flt(line.bagrate)


def populate_order_rate(line, *, is_purchase: bool) -> None:
	if not hasattr(line, "order_rate"):
		return
	if is_purchase and getattr(line, "ponumber", None):
		line.order_rate = flt(frappe.db.get_value("Purchase Order", line.ponumber, "rate"))
	elif not is_purchase and getattr(line, "sonumber", None):
		line.order_rate = flt(frappe.db.get_value("Sales Order", line.sonumber, "rate"))
	else:
		line.order_rate = 0


def populate_brokery_mund(line, mundtype: str, *, is_purchase: bool, netweight: float = 0) -> None:
	if not is_purchase or not hasattr(line, "brokery_mund"):
		return
	net = flt(netweight)
	mund_kg = net + flt(getattr(line, "dust", 0)) + flt(getattr(line, "lessweight", 0))
	line.brokery_mund = round(flt(kg_to_mund(mund_kg, mundtype)), 2)


def line_weight_qty(
	line,
	kantatype: str,
	*,
	is_purchase: bool = False,
	header=None,
) -> float:
	"""Grain qty for stock — netweight or truckqty when kanta Q."""
	if normalize_kantatype(kantatype) == "Q":
		return flt(line.truckqty)
	net = flt(line.netweight)
	if net > 0:
		return net
	if header is not None:
		doctype = getattr(header, "doctype", "") or ""
		if doctype == "Purchase Return":
			is_purchase = True
		elif doctype == "Sales Return":
			is_purchase = False
	return calc_net_weight(line, kantatype, is_purchase=is_purchase, header=header)


def line_base_amount(line, amntby: str, mundtype: str, kantatype: str, *, is_purchase: bool = False, header=None) -> float:
	itemcode = getattr(header, "itemcode", None) if header else getattr(line, "itemcode", None)
	if is_bardana_item(itemcode):
		return round(flt(line.truckqty) * flt(line.rate))
	net = flt(line.netweight) or calc_net_weight(line, kantatype, is_purchase=is_purchase, header=header)
	ab = normalize_amntby(amntby)
	if ab == "B":
		return round(flt(line.bagqty) * flt(line.rate))
	if ab == "M":
		mund = kg_to_mund(net, mundtype or "N")
		return round(mund * flt(line.rate))
	return round(flt(line.truckqty) * flt(line.rate))


def calc_line_totals(line, header, *, is_purchase: bool = False) -> dict:
	use_purchase_bags, _, _ = _doctype_flags(header, is_purchase)
	kantatype = header.kantatype
	mundtype = _mund_code(header)
	total_weight = display_total_weight(line, kantatype, header=header)
	net = calc_net_weight(line, kantatype, is_purchase=is_purchase, header=header)
	bagamnt = calc_bagamnt(line, is_purchase=use_purchase_bags)
	mund = kg_to_mund(net, mundtype)
	base = line_base_amount(
		line,
		header.amntby,
		mundtype,
		kantatype,
		is_purchase=is_purchase,
		header=header,
	)
	# Oracle: TotalAmnt = base + Bardana − Discount (broker + labour are separate columns).
	total = round(base + bagamnt - flt(getattr(line, "discount", 0)))
	populate_order_rate(line, is_purchase=is_purchase)
	populate_brokery_mund(line, mundtype, is_purchase=is_purchase, netweight=net)
	if hasattr(line, "bardana"):
		line.bardana = round(flt(bagamnt), 2)
	return {
		"total_weight": round(flt(total_weight), 2),
		"netweight": net,
		"mund": round(flt(mund), 2),
		"bagamnt": round(flt(bagamnt), 2),
		"totalamnt": round(flt(total), 2),
	}


def recalc_invoice_lines(doc, *, is_purchase: bool = False) -> None:
	total_header = 0.0
	for line in doc.details or []:
		calc = calc_line_totals(line, doc, is_purchase=is_purchase)
		line.total_weight = calc["total_weight"]
		line.netweight = calc["netweight"]
		line.mund = calc["mund"]
		line.bagamnt = calc["bagamnt"]
		line.totalamnt = calc["totalamnt"]
		total_header += calc["totalamnt"]
	doc.amount = round(flt(total_header), 2)
	from millitrix.utils.brokery import apply_brokery_auto, apply_sales_return_brokery

	doctype = getattr(doc, "doctype", "")
	if doctype == "Sales Return":
		apply_sales_return_brokery(doc)
	else:
		apply_brokery_auto(doc, is_purchase=is_purchase)
	recalc_invoice_header(doc, is_purchase=is_purchase)


def _header_total(
	doc,
	amount: float,
	total_labour: float,
	total_cartage: float,
	total_truck_adv: float,
) -> float:
	"""Oracle commit blocks — borrow/labour rules differ per DocType."""
	borrow = (getattr(doc, "borrow", None) or "Delivery").strip().upper()
	dt = getattr(doc, "doctype", "") or ""
	amt = flt(amount)

	if dt == "Purchase Invoice":
		if borrow.startswith("X"):
			total = amt + total_truck_adv
		elif borrow.startswith("D"):
			total = amt - total_cartage
		else:
			total = amt
	elif dt == "Sales Invoice":
		if borrow.startswith("X"):
			total = amt + total_labour + total_truck_adv
		elif borrow.startswith("D"):
			total = amt + total_labour - total_cartage
		else:
			total = amt + total_labour
	elif dt == "Purchase Return":
		if borrow.startswith("D"):
			total = amt + total_labour - total_cartage
		else:
			total = amt + total_labour
	elif dt == "Sales Return":
		if borrow.startswith("D"):
			total = amt - total_cartage
		else:
			total = amt
	elif borrow.startswith("X"):
		total = amt + total_labour + total_truck_adv
	else:
		total = amt + total_labour - total_cartage
	return _round_money(total, doc)


def recalc_invoice_header(doc, *, is_purchase: bool = False) -> None:
	from millitrix.utils.brokery import calc_header_party_brokery

	total_cartage = sum(flt(line.cartage) for line in doc.details or [])
	total_truck_adv = sum(flt(getattr(line, "truckadv", 0)) for line in doc.details or [])
	total_broker = sum(flt(line.brokeramnt) for line in doc.details or [])
	total_labour = sum(flt(line.labouramnt) for line in doc.details or [])

	if hasattr(doc, "brokeramnt"):
		doc.brokeramnt = round(flt(total_broker), 2)
	if hasattr(doc, "brokerypayable"):
		doc.brokerypayable = 0 if is_brokery_paid(doc.brokery) else round(flt(total_broker), 2)

	amount = flt(doc.amount)
	header_total = _header_total(doc, amount, total_labour, total_cartage, total_truck_adv)

	doctype = getattr(doc, "doctype", "")
	if doctype == "Purchase Invoice":
		party_brokery = calc_header_party_brokery(doc, is_purchase=True)
		deduction = party_brokery if party_brokery > 0 else (
			flt(total_broker) if is_yes(getattr(doc, "brokery_dr_supplier", None)) else 0
		)
		payable = header_total - deduction
		if is_brokery_paid(doc.brokery):
			payable += flt(total_broker)
		doc.payable = _round_money(payable, doc)
	elif doctype == "Purchase Return":
		receivable = header_total
		if is_brokery_paid(doc.brokery):
			receivable -= flt(total_broker)
		doc.receivable = _round_money(receivable, doc)
	elif doctype == "Sales Invoice":
		receivable = header_total
		if is_brokery_paid(doc.brokery):
			receivable -= flt(total_broker)
		doc.receivable = _round_money(receivable, doc)
	elif doctype == "Sales Return":
		payable = header_total
		if is_brokery_paid(doc.brokery):
			payable += flt(total_broker)
		doc.payable = _round_money(payable, doc)
	elif is_purchase and hasattr(doc, "payable"):
		doc.payable = header_total
	elif hasattr(doc, "receivable"):
		doc.receivable = header_total


def _mund_code(header) -> str:
	return normalize_mundtype_code(header)


def open_truck_qty(order_qty: float, fulfilled: float, cancelled: float) -> float:
	return flt(order_qty) - flt(fulfilled) - flt(cancelled)


def grain_moving_rate(line, header, *, is_purchase: bool = True) -> float:
	"""Oracle PISUBMIT — in_value = TotalAmnt − BagAmnt; rate = in_value / qty."""
	qty = line_weight_qty(line, header.kantatype, is_purchase=is_purchase, header=header)
	grain_value = flt(line.totalamnt) - flt(line.bagamnt)
	if qty > 0 and grain_value > 0:
		return round(flt(grain_value / qty), 2)
	return flt(line.rate)
