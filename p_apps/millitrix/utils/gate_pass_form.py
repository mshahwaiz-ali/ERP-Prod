# Copyright (c) 2026, Millitrix and contributors
# Oracle GatePass.fmb — item/bag defaults and LOV queries.

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.bardana_items import get_bardana_item_class_id, is_bardana_item
from millitrix.utils.field_normalizers import is_yes
from millitrix.utils.invoice_fields import mundtype_code_from_value
from millitrix.utils.stock import get_in_store_item_name
from millitrix.utils.stock_key import StockKey


def _bag_stock_key(
	*,
	storeid: str,
	bagid: str,
	emptybags: str | None,
	itemcode: str | None,
) -> StockKey:
	bagitemcode = None if is_yes(emptybags) else (itemcode or None)
	return StockKey(
		storeid=storeid,
		itemcode=bagid,
		bagitemcode=bagitemcode,
		bags_are="PU",
	)


def get_header_item_defaults(
	*,
	location_id: str,
	itemcode: str,
	gpdate: str | None = None,
) -> dict:
	"""Oracle WHEN-VALIDATE (ITEMCODE) — mundtype, purchase rate, stockable."""
	if not itemcode:
		return {}
	item = frappe.db.get_value(
		"Item Setup",
		itemcode,
		["itemname", "mundtype", "stockable", "iclassid"],
		as_dict=True,
	)
	if not item:
		frappe.throw(frappe._("This item does not exist in master setup."))
	from millitrix.utils.item_price import get_item_rate

	rate = flt(get_item_rate(location_id, itemcode, gpdate, is_purchase=True))
	return {
		"mundtype": mundtype_code_from_value(item.mundtype),
		"rate": rate,
		"stockable": (item.stockable or "").strip(),
		"iclassid": (item.iclassid or "").strip(),
		"is_bardana": is_bardana_item(itemcode),
	}


def get_bag_line_defaults(
	*,
	location_id: str,
	storeid: str,
	bagid: str,
	emptybags: str | None = None,
	itemcode: str | None = None,
	gpdate: str | None = None,
) -> dict:
	"""Oracle BAGID select — bagweight + bagrate from store stock."""
	if not storeid or not bagid:
		return {}
	key = _bag_stock_key(
		storeid=storeid,
		bagid=bagid,
		emptybags=emptybags,
		itemcode=itemcode,
	)
	name = get_in_store_item_name(key)
	if not name:
		return {}
	stock = frappe.db.get_value(
		"Stock In Hand",
		name,
		["bagweight", "movingrate"],
		as_dict=True,
	) or {}
	return {
		"bagweight": flt(stock.get("bagweight")),
		"bagrate": flt(stock.get("movingrate")),
	}


@frappe.validate_and_sanitize_search_inputs
def search_header_item(doctype, txt, searchfield, start, page_len, filters):
	"""Oracle ITEMCODE LOV — stock in user stores or non-stockable items."""
	storeid = (filters or {}).get("storeid")
	location_id = (filters or {}).get("location_id")
	txt = f"%{txt or ''}%"
	if storeid:
		return frappe.db.sql(
			"""SELECT DISTINCT s.itemcode, i.itemname
			FROM `tabStock In Hand` s
			INNER JOIN `tabItem Setup` i ON i.name = s.itemcode
			WHERE s.storeid = %(storeid)s
			  AND IFNULL(s.bagitemcode, '') = ''
			  AND IFNULL(s.partyid, '') = ''
			  AND IFNULL(s.stock_in_hand, 0) > 0
			  AND (s.itemcode LIKE %(txt)s OR i.itemname LIKE %(txt)s)
			ORDER BY i.itemname
			LIMIT %(start)s, %(page_len)s""",
			{
				"storeid": storeid,
				"txt": txt,
				"start": start,
				"page_len": page_len,
			},
		)
	return frappe.db.sql(
		"""SELECT itemcode, itemname
		FROM `tabItem Setup`
		WHERE (stockable = 'No' OR stockable IS NULL OR stockable = '')
		  AND (itemcode LIKE %(txt)s OR itemname LIKE %(txt)s)
		ORDER BY itemname
		LIMIT %(start)s, %(page_len)s""",
		{"txt": txt, "start": start, "page_len": page_len},
	)


@frappe.validate_and_sanitize_search_inputs
def search_bagid(doctype, txt, searchfield, start, page_len, filters):
	"""Oracle BAGID LOV — empty or filled bardana in store."""
	storeid = (filters or {}).get("storeid")
	itemcode = (filters or {}).get("itemcode")
	emptybags = (filters or {}).get("emptybags") or "No"
	if not storeid:
		return []
	txt = f"%{txt or ''}%"
	bardana_class = get_bardana_item_class_id()
	class_filter = ""
	params: dict = {
		"storeid": storeid,
		"txt": txt,
		"start": start,
		"page_len": page_len,
	}
	if is_yes(emptybags):
		sql = """SELECT DISTINCT s.itemcode, i.itemname
		FROM `tabStock In Hand` s
		INNER JOIN `tabItem Setup` i ON i.name = s.itemcode
		WHERE s.storeid = %(storeid)s
		  AND IFNULL(s.bagitemcode, '') = ''
		  AND IFNULL(s.partyid, '') = ''
		  AND IFNULL(s.stock_in_hand, 0) > 0
		  AND (s.itemcode LIKE %(txt)s OR i.itemname LIKE %(txt)s)"""
		if bardana_class:
			sql += " AND i.iclassid = %(bardana_class)s"
			params["bardana_class"] = bardana_class
	else:
		if not itemcode:
			return []
		sql = """SELECT DISTINCT s.itemcode, i.itemname
		FROM `tabStock In Hand` s
		INNER JOIN `tabItem Setup` i ON i.name = s.itemcode
		WHERE s.storeid = %(storeid)s
		  AND s.bagitemcode = %(itemcode)s
		  AND IFNULL(s.partyid, '') = ''
		  AND IFNULL(s.stock_in_hand, 0) > 0
		  AND (s.itemcode LIKE %(txt)s OR i.itemname LIKE %(txt)s)"""
		params["itemcode"] = itemcode
	sql += " ORDER BY i.itemname LIMIT %(start)s, %(page_len)s"
	return frappe.db.sql(sql, params)
