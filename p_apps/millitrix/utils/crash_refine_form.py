# Copyright (c) 2026, Millitrix and contributors
# Oracle CrashRefine.fmb — line defaults and recalc helpers.

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.bardana_items import get_bardana_item_class_id
from millitrix.utils.invoice_fields import mundtype_code_from_value
from millitrix.utils.mill_setting import get_setting_value
from millitrix.utils.production_calc import prod_1_qty, prod_2_qty, recalc_input_line
from millitrix.utils.stock import get_in_store_item_name
from millitrix.utils.stock_key import StockKey

# Oracle PRODITEM: IClassId in ('102','105'). Also accept Item Class names/descriptions
# used on migrated sites (e.g. class 2 = Finished Goods).
FINISHED_ICLASS_ORACLE = ("102", "105")
EXCLUDED_OUTPUT_ICLASS = ("103", "104")


def finished_product_iclass_ids() -> list[str]:
	ids = set(FINISHED_ICLASS_ORACLE)
	for row in frappe.get_all("Item Class", fields=["name", "description"]):
		name = str(row.name or "").strip()
		desc = (row.description or "").lower()
		if name in EXCLUDED_OUTPUT_ICLASS:
			continue
		if "finish" in desc or "refine" in desc or "canola" in desc:
			ids.add(name)
	return sorted(ids)


def is_finished_product_iclass(iclassid: str | None) -> bool:
	iclass = str(iclassid or "").strip()
	return iclass in finished_product_iclass_ids()


def _grain_stock_row(storeid: str, itemcode: str) -> dict | None:
	if not storeid or not itemcode:
		return None
	name = get_in_store_item_name(StockKey(storeid=storeid, itemcode=itemcode, bags_are="PU"))
	if not name:
		return None
	return frappe.db.get_value(
		"Stock In Hand",
		name,
		["stock_in_hand", "movingrate", "bagweight"],
		as_dict=True,
	)


def _bag_stock_row(storeid: str, critem: str, crbagid: str) -> dict | None:
	if not storeid or not critem or not crbagid:
		return None
	name = get_in_store_item_name(
		StockKey(
			storeid=storeid,
			itemcode=crbagid,
			bagitemcode=critem,
			bags_are="PU",
		)
	)
	if not name:
		return None
	return frappe.db.get_value(
		"Stock In Hand",
		name,
		["stock_in_hand", "movingrate", "bagweight"],
		as_dict=True,
	)


def apply_critem_defaults(line, *, location_id: str, crdate: str | None = None) -> None:
	if not line.critem:
		return
	item = frappe.db.get_value(
		"Item Setup",
		line.critem,
		["itemname", "mundtype"],
		as_dict=True,
	)
	if not item:
		return

	line.mundtype = mundtype_code_from_value(item.mundtype)

	stock = _grain_stock_row(line.storeid, line.critem)
	if stock and flt(stock.movingrate) > 0:
		line.rate = flt(stock.movingrate)


def apply_bagdust_defaults(line, *, location_id: str, crdate: str | None = None) -> None:
	"""Oracle WHEN-VALIDATE (BAGDUST) — dust item + purchase rate when westage entered."""
	if not flt(line.bagdust):
		line.dustitemid = ""
		line.dust_rate = 0
		return
	dust_item = get_setting_value("Dust Item")
	if not dust_item:
		return
	line.dustitemid = dust_item
	from millitrix.utils.item_price import get_item_rate

	line.dust_rate = flt(get_item_rate(location_id, dust_item, crdate, is_purchase=True))


def apply_crbagid_defaults(line) -> None:
	if not line.crbagid or not line.critem:
		return
	stock = _bag_stock_row(line.storeid, line.critem, line.crbagid)
	if not stock:
		return
	if flt(stock.bagweight) > 0:
		line.bagweight = flt(stock.bagweight)
	if flt(stock.movingrate) > 0:
		line.bagrate = flt(stock.movingrate)


def get_input_line_defaults(
	*,
	location_id: str,
	storeid: str,
	critem: str | None = None,
	crbagid: str | None = None,
	crdate: str | None = None,
) -> dict:
	"""API helper — rate/mundtype from grain; bagweight/bagrate from filled bag stock."""
	line = frappe._dict(
		storeid=storeid,
		critem=critem,
		crbagid=crbagid,
		bagqty=0,
		bagweight=0,
		bagdust=0,
		rate=0,
		bagrate=0,
		mundtype="",
		dustitemid="",
		dust_rate=0,
	)
	if critem:
		apply_critem_defaults(line, location_id=location_id, crdate=crdate)
	if crbagid and critem:
		apply_crbagid_defaults(line)
	return {
		"rate": flt(line.rate),
		"bagrate": flt(line.bagrate),
		"bagweight": flt(line.bagweight),
		"mundtype": line.mundtype or "",
		"dustitemid": line.dustitemid or "",
		"dust_rate": flt(line.dust_rate),
	}


def get_bagdust_defaults(
	*,
	location_id: str,
	bagdust: float = 0,
	crdate: str | None = None,
) -> dict:
	line = frappe._dict(bagdust=bagdust, dustitemid="", dust_rate=0)
	if flt(bagdust):
		apply_bagdust_defaults(line, location_id=location_id, crdate=crdate)
	return {
		"dustitemid": line.dustitemid or "",
		"dust_rate": flt(line.dust_rate),
	}


def recalc_document_lines(doc) -> None:
	for line in doc.inputs or []:
		if flt(line.bagdust):
			apply_bagdust_defaults(line, location_id=doc.location_id or doc.mill_id, crdate=doc.crdate)
		recalc_input_line(line)
	recalc_output_lines(doc)


def recalc_output_lines(doc) -> None:
	"""Oracle PRODITEM — weight from CRITEM Prod.1/Prod.2 summed across all inputs."""
	inputs = doc.inputs or []
	if not inputs:
		return
	primary = inputs[0]
	storeid = primary.storeid or ""
	total_prod_1 = 0.0
	total_prod_2 = 0.0
	for inp in inputs:
		if flt(getattr(inp, "dip", 0)) <= 0:
			continue
		recalc_input_line(inp)
		total_prod_1 += prod_1_qty(inp)
		total_prod_2 += prod_2_qty(inp)
	for idx, out in enumerate(doc.outputs or []):
		if storeid:
			out.storeid = storeid
		if idx == 0 and total_prod_1:
			out.weight = flt(total_prod_1)
		elif idx == 1 and total_prod_2:
			out.weight = flt(total_prod_2)


def get_output_line_defaults(
	*,
	location_id: str,
	proditem: str,
	crdate: str | None = None,
) -> dict:
	"""Oracle WHEN-VALIDATE-ITEM (PRODITEM.PRODITEM) — name + purchase rate."""
	if not proditem:
		return {}
	item = frappe.db.get_value(
		"Item Setup",
		proditem,
		["itemname", "iclassid", "stockable"],
		as_dict=True,
	)
	if not item:
		frappe.throw(frappe._("This item does not exist in master setup."))
	iclass = (item.iclassid or "").strip()
	if not is_finished_product_iclass(iclass):
		frappe.throw(
			frappe._("Item {0} is not a finished product (class {1}). Use a Finishgoods class item.").format(
				proditem, iclass or "?"
			)
		)
	if (item.stockable or "").strip().lower() not in ("yes", "y", "1"):
		frappe.throw(frappe._("Item {0} is not stockable.").format(proditem))
	from millitrix.utils.item_price import get_item_rate

	rate = get_item_rate(location_id, proditem, crdate, is_purchase=True)
	if not rate:
		frappe.throw(frappe._("Please define purchase rate in rate list for item {0}.").format(proditem))
	return {
		"item_name": item.itemname or "",
		"rate": rate,
	}


@frappe.validate_and_sanitize_search_inputs
def search_crbagid(doctype, txt, searchfield, start, page_len, filters):
	"""Bag Id list — Oracle: IN_STORE_ITEMS where FILLED_ITEM = critem."""
	storeid = (filters or {}).get("storeid")
	critem = (filters or {}).get("critem")
	if not storeid or not critem:
		return []
	txt = f"%{txt or ''}%"
	return frappe.db.sql(
		"""SELECT DISTINCT s.itemcode, i.itemname
		FROM `tabStock In Hand` s
		LEFT JOIN `tabItem Setup` i ON i.name = s.itemcode
		WHERE s.storeid = %(storeid)s
		  AND s.bagitemcode = %(critem)s
		  AND IFNULL(s.stock_in_hand, 0) > 0
		  AND (s.itemcode LIKE %(txt)s OR i.itemname LIKE %(txt)s)
		ORDER BY i.itemname
		LIMIT %(start)s, %(page_len)s""",
		{
			"storeid": storeid,
			"critem": critem,
			"txt": txt,
			"start": start,
			"page_len": page_len,
		},
	)


def _excluded_grain_iclass_ids() -> tuple[str, ...]:
	excluded = {"103", "104"}
	bardana = get_bardana_item_class_id()
	if bardana:
		excluded.add(str(bardana))
	return tuple(sorted(excluded))


@frappe.validate_and_sanitize_search_inputs
def search_critem(doctype, txt, searchfield, start, page_len, filters):
	"""Input grain — Oracle CRITEM LOV: stock in store, not bardana class."""
	storeid = (filters or {}).get("storeid")
	if not storeid:
		return []
	txt = f"%{txt or ''}%"
	excluded = _excluded_grain_iclass_ids()
	if not excluded:
		return []
	return frappe.db.sql(
		"""SELECT DISTINCT s.itemcode, i.itemname
		FROM `tabStock In Hand` s
		INNER JOIN `tabItem Setup` i ON i.name = s.itemcode
		WHERE s.storeid = %(storeid)s
		  AND IFNULL(s.bagitemcode, '') = ''
		  AND IFNULL(s.partyid, '') = ''
		  AND IFNULL(s.stock_in_hand, 0) > 0
		  AND i.iclassid NOT IN %(excluded)s
		  AND (s.itemcode LIKE %(txt)s OR i.itemname LIKE %(txt)s)
		ORDER BY i.itemname
		LIMIT %(start)s, %(page_len)s""",
		{
			"storeid": storeid,
			"excluded": excluded,
			"txt": txt,
			"start": start,
			"page_len": page_len,
		},
	)


@frappe.validate_and_sanitize_search_inputs
def search_proditem(doctype, txt, searchfield, start, page_len, filters):
	"""Output ItemCode — Oracle: IClassId in (102,105), stockable Yes."""
	class_ids = finished_product_iclass_ids()
	if not class_ids:
		return []
	txt = f"%{txt or ''}%"
	return frappe.db.sql(
		"""SELECT itemcode, itemname
		FROM `tabItem Setup`
		WHERE stockable = 'Yes'
		  AND iclassid IN %(class_ids)s
		  AND (CAST(itemcode AS CHAR) LIKE %(txt)s OR itemname LIKE %(txt)s)
		ORDER BY itemname
		LIMIT %(start)s, %(page_len)s""",
		{
			"class_ids": tuple(class_ids),
			"txt": txt,
			"start": start,
			"page_len": page_len,
		},
	)
