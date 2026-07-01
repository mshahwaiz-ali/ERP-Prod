# Copyright (c) 2026, Millitrix and contributors
# Oracle Stock_Adjustment.fmb — Bardana item class from PROJECT_PARA / Item Class master.

from __future__ import annotations

import frappe


def get_bardana_item_class_id() -> str | None:
	"""Item Class id for bardana sack items (Oracle PROJECT_PARA Description = Bardana)."""
	cached = frappe.cache.get_value("millitrix_bardana_iclass_id")
	if cached is not None:
		return cached or None

	iclassid = frappe.db.get_value(
		"Item Class",
		{"description": ("like", "%Bardana%")},
		"name",
		order_by="name asc",
	)
	frappe.cache.set_value("millitrix_bardana_iclass_id", iclassid or "")
	return iclassid or None


def is_bardana_item(itemcode: str | None) -> bool:
	if not itemcode:
		return False
	bardana_class = get_bardana_item_class_id()
	if not bardana_class:
		return False
	iclassid = frappe.db.get_value("Item Setup", itemcode, "iclassid")
	return str(iclassid or "") == str(bardana_class)


@frappe.validate_and_sanitize_search_inputs
def search_filled_bag_item(doctype, txt, searchfield, start, page_len, filters):
	"""Stock BAGITEMCODE — filled grain when line item is a bardana sack (Oracle STKADJDETL.BAGITEMCODE)."""
	itemcode = (filters or {}).get("itemcode")
	if not itemcode or not is_bardana_item(itemcode):
		return []

	bardana_class = get_bardana_item_class_id()
	if not bardana_class:
		return []

	txt = f"%{txt or ''}%"
	return frappe.db.sql(
		"""SELECT itemcode, itemname
		FROM `tabItem Setup`
		WHERE stockable = 'Yes'
		  AND IFNULL(iclassid, '') != %(bardana_class)s
		  AND (CAST(itemcode AS CHAR) LIKE %(txt)s OR itemname LIKE %(txt)s)
		ORDER BY itemcode
		LIMIT %(start)s, %(page_len)s""",
		{
			"bardana_class": bardana_class,
			"txt": txt,
			"start": start,
			"page_len": page_len,
		},
	)
