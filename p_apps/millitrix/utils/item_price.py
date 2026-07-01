# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe.utils import flt, getdate


def get_item_rate(
	location_id: str,
	itemcode: str,
	on_date: str | None = None,
	*,
	is_purchase: bool = False,
) -> float:
	"""Latest Item Price List rate for location/item on or before date."""
	if not location_id or not itemcode:
		return 0.0
	on_date = getdate(on_date or frappe.utils.today())
	rate_col = "purchrate" if is_purchase else "salesrate"
	rows = frappe.db.sql(
		f"""SELECT {rate_col}
		FROM `tabItem Price List`
		WHERE location_id = %s AND itemcode = %s AND ipdate <= %s
		ORDER BY ipdate DESC
		LIMIT 1""",
		(location_id, itemcode, on_date),
	)
	return flt(rows[0][0]) if rows else 0.0


def get_item_price_row(
	location_id: str,
	itemcode: str,
	on_date: str | None = None,
) -> dict | None:
	"""Latest Item Price List row for location/item on or before date."""
	if not location_id or not itemcode:
		return None
	on_date = getdate(on_date or frappe.utils.today())
	return frappe.db.get_value(
		"Item Price List",
		{"location_id": location_id, "itemcode": itemcode, "ipdate": ("<=", on_date)},
		["bagweight", "westage", "purchrate", "salesrate", "ipdate"],
		as_dict=True,
		order_by="ipdate desc",
	)


def get_item_westage(
	location_id: str,
	itemcode: str,
	on_date: str | None = None,
) -> float:
	"""Default westage factor from Item Price List (decimal, not %)."""
	row = get_item_price_row(location_id, itemcode, on_date)
	return flt(row.westage) if row else 0.0


def apply_price_list_to_invoice(doc, *, is_purchase: bool = False, rate_field: str = "rate") -> None:
	"""Fill blank line rates from Item Price List when header item matches."""
	if not doc.location_id or not getattr(doc, "itemcode", None):
		return
	on_date = getattr(doc, "invdate", None) or getattr(doc, "podate", None) or getattr(doc, "sodate", None)
	header_rate = get_item_rate(doc.location_id, doc.itemcode, on_date, is_purchase=is_purchase)
	if header_rate <= 0:
		return
	for line in doc.details or []:
		if flt(getattr(line, rate_field, 0)) <= 0:
			setattr(line, rate_field, header_rate)
