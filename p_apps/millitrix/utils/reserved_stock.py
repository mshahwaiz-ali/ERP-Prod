# Copyright (c) 2026, Millitrix and contributors
# Blueprint Section 11.4 — VIEW_US_STOCK equivalent

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.stock_key import StockKey


def get_reserved_qty(
	key: StockKey,
	*,
	exclude_doctype: str | None = None,
	exclude_name: str | None = None,
) -> float:
	"""Reserved qty on unsubmitted (draft) OUT stock documents."""
	total = 0.0
	total += _reserved_from_gate_pass(key, exclude_doctype, exclude_name)
	total += _reserved_from_sales_invoice(key, exclude_doctype, exclude_name)
	total += _reserved_from_stock_transfer(key, exclude_doctype, exclude_name)
	total += _reserved_from_stock_adjustment(key, exclude_doctype, exclude_name)
	return flt(total)


def _reserved_from_gate_pass(key: StockKey, exclude_dt, exclude_name) -> float:
	"""Draft In Out Gate Pass with OUT-type gptype."""
	conditions = [
		"gp.docstatus = 0",
		"UPPER(gp.gptype) IN ('OUT', 'SALES', 'O')",
	]
	params: list = []

	if exclude_dt == "In Out Gate Pass" and exclude_name:
		conditions.append("gp.name != %s")
		params.append(exclude_name)

	conditions.append("d.storeid = %s")
	params.append(key.storeid)

	if key.partyid:
		conditions.append("gp.partyid = %s")
		params.append(key.partyid)
	else:
		conditions.append("(gp.partyid IS NULL OR gp.partyid = '')")

	if key.bags_are:
		conditions.append("d.bags_are = %s")
		params.append(key.bags_are)

	# Bardana line (bag item)
	if key.itemcode and frappe.db.exists("Item Setup", key.itemcode):
		conditions.append("(d.bagid = %s OR gp.itemcode = %s)")
		params.extend([key.itemcode, key.itemcode])
	else:
		conditions.append("gp.itemcode = %s")
		params.append(key.itemcode)

	qty = frappe.db.sql(
		f"""
		SELECT COALESCE(SUM(
			CASE
				WHEN d.bagid IS NOT NULL AND d.bagid != '' THEN COALESCE(d.bagqty, 0)
				ELSE COALESCE(NULLIF(d.netweight, 0), d.truckqty, 0)
			END
		), 0)
		FROM `tabGate Pass Detail` d
		INNER JOIN `tabIn Out Gate Pass` gp ON gp.name = d.parent
		WHERE {" AND ".join(conditions)}
		""",
		tuple(params),
	)[0][0]
	return flt(qty)


def _reserved_from_sales_invoice(key: StockKey, exclude_dt, exclude_name) -> float:
	"""Draft Sales Invoice lines reserve OUT grain / bardana stock."""
	conditions = ["si.docstatus = 0"]
	params: list = []

	if exclude_dt == "Sales Invoice" and exclude_name:
		conditions.append("si.name != %s")
		params.append(exclude_name)

	conditions.append("d.storeid = %s")
	params.append(key.storeid)

	if key.partyid and (key.bags_are or "").upper() == "SA":
		conditions.append("si.customerid = %s")
		params.append(key.partyid)
		conditions.append("d.bags_are = 'SA'")
		conditions.append("d.bagid = %s")
		params.append(key.itemcode)
		qty_expr = "COALESCE(d.bagqty, 0)"
	else:
		conditions.append("si.itemcode = %s")
		params.append(key.itemcode)
		if key.bags_are:
			conditions.append("d.bags_are = %s")
			params.append(key.bags_are)
		if key.partyid:
			conditions.append("si.customerid = %s")
			params.append(key.partyid)
		qty_expr = """
			CASE
				WHEN UPPER(si.kantatype) = 'Q' THEN COALESCE(d.truckqty, 0)
				ELSE COALESCE(NULLIF(d.netweight, 0), d.truckqty, 0)
			END
		"""

	qty = frappe.db.sql(
		f"""SELECT COALESCE(SUM({qty_expr}), 0)
		FROM `tabSales Invoice Detail` d
		INNER JOIN `tabSales Invoice` si ON si.name = d.parent
		WHERE {" AND ".join(conditions)}
		""",
		tuple(params),
	)[0][0]
	return flt(qty)


def _reserved_from_stock_transfer(key: StockKey, exclude_dt, exclude_name) -> float:
	conditions = ["st.docstatus = 0", "st.fromstoreid = %s"]
	params: list = [key.storeid]

	if exclude_dt == "Stock Transfer Note" and exclude_name:
		conditions.append("st.name != %s")
		params.append(exclude_name)

	conditions.append("st.itemcode = %s")
	params.append(key.itemcode)

	qty = frappe.db.sql(
		f"""SELECT COALESCE(SUM(COALESCE(NULLIF(d.netweight, 0), d.truckqty, 0)), 0)
		FROM `tabStock Transfer Detail` d
		INNER JOIN `tabStock Transfer Note` st ON st.name = d.parent
		WHERE {" AND ".join(conditions)}
		""",
		tuple(params),
	)[0][0]
	return flt(qty)


def _reserved_from_stock_adjustment(key: StockKey, exclude_dt, exclude_name) -> float:
	conditions = ["sa.docstatus = 0", "d.storeid = %s", "d.itemcode = %s"]
	params: list = [key.storeid, key.itemcode]

	if exclude_dt == "Stock Adjustment" and exclude_name:
		conditions.append("sa.name != %s")
		params.append(exclude_name)

	if key.partyid:
		conditions.append("d.partyid = %s")
		params.append(key.partyid)
	if key.bags_are:
		conditions.append("d.bags_are = %s")
		params.append(key.bags_are)

	qty = frappe.db.sql(
		f"""SELECT COALESCE(SUM(COALESCE(d.dec_stock, 0)), 0)
		FROM `tabStock Adjustment Detail` d
		INNER JOIN `tabStock Adjustment` sa ON sa.name = d.parent
		WHERE {" AND ".join(conditions)}
		""",
		tuple(params),
	)[0][0]
	return flt(qty)


def get_reserved_stock_rows() -> list[dict]:
	"""All reserved rows for script report."""
	rows = frappe.db.sql(
		"""
		SELECT gp.location_id AS location_id, d.storeid AS storeid,
			COALESCE(gp.itemcode, d.bagid) AS itemcode, gp.partyid AS partyid,
			d.bags_are AS bags_are,
			COALESCE(NULLIF(d.netweight, 0), d.truckqty, d.bagqty, 0) AS reserved_qty,
			'In Out Gate Pass' AS source_doctype, gp.name AS source_name, gp.gptype AS movement
		FROM `tabGate Pass Detail` d
		INNER JOIN `tabIn Out Gate Pass` gp ON gp.name = d.parent
		WHERE gp.docstatus = 0 AND UPPER(gp.gptype) IN ('OUT', 'SALES', 'O')

		UNION ALL

		SELECT si.location_id, d.storeid, si.itemcode, si.customerid, d.bags_are,
			CASE
				WHEN UPPER(si.kantatype) = 'Q' THEN COALESCE(d.truckqty, 0)
				ELSE COALESCE(NULLIF(d.netweight, 0), d.truckqty, 0)
			END,
			'Sales Invoice', si.name, 'OUT' FROM `tabSales Invoice Detail` d
		INNER JOIN `tabSales Invoice` si ON si.name = d.parent
		WHERE si.docstatus = 0

		UNION ALL

		SELECT st.location_id, st.fromstoreid, st.itemcode, st.partyid, d.bags_are,
			COALESCE(NULLIF(d.netweight, 0), d.truckqty, 0),'Stock Transfer Note', st.name, 'OUT' FROM `tabStock Transfer Detail` d
		INNER JOIN `tabStock Transfer Note` st ON st.name = d.parent
		WHERE st.docstatus = 0

		UNION ALL

		SELECT sa.location_id, d.storeid, d.itemcode, d.partyid, d.bags_are,
			COALESCE(d.dec_stock, 0),'Stock Adjustment', sa.name, 'OUT'
		FROM `tabStock Adjustment Detail` d
		INNER JOIN `tabStock Adjustment` sa ON sa.name = d.parent
		WHERE sa.docstatus = 0 AND COALESCE(d.dec_stock, 0) > 0
		""",
		as_dict=True,
	)
	return rows
