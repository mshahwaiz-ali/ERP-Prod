# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.fiscal import validate_fiscal_period
from millitrix.utils.mill_setting import get_setting_value
from millitrix.utils.stock import apply_stock_in, apply_stock_out, mark_posted, mark_unposted
from millitrix.utils.stock_key import StockKey


def validate(doc, method=None):
	validate_fiscal_period(doc.sadate)
	from millitrix.utils.child_table_helpers import strip_blank_child_rows
	from millitrix.utils.stock_adjustment_calc import recalc_adjustment_document

	strip_blank_child_rows(doc, "details", "Stock Adjustment Detail")
	if not doc.details:
		frappe.throw(_("Add at least one adjustment detail line"))

	recalc_adjustment_document(doc)

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)

	for line in doc.details:
		inc = flt(line.inc_stock)
		dec = flt(line.dec_stock)
		if inc > 0 and dec > 0:
			frappe.throw(_("Line cannot have both inc_stock and dec_stock"))
		if inc <= 0 and dec <= 0:
			frappe.throw(_("Line must have inc_stock or dec_stock"))
		if dec > 0:
			key = StockKey(
				storeid=line.storeid,
				itemcode=line.itemcode,
				bagitemcode=line.bagitemcode or None,
				partyid=line.partyid or None,
				bags_are=line.bags_are or None,
			)
			from millitrix.utils.reserved_stock import get_reserved_qty
			from millitrix.utils.stock import get_in_store_item_name

			name = get_in_store_item_name(key)
			stock = flt(frappe.db.get_value("Stock In Hand", name, "stock_in_hand")) if name else 0
			reserved = get_reserved_qty(
				key,
				exclude_doctype="Stock Adjustment",
				exclude_name=doc.name if doc.name else None,
			)
			if dec > stock - reserved + 1e-9:
				frappe.throw(
					_("Insufficient stock for Store {0}, Item {1}. Available {2}, required {3}").format(
						line.storeid, line.itemcode, stock - reserved, dec
					)
				)


def _mirror_party_bardana_store(doc, line, delta: float) -> None:
	"""Oracle Stock_Adjustment.fmb — party bardana also posts to Bardana Store."""
	if not line.partyid or abs(delta) < 1e-9:
		return
	bardana_store = get_setting_value("Bardana Store")
	if not bardana_store:
		return
	key = StockKey(
		storeid=bardana_store,
		itemcode=line.itemcode,
		bagitemcode=None,
		partyid=line.partyid,
		bags_are=line.bags_are or None,
	)
	if delta > 0:
		apply_stock_in(
			key,
			delta,
			rate=flt(line.rate),
			movement_date=doc.sadate,
		)
	else:
		apply_stock_out(key, -delta, movement_date=doc.sadate, check_reserved=False)


def on_submit(doc, method=None):
	for line in doc.details:
		key = StockKey(
			storeid=line.storeid,
			itemcode=line.itemcode,
			bagitemcode=line.bagitemcode or None,
			partyid=line.partyid or None,
			bags_are=line.bags_are or None,
		)
		inc = flt(line.inc_stock)
		dec = flt(line.dec_stock)
		delta = inc - dec
		if inc > 0:
			apply_stock_in(
				key,
				inc,
				rate=flt(line.rate),
				movement_date=doc.sadate,
				bagweight=flt(line.bagweight) or None,
			)
		elif dec > 0:
			apply_stock_out(key, dec, movement_date=doc.sadate, check_reserved=False)
		_mirror_party_bardana_store(doc, line, delta)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)