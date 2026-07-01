# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.stock.stock_closing import preview_closing_stock_accounting_lines
from millitrix.utils.bardana_items import is_bardana_item, search_filled_bag_item


@frappe.whitelist()
def get_stock_balance(
	storeid: str,
	itemcode: str,
	bagitemcode: str | None = None,
	partyid: str | None = None,
	bags_are: str | None = None,
) -> dict:
	from millitrix.utils.stock import get_in_store_item_name
	from millitrix.utils.stock_key import StockKey

	frappe.has_permission("Stock Adjustment", "read", throw=True)
	key = StockKey(
		storeid=storeid,
		itemcode=itemcode,
		bagitemcode=bagitemcode or None,
		partyid=partyid or None,
		bags_are=bags_are or None,
	)
	name = get_in_store_item_name(key)
	if not name:
		return {"stock_in_hand": 0, "movingrate": 0}
	row = frappe.db.get_value(
		"Stock In Hand", name, ["stock_in_hand", "movingrate"], as_dict=True
	)
	return row or {"stock_in_hand": 0, "movingrate": 0}


@frappe.whitelist()
def is_bardana_line_item(itemcode: str | None = None) -> bool:
	frappe.has_permission("Item Setup", "read", throw=True)
	return is_bardana_item(itemcode)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def bagitem_query(doctype, txt, searchfield, start, page_len, filters):
	frappe.has_permission("Item Setup", "read", throw=True)
	return search_filled_bag_item(doctype, txt, searchfield, start, page_len, filters)


@frappe.whitelist()
def get_closing_stock_accounting_lines(name: str) -> list[dict]:
	doc = frappe.get_doc("Closing Stock", name)
	frappe.has_permission("Closing Stock", "read", doc=doc, throw=True)
	return preview_closing_stock_accounting_lines(doc)
