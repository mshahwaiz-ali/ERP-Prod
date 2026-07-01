# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.order_balance import SIDE_PURCHASE, SIDE_SALES, open_truck_qty_for_order
from millitrix.utils.report_filters import normalize_report_dates


def _date_location_conditions(filters: dict, alias: str, date_field: str) -> tuple[list[str], dict]:
	conditions = [f"{alias}.docstatus = 1"]
	params: dict = {}

	if filters.get("from_date"):
		conditions.append(f"{alias}.{date_field} >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append(f"{alias}.{date_field} <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append(f"{alias}.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]

	return conditions, params


def get_purchase_invoice_register_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PInvRegister.RDF — purchase invoice detail lines with supplier/store/item names."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "pi", "invdate")
	if filters.get("supplierid"):
		conditions.append("pi.supplierid = %(supplierid)s")
		params["supplierid"] = filters["supplierid"]
	if filters.get("itemcode"):
		conditions.append("pi.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	return frappe.db.sql(
		f"""SELECT
			pi.purchinvno,
			pi.invdate,
			pi.location_id,
			pi.supplierid,
			party.party_name AS supplier_name,
			pi.itemcode,
			item.itemname AS item_name,
			pi.borrow,
			pi.amount AS invoice_amount,
			pi.payable,
			pi.posted,
			pi.remarks,
			d.ponumber,
			d.storeid,
			store.description AS store_name,
			d.truckno,
			d.bagqty,
			d.bagweight,
			d.netweight,
			d.rate,
			d.totalamnt AS line_amount
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Detail` d ON d.parent = pi.name
		LEFT JOIN `tabParty` party ON party.name = pi.supplierid
		LEFT JOIN `tabItem Setup` item ON item.name = pi.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		WHERE {" AND ".join(conditions)}
		ORDER BY pi.invdate, pi.purchinvno, d.idx
		""",
		params,
		as_dict=True,
	)


def get_sales_invoice_register_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SInvRegister.RDF — sales invoice detail lines with customer/store/item names."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "si", "invdate")
	if filters.get("customerid"):
		conditions.append("si.customerid = %(customerid)s")
		params["customerid"] = filters["customerid"]
	if filters.get("itemcode"):
		conditions.append("si.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	return frappe.db.sql(
		f"""SELECT
			si.salesinvno,
			si.invdate,
			si.location_id,
			si.customerid,
			party.party_name AS customer_name,
			si.itemcode,
			item.itemname AS item_name,
			si.borrow,
			si.amount AS invoice_amount,
			si.receivable,
			si.posted,
			si.remarks,
			d.sonumber,
			d.storeid,
			store.description AS store_name,
			d.truckno,
			d.bagqty,
			d.bagweight,
			d.netweight,
			d.rate,
			d.totalamnt AS line_amount
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Detail` d ON d.parent = si.name
		LEFT JOIN `tabParty` party ON party.name = si.customerid
		LEFT JOIN `tabItem Setup` item ON item.name = si.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		WHERE {" AND ".join(conditions)}
		ORDER BY si.invdate, si.salesinvno, d.idx
		""",
		params,
		as_dict=True,
	)


def get_purchase_order_pending_rows(filters: dict | None = None) -> list[dict]:
	from millitrix.utils.report_filters import normalize_report_filters

	filters = normalize_report_filters(filters)
	conditions = ["po.docstatus = 1", "po.status IN ('IN', 'IP', 'Initial', 'In Progress')"]
	params: dict = {}

	if filters.get("location_id"):
		conditions.append("po.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("supplierid"):
		conditions.append("po.supplierid = %(supplierid)s")
		params["supplierid"] = filters["supplierid"]
	if filters.get("itemcode"):
		conditions.append("po.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("brokerid"):
		conditions.append("po.brokerid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	if filters.get("sub_partyid"):
		conditions.append("po.sub_partyid = %(sub_partyid)s")
		params["sub_partyid"] = filters["sub_partyid"]
	if filters.get("from_date"):
		conditions.append("po.podate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("po.podate <= %(to_date)s")
		params["to_date"] = filters["to_date"]

	rows = frappe.db.sql(
		f"""SELECT
			po.name,
			po.ponumber,
			po.podate,
			po.location_id,
			po.supplierid,
			party.party_name AS supplier_name,
			po.itemcode,
			item.itemname AS item_name,
			po.status,
			po.truckqty,
			po.truckreceived,
			po.truckqtycancel,
			po.weight,
			po.rate,
			po.amount
		FROM `tabPurchase Order` po
		LEFT JOIN `tabParty` party ON party.name = po.supplierid
		LEFT JOIN `tabItem Setup` item ON item.name = po.itemcode
		WHERE {" AND ".join(conditions)}
		ORDER BY po.podate, po.ponumber
		""",
		params,
		as_dict=True,
	)

	pending: list[dict] = []
	for row in rows:
		open_qty = open_truck_qty_for_order(row.name, SIDE_PURCHASE)
		if open_qty <= 0:
			continue
		truckqty = flt(row.get("truckqty"))
		row.open_trucks = open_qty
		if truckqty:
			ratio = open_qty / truckqty
			row.open_weight = flt(row.get("weight")) * ratio
			row.open_amount = flt(row.get("amount")) * ratio
		else:
			row.open_weight = 0.0
			row.open_amount = 0.0
		pending.append(row)
	return pending


def get_pi_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PISummary.RDF — PI totals by supplier/item with names."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "pi", "invdate")
	if filters.get("supplierid"):
		conditions.append("pi.supplierid = %(supplierid)s")
		params["supplierid"] = filters["supplierid"]
	if filters.get("itemcode"):
		conditions.append("pi.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	return frappe.db.sql(
		f"""SELECT
			pi.location_id,
			pi.supplierid,
			party.party_name AS supplier_name,
			pi.itemcode,
			item.itemname AS item_name,
			COUNT(*) AS invoice_count,
			SUM(pi.amount) AS total_amount,
			SUM(pi.payable) AS total_payable
		FROM `tabPurchase Invoice` pi
		LEFT JOIN `tabParty` party ON party.name = pi.supplierid
		LEFT JOIN `tabItem Setup` item ON item.name = pi.itemcode
		WHERE {" AND ".join(conditions)}
		GROUP BY pi.location_id, pi.supplierid, party.party_name, pi.itemcode, item.itemname
		ORDER BY pi.location_id, pi.supplierid, pi.itemcode
		""",
		params,
		as_dict=True,
	)


def get_si_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SISummary.RDF — SI totals by customer/item with names and detail weights."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "si", "invdate")
	if filters.get("customerid"):
		conditions.append("si.customerid = %(customerid)s")
		params["customerid"] = filters["customerid"]
	if filters.get("itemcode"):
		conditions.append("si.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("brokerid"):
		conditions.append("si.brokerid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	return frappe.db.sql(
		f"""SELECT
			si.location_id,
			si.customerid,
			party.party_name AS customer_name,
			si.itemcode,
			item.itemname AS item_name,
			COUNT(DISTINCT si.name) AS invoice_count,
			SUM(COALESCE(d.bagweight, 0)) AS bagweight,
			SUM(COALESCE(d.netweight, 0)) AS netweight,
			SUM(COALESCE(d.brokeramnt, 0)) AS broker_amnt,
			SUM(COALESCE(si.amount, 0)) AS total_amount,
			SUM(COALESCE(si.receivable, 0)) AS total_receivable
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Detail` d ON d.parent = si.name
		LEFT JOIN `tabParty` party ON party.name = si.customerid
		LEFT JOIN `tabItem Setup` item ON item.name = si.itemcode
		WHERE {" AND ".join(conditions)}
		GROUP BY si.location_id, si.customerid, party.party_name, si.itemcode, item.itemname
		ORDER BY si.location_id, si.customerid, si.itemcode
		""",
		params,
		as_dict=True,
	)


def get_po_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle POSummary.RDF — PO totals by supplier/item/broker with names."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "po", "podate")
	if filters.get("supplierid"):
		conditions.append("po.supplierid = %(supplierid)s")
		params["supplierid"] = filters["supplierid"]
	if filters.get("itemcode"):
		conditions.append("po.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("brokerid"):
		conditions.append("po.brokerid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	return frappe.db.sql(
		f"""SELECT
			po.location_id,
			po.supplierid,
			party.party_name AS supplier_name,
			po.itemcode,
			item.itemname AS item_name,
			po.brokerid,
			broker.party_name AS broker_name,
			COUNT(*) AS order_count,
			SUM(po.truckqty) AS total_trucks,
			SUM(po.weight) AS total_weight,
			SUM(po.amount) AS total_amount
		FROM `tabPurchase Order` po
		LEFT JOIN `tabParty` party ON party.name = po.supplierid
		LEFT JOIN `tabItem Setup` item ON item.name = po.itemcode
		LEFT JOIN `tabParty` broker ON broker.name = po.brokerid
		WHERE {" AND ".join(conditions)}
		GROUP BY po.location_id, po.supplierid, party.party_name, po.itemcode, item.itemname,
			po.brokerid, broker.party_name
		ORDER BY po.location_id, po.supplierid, po.itemcode, po.brokerid
		""",
		params,
		as_dict=True,
	)


def get_so_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SOSummary.RDF — SO totals by customer/item/broker with names."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "so", "sodate")
	if filters.get("customerid"):
		conditions.append("so.customerid = %(customerid)s")
		params["customerid"] = filters["customerid"]
	if filters.get("itemcode"):
		conditions.append("so.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("brokerid"):
		conditions.append("so.brokerid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	return frappe.db.sql(
		f"""SELECT
			so.location_id,
			so.customerid,
			party.party_name AS customer_name,
			so.itemcode,
			item.itemname AS item_name,
			so.brokerid,
			broker.party_name AS broker_name,
			COUNT(*) AS order_count,
			SUM(so.truckqty) AS total_trucks,
			SUM(so.weight) AS total_weight,
			SUM(so.amount) AS total_amount
		FROM `tabSales Order` so
		LEFT JOIN `tabParty` party ON party.name = so.customerid
		LEFT JOIN `tabItem Setup` item ON item.name = so.itemcode
		LEFT JOIN `tabParty` broker ON broker.name = so.brokerid
		WHERE {" AND ".join(conditions)}
		GROUP BY so.location_id, so.customerid, party.party_name, so.itemcode, item.itemname,
			so.brokerid, broker.party_name
		ORDER BY so.location_id, so.customerid, so.itemcode, so.brokerid
		""",
		params,
		as_dict=True,
	)


def get_po_register_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PORegister.RDF — purchase orders with supplier city and item names."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "po", "podate")
	if filters.get("supplierid"):
		conditions.append("po.supplierid = %(supplierid)s")
		params["supplierid"] = filters["supplierid"]
	if filters.get("itemcode"):
		conditions.append("po.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	return frappe.db.sql(
		f"""SELECT
			po.ponumber,
			po.podate,
			po.location_id,
			po.supplierid,
			party.party_name AS supplier_name,
			city.cityname AS city_name,
			po.itemcode,
			item.itemname AS item_name,
			po.truckqty,
			po.weight,
			po.rate,
			po.amount,
			po.status,
			po.remarks
		FROM `tabPurchase Order` po
		LEFT JOIN `tabParty` party ON party.name = po.supplierid
		LEFT JOIN `tabCity Setup` city ON city.name = COALESCE(po.cityid, party.cityid)
		LEFT JOIN `tabItem Setup` item ON item.name = po.itemcode
		WHERE {" AND ".join(conditions)}
		ORDER BY po.podate, po.ponumber
		""",
		params,
		as_dict=True,
	)


def get_so_register_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SORegister.RDF — sales orders with customer/broker/delivery cities and item names."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "so", "sodate")
	if filters.get("customerid"):
		conditions.append("so.customerid = %(customerid)s")
		params["customerid"] = filters["customerid"]
	if filters.get("itemcode"):
		conditions.append("so.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("brokerid"):
		conditions.append("so.brokerid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	return frappe.db.sql(
		f"""SELECT
			so.sonumber,
			so.sodate,
			so.location_id,
			so.customerid,
			customer.party_name AS customer_name,
			cust_city.cityname AS cust_city,
			so.brokerid,
			broker.party_name AS broker_name,
			broker_city.cityname AS broker_city,
			deli_city.cityname AS deli_city,
			so.itemcode,
			item.itemname AS item_name,
			so.truckqty,
			so.weight,
			so.rate,
			so.amount,
			so.status,
			so.remarks
		FROM `tabSales Order` so
		LEFT JOIN `tabParty` customer ON customer.name = so.customerid
		LEFT JOIN `tabCity Setup` cust_city ON cust_city.name = customer.cityid
		LEFT JOIN `tabParty` broker ON broker.name = so.brokerid
		LEFT JOIN `tabCity Setup` broker_city ON broker_city.name = broker.cityid
		LEFT JOIN `tabCity Setup` deli_city ON deli_city.name = so.cityid
		LEFT JOIN `tabItem Setup` item ON item.name = so.itemcode
		WHERE {" AND ".join(conditions)}
		ORDER BY so.sodate, so.sonumber
		""",
		params,
		as_dict=True,
	)


def get_sales_order_pending_rows(filters: dict | None = None) -> list[dict]:
	from millitrix.utils.report_filters import normalize_report_filters

	filters = normalize_report_filters(filters)
	conditions = ["so.docstatus = 1", "so.status IN ('IN', 'IP', 'Initial', 'In Progress')"]
	params: dict = {}

	if filters.get("location_id"):
		conditions.append("so.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("customerid"):
		conditions.append("so.customerid = %(customerid)s")
		params["customerid"] = filters["customerid"]
	if filters.get("itemcode"):
		conditions.append("so.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("brokerid"):
		conditions.append("so.brokerid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	if filters.get("sub_partyid"):
		conditions.append("so.sub_partyid = %(sub_partyid)s")
		params["sub_partyid"] = filters["sub_partyid"]
	if filters.get("from_date"):
		conditions.append("so.sodate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("so.sodate <= %(to_date)s")
		params["to_date"] = filters["to_date"]

	rows = frappe.db.sql(
		f"""SELECT
			so.name,
			so.sonumber,
			so.sodate,
			so.location_id,
			so.customerid,
			party.party_name AS customer_name,
			city.cityname AS city_name,
			so.itemcode,
			item.itemname AS item_name,
			so.status,
			so.truckqty,
			so.truckissued,
			so.truckqtycancel,
			so.weight,
			so.rate,
			so.amount
		FROM `tabSales Order` so
		LEFT JOIN `tabParty` party ON party.name = so.customerid
		LEFT JOIN `tabCity Setup` city ON city.name = COALESCE(so.cityid, party.cityid)
		LEFT JOIN `tabItem Setup` item ON item.name = so.itemcode
		WHERE {" AND ".join(conditions)}
		ORDER BY so.sodate, so.sonumber
		""",
		params,
		as_dict=True,
	)

	pending: list[dict] = []
	for row in rows:
		open_qty = open_truck_qty_for_order(row.name, SIDE_SALES)
		if open_qty <= 0:
			continue
		truckqty = flt(row.get("truckqty"))
		row.open_trucks = open_qty
		if truckqty:
			ratio = open_qty / truckqty
			row.open_weight = flt(row.get("weight")) * ratio
			row.open_amount = flt(row.get("amount")) * ratio
		else:
			row.open_weight = 0.0
			row.open_amount = 0.0
		pending.append(row)
	return pending
