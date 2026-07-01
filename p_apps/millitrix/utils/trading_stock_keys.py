# Copyright (c) 2026, Millitrix and contributors
# Shared stock keys for trading documents (PI/SI/returns/gate pass).

from __future__ import annotations

from frappe.utils import flt

from millitrix.utils.borrow import effective_bardana_bags_are, should_move_our_bardana_stock
from millitrix.utils.field_normalizers import is_yes
from millitrix.utils.stock_key import StockKey


def trading_grain_key(*, itemcode: str, storeid: str) -> StockKey:
	"""Grain stock is always general PU; borrow affects bardana only."""
	return StockKey(
		storeid=storeid,
		itemcode=itemcode,
		partyid=None,
		bags_are="PU",
	)


def purchase_bardana_key(doc, line) -> StockKey | None:
	if not should_move_our_bardana_stock(doc):
		return None
	if not line.bagid or flt(line.bagqty) <= 0:
		return None
	bags_are = effective_bardana_bags_are(doc, line, is_purchase=True)
	if bags_are != "PU":
		return None
	bagitemcode = line.bagid
	partyid = doc.supplierid if bags_are == "PA" else None
	return StockKey(
		storeid=line.storeid,
		itemcode=line.bagid,
		bagitemcode=bagitemcode,
		partyid=partyid,
		bags_are=bags_are,
	)


def sales_bardana_key(doc, line) -> StockKey | None:
	if not should_move_our_bardana_stock(doc):
		return None
	if not line.bagid or flt(line.bagqty) <= 0:
		return None
	bags_are = effective_bardana_bags_are(doc, line, is_purchase=False)
	if bags_are != "SA":
		return None
	bagitemcode = None if is_yes(line.emptybags) else line.bagid
	partyid = doc.customerid if bags_are == "PA" else None
	return StockKey(
		storeid=line.storeid,
		itemcode=line.bagid,
		bagitemcode=bagitemcode,
		partyid=partyid,
		bags_are=bags_are,
	)
