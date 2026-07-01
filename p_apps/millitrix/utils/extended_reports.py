# Copyright (c) 2026, Millitrix and contributors
# Oracle report helpers — batch 18 (invoice detail, summaries, party).

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate, today

from millitrix.utils.doctype_ids import (
	BROKER_INVOICE_PAYMENT,
	PAID_ADVANCE_ADJUSTMENT,
	PARTY_PAYMENT_VOUCHER,
	PARTY_RECEIPT_VOUCHER,
	PAYMENT_VOUCHER,
	PURCHASE_INVOICE,
	PURCHASE_INVOICE_PAYMENT,
	PURCHASE_OTHER_BILL,
	RECEIPT_VOUCHER,
	RECEIVED_ADVANCE_ADJUSTMENT,
	SALES_INVOICE,
	SALES_INVOICE_RECEIPT,
	SALES_OTHER_BILL,
)
from millitrix.utils.finance_reports import get_bank_account_accids, get_cash_book_rows, get_party_balance_summary
from millitrix.utils.gl_reports import aggregate_account_balances, get_voucher_gl_lines
from millitrix.utils.knockoff_docs import get_si_outstanding_rows
from millitrix.utils.report_filters import normalize_report_dates
from millitrix.utils.stock_reports import get_item_ledger_rows
from millitrix.utils.trading_reports import _date_location_conditions


def get_purch_invoice_detail_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PurchInvoice.RDF — PI detail lines with supplier/item/store names."""
	filters = normalize_report_dates(filters or {})
	conditions, params = _date_location_conditions(filters, "pi", "invdate")
	if filters.get("supplierid"):
		conditions.append("pi.supplierid = %(supplierid)s")
		params["supplierid"] = filters["supplierid"]
	if filters.get("itemcode"):
		conditions.append("pi.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("brokerid"):
		conditions.append("pi.brokerid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	return frappe.db.sql(
		f"""SELECT
			pi.purchinvno,
			pi.invdate,
			pi.location_id,
			pi.supplierid,
			supplier.party_name AS supplier_name,
			pi.sub_partyid,
			subparty.party_name AS sub_party_name,
			pi.brokerid,
			broker.party_name AS broker_name,
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
			d.truckqty,
			d.bagqty,
			d.bagweight,
			d.bags_are,
			d.lessweight,
			d.dust,
			d.netweight,
			d.bardana,
			d.bagamnt,
			d.rate,
			d.totalamnt
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Detail` d ON d.parent = pi.name
		LEFT JOIN `tabParty` supplier ON supplier.name = pi.supplierid
		LEFT JOIN `tabParty` subparty ON subparty.name = pi.sub_partyid
		LEFT JOIN `tabParty` broker ON broker.name = pi.brokerid
		LEFT JOIN `tabItem Setup` item ON item.name = pi.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		WHERE {" AND ".join(conditions)}
		ORDER BY pi.invdate, pi.purchinvno, d.idx
		""",
		params,
		as_dict=True,
	)


def get_sales_invoice_detail_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SalesInvoice.RDF — SI detail lines with customer/item/store names."""
	filters = normalize_report_dates(filters or {})
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
			si.salesinvno,
			si.invdate,
			si.location_id,
			si.customerid,
			customer.party_name AS customer_name,
			si.sub_partyid,
			subparty.party_name AS sub_party_name,
			si.brokerid,
			broker.party_name AS broker_name,
			si.itemcode,
			item.itemname AS item_name,
			si.borrow,
			si.kantatype,
			si.amount AS invoice_amount,
			si.receivable,
			si.posted,
			si.remarks,
			d.sonumber,
			d.storeid,
			store.description AS store_name,
			d.truckno,
			d.truckqty,
			d.bagqty,
			d.bagweight,
			d.bags_are,
			d.delikanta,
			d.lessweight,
			d.netweight,
			d.bagamnt,
			d.bardana,
			d.rate,
			d.labouramnt,
			d.brokeramnt,
			d.totalamnt
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Detail` d ON d.parent = si.name
		LEFT JOIN `tabParty` customer ON customer.name = si.customerid
		LEFT JOIN `tabParty` subparty ON subparty.name = si.sub_partyid
		LEFT JOIN `tabParty` broker ON broker.name = si.brokerid
		LEFT JOIN `tabItem Setup` item ON item.name = si.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		WHERE {" AND ".join(conditions)}
		ORDER BY si.invdate, si.salesinvno, d.idx
		""",
		params,
		as_dict=True,
	)


def get_purch_inv_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Invoice totals by supplier (Oracle PurchInvSummary.rep)."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "pi", "invdate")
	if filters.get("supplierid"):
		conditions.append("pi.supplierid = %(supplierid)s")
		params["supplierid"] = filters["supplierid"]
	return frappe.db.sql(
		f"""SELECT
			pi.location_id,
			pi.supplierid,
			COUNT(*) AS invoice_count,
			SUM(pi.amount) AS total_amount,
			SUM(pi.payable) AS total_payable
		FROM `tabPurchase Invoice` pi
		WHERE {" AND ".join(conditions)}
		GROUP BY pi.location_id, pi.supplierid
		ORDER BY pi.location_id, pi.supplierid
		""",
		params,
		as_dict=True,
	)


def get_sales_inv_summary_rows(filters: dict | None = None) -> list[dict]:
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "si", "invdate")
	if filters.get("customerid"):
		conditions.append("si.customerid = %(customerid)s")
		params["customerid"] = filters["customerid"]
	return frappe.db.sql(
		f"""SELECT
			si.location_id,
			si.customerid,
			COUNT(*) AS invoice_count,
			SUM(si.amount) AS total_amount,
			SUM(si.receivable) AS total_receivable
		FROM `tabSales Invoice` si
		WHERE {" AND ".join(conditions)}
		GROUP BY si.location_id, si.customerid
		ORDER BY si.location_id, si.customerid
		""",
		params,
		as_dict=True,
	)


def get_purch_item_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PurchItemSummary.RDF — PI weight/amount by item and supplier."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "pi", "invdate")
	if filters.get("itemcode"):
		conditions.append("pi.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("supplierid"):
		conditions.append("pi.supplierid = %(supplierid)s")
		params["supplierid"] = filters["supplierid"]
	rows = frappe.db.sql(
		f"""SELECT
			pi.location_id,
			pi.itemcode,
			item.itemname AS item_name,
			pi.supplierid,
			party.party_name AS supplier_name,
			city.cityname AS city_name,
			COUNT(DISTINCT pi.name) AS invoice_count,
			SUM(COALESCE(NULLIF(d.netweight, 0), d.truckqty, 0)) AS total_weight,
			SUM(COALESCE(d.lessweight, 0)) AS lessweight,
			SUM(COALESCE(d.dust, 0)) AS dust,
			SUM(COALESCE(d.totalamnt, 0)) AS line_amount,
			SUM(COALESCE(pi.amount, 0)) AS invoice_amount,
			SUM(COALESCE(pi.payable, 0)) AS payable
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Detail` d ON d.parent = pi.name
		LEFT JOIN `tabItem Setup` item ON item.name = pi.itemcode
		LEFT JOIN `tabParty` party ON party.name = pi.supplierid
		LEFT JOIN `tabCity Setup` city ON city.name = party.cityid
		WHERE {" AND ".join(conditions)}
		GROUP BY pi.location_id, pi.itemcode, item.itemname, pi.supplierid, party.party_name, city.cityname
		ORDER BY pi.location_id, pi.itemcode, pi.supplierid
		""",
		params,
		as_dict=True,
	)
	for row in rows:
		weight = flt(row.get("total_weight"))
		row["avg_rate"] = flt(row.get("line_amount")) / weight if weight else 0.0
	return rows


def get_sales_item_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SalesItemSummary.RDF — SI weight/amount by item and customer."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "si", "invdate")
	if filters.get("itemcode"):
		conditions.append("si.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("customerid"):
		conditions.append("si.customerid = %(customerid)s")
		params["customerid"] = filters["customerid"]
	rows = frappe.db.sql(
		f"""SELECT
			si.location_id,
			si.itemcode,
			item.itemname AS item_name,
			si.customerid,
			party.party_name AS customer_name,
			city.cityname AS city_name,
			COUNT(DISTINCT si.name) AS invoice_count,
			SUM(COALESCE(NULLIF(d.netweight, 0), d.truckqty, 0)) AS total_weight,
			SUM(COALESCE(d.lessweight, 0)) AS lessweight,
			SUM(COALESCE(d.totalamnt, 0)) AS line_amount,
			SUM(COALESCE(si.amount, 0)) AS invoice_amount,
			SUM(COALESCE(si.receivable, 0)) AS receivable
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Detail` d ON d.parent = si.name
		LEFT JOIN `tabItem Setup` item ON item.name = si.itemcode
		LEFT JOIN `tabParty` party ON party.name = si.customerid
		LEFT JOIN `tabCity Setup` city ON city.name = party.cityid
		WHERE {" AND ".join(conditions)}
		GROUP BY si.location_id, si.itemcode, item.itemname, si.customerid, party.party_name, city.cityname
		ORDER BY si.location_id, si.itemcode, si.customerid
		""",
		params,
		as_dict=True,
	)
	for row in rows:
		weight = flt(row.get("total_weight"))
		row["avg_rate"] = flt(row.get("line_amount")) / weight if weight else 0.0
	return rows


def get_po_inv_detail_rows(filters: dict | None = None) -> list[dict]:
	filters = normalize_report_dates(filters or {})
	conditions = ["po.docstatus = 1"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append("po.podate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("po.podate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append("po.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
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
			po.itemcode,
			item.itemname AS item_name,
			po.truckqty,
			po.amount AS po_amount,
			pi.purchinvno,
			pi.invdate,
			d.netweight,
			d.truckno,
			d.totalamnt AS line_amount
		FROM `tabPurchase Order` po
		LEFT JOIN `tabParty` party ON party.name = po.supplierid
		LEFT JOIN `tabItem Setup` item ON item.name = po.itemcode
		LEFT JOIN `tabPurchase Invoice Detail` d ON d.ponumber = po.name
		LEFT JOIN `tabPurchase Invoice` pi ON pi.name = d.parent AND pi.docstatus = 1
		WHERE {" AND ".join(conditions)}
		ORDER BY po.podate, po.ponumber, pi.invdate, pi.purchinvno, d.idx
		""",
		params,
		as_dict=True,
	)


def get_so_inv_detail_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SOInvDetail.RDF — sales orders with linked invoice lines."""
	filters = normalize_report_dates(filters or {})
	conditions = ["so.docstatus = 1"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append("so.sodate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("so.sodate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append("so.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	customer = filters.get("customerid") or filters.get("partyid")
	if customer:
		conditions.append("so.customerid = %(customerid)s")
		params["customerid"] = customer
	if filters.get("itemcode"):
		conditions.append("so.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	return frappe.db.sql(
		f"""SELECT
			so.sonumber,
			so.sodate,
			so.location_id,
			so.customerid,
			party.party_name,
			so.itemcode,
			item.itemname AS item_name,
			so.truckqty,
			so.amount AS so_amount,
			si.salesinvno,
			si.invdate,
			si.kantatype,
			d.truckno,
			d.bagqty,
			d.bagweight,
			d.netweight,
			CASE
				WHEN UPPER(si.kantatype) = 'D' THEN COALESCE(d.delikanta, 0)
				WHEN UPPER(si.kantatype) = 'W' THEN COALESCE(d.bagqty, 0) * COALESCE(d.bagweight, 0)
				ELSE COALESCE(d.netweight, 0)
			END AS kanta_weight,
			d.totalamnt AS line_amount
		FROM `tabSales Order` so
		LEFT JOIN `tabParty` party ON party.name = so.customerid
		LEFT JOIN `tabItem Setup` item ON item.name = so.itemcode
		LEFT JOIN `tabSales Invoice Detail` d ON d.sonumber = so.name
		LEFT JOIN `tabSales Invoice` si ON si.name = d.parent AND si.docstatus = 1
		WHERE {" AND ".join(conditions)}
		ORDER BY so.sodate, so.sonumber, si.invdate, si.salesinvno, d.idx
		""",
		params,
		as_dict=True,
	)


def _party_ids_from_field(doctype: str, field: str) -> set[str]:
	rows = frappe.db.sql(
		f"""
		SELECT DISTINCT `{field}` AS partyid
		FROM `tab{doctype}`
		WHERE docstatus = 1 AND `{field}` IS NOT NULL AND `{field}` != ''
		""",
		as_dict=True,
	)
	return {row.partyid for row in rows if row.partyid}


def get_supplier_ledger_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SupplierLedgerSummary.RDF — supplier GL opening + period Dr/Cr + balance (pcat 12)."""
	from frappe.utils import add_days, getdate

	from millitrix.utils.gl_reports import get_voucher_gl_lines

	filters = normalize_report_dates(filters or {})
	suppliers = frappe.get_all("Party", filters={"pcat_id": 12}, fields=["name", "party_name"], order_by="name")
	if filters.get("partyid"):
		suppliers = [row for row in suppliers if row.name == filters["partyid"]]
	if not suppliers:
		return []

	opening_end = str(add_days(getdate(filters["from_date"]), -1))
	show_zero = int(filters.get("show_zero") or 0)
	rows: list[dict] = []
	for supplier in suppliers:
		partyid = supplier.name
		open_filters = {**filters, "partyid": partyid, "to_date": opening_end}
		open_filters.pop("from_date", None)
		open_lines = get_voucher_gl_lines(open_filters)
		open_dr = sum(flt(line.debit) for line in open_lines)
		open_cr = sum(flt(line.credit) for line in open_lines)
		opening_balance = flt(open_cr - open_dr)

		period_filters = {**filters, "partyid": partyid}
		period_lines = get_voucher_gl_lines(period_filters)
		period_dr = sum(flt(line.debit) for line in period_lines)
		period_cr = sum(flt(line.credit) for line in period_lines)
		balance = flt(opening_balance + period_cr - period_dr)

		if not show_zero and not any(
			abs(v) > 0.009 for v in (opening_balance, period_dr, period_cr, balance)
		):
			continue
		rows.append(
			{
				"partyid": partyid,
				"party_name": supplier.party_name or partyid,
				"opening_balance": opening_balance,
				"total_debit": period_dr,
				"total_credit": period_cr,
				"balance": balance,
			}
		)
	return rows


def get_cust_ledger_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle CustLedgerSummary.RDF — customer GL opening + period Dr/Cr + balance (pcat 13)."""
	from frappe.utils import add_days, getdate

	filters = normalize_report_dates(filters or {})
	customers = frappe.get_all("Party", filters={"pcat_id": 13}, fields=["name", "party_name"], order_by="name")
	if filters.get("partyid"):
		customers = [row for row in customers if row.name == filters["partyid"]]
	if not customers:
		return []

	opening_end = str(add_days(getdate(filters["from_date"]), -1))
	show_zero = int(filters.get("show_zero") or 0)
	rows: list[dict] = []
	for cust in customers:
		partyid = cust.name
		open_filters = {**filters, "partyid": partyid, "to_date": opening_end}
		open_filters.pop("from_date", None)
		open_lines = get_voucher_gl_lines(open_filters)
		open_dr = sum(flt(line.debit) for line in open_lines)
		open_cr = sum(flt(line.credit) for line in open_lines)
		opening_balance = flt(open_cr - open_dr)

		period_filters = {**filters, "partyid": partyid}
		period_lines = get_voucher_gl_lines(period_filters)
		period_dr = sum(flt(line.debit) for line in period_lines)
		period_cr = sum(flt(line.credit) for line in period_lines)
		balance = flt(opening_balance + period_cr - period_dr)

		if not show_zero and not any(
			abs(v) > 0.009 for v in (opening_balance, period_dr, period_cr, balance)
		):
			continue
		rows.append(
			{
				"partyid": partyid,
				"party_name": cust.party_name or partyid,
				"opening_balance": opening_balance,
				"total_debit": period_dr,
				"total_credit": period_cr,
				"balance": balance,
			}
		)
	return rows


def get_cust_aging_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle CustAging.RDF — customer SI outstanding by aging bucket."""
	filters = dict(filters or {})
	as_of = filters.get("as_of_date") or filters.get("to_date") or today()
	filters["as_of_date"] = str(getdate(as_of))
	customer_parties = {
		row.name: row.party_name
		for row in frappe.get_all("Party", filters={"pcat_id": 13}, fields=["name", "party_name"])
	}
	outstanding = get_si_outstanding_rows(filters)
	by_party: dict[str, dict] = {}
	for row in outstanding:
		party = row.get("partyid")
		if not party or party not in customer_parties:
			continue
		age_days = date_diff(as_of, row.get("invdate") or as_of)
		bucket = _aging_bucket(age_days)
		entry = by_party.setdefault(
			party,
			{
				"partyid": party,
				"party_name": customer_parties.get(party) or party,
				"location_id": row.get("location_id"),
				"current": 0.0,
				"days_31_60": 0.0,
				"days_61_90": 0.0,
				"over_90": 0.0,
				"total_outstanding": 0.0,
			},
		)
		amount = flt(row.get("docbalamnt"))
		entry[bucket] += amount
		entry["total_outstanding"] += amount
	return sorted(by_party.values(), key=lambda r: r["partyid"])


def _aging_bucket(age_days: int) -> str:
	if age_days <= 30:
		return "current"
	if age_days <= 60:
		return "days_31_60"
	if age_days <= 90:
		return "days_61_90"
	return "over_90"


def get_party_info_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle Party_Info.RDF — party master list filtered by category/city."""
	filters = filters or {}
	conditions = ["1=1"]
	params: dict = {}
	if filters.get("pcat_id"):
		conditions.append("p.pcat_id = %(pcat_id)s")
		params["pcat_id"] = filters["pcat_id"]
	if filters.get("cityid"):
		conditions.append("p.cityid = %(cityid)s")
		params["cityid"] = filters["cityid"]
	if filters.get("partyid"):
		conditions.append("p.name = %(partyid)s")
		params["partyid"] = filters["partyid"]
	return frappe.db.sql(
		f"""SELECT
			p.name AS partyid,
			p.party_name,
			p.pcat_id,
			cat.description AS category_name,
			p.cityid,
			city.cityname AS city_name,
			p.address,
			p.phno1,
			p.phno2,
			p.mobileno,
			p.resphno,
			p.creditlimit,
			p.creditdays
		FROM `tabParty` p
		LEFT JOIN `tabParty Category` cat ON cat.name = p.pcat_id
		LEFT JOIN `tabCity Setup` city ON city.name = p.cityid
		WHERE {" AND ".join(conditions)}
		ORDER BY p.partyid
		""",
		params,
		as_dict=True,
	)


def get_daily_item_purch_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle DailyItemPurch.RDF — daily purchase weight/amount/rate by item."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "pi", "invdate")
	if filters.get("itemcode"):
		conditions.append("pi.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	rows = frappe.db.sql(
		f"""SELECT
			pi.invdate AS tdate,
			pi.location_id,
			pi.itemcode,
			item.itemname AS item_name,
			SUM(COALESCE(d.netweight, 0)) AS total_weight,
			SUM(COALESCE(d.totalamnt, 0)) AS total_amount,
			COUNT(DISTINCT pi.name) AS invoice_count
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Detail` d ON d.parent = pi.name
		LEFT JOIN `tabItem Setup` item ON item.name = pi.itemcode
		WHERE {" AND ".join(conditions)}
		GROUP BY pi.invdate, pi.location_id, pi.itemcode, item.itemname
		ORDER BY pi.invdate, pi.location_id, pi.itemcode
		""",
		params,
		as_dict=True,
	)
	for row in rows:
		weight = flt(row.get("total_weight"))
		row["avg_rate"] = flt(row.get("total_amount")) / weight if weight else 0.0
	return rows


def get_daily_item_sales_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle DailyItemSales.RDF — daily sales weight/amount/rate by item."""
	filters = normalize_report_dates(filters)
	conditions, params = _date_location_conditions(filters, "si", "invdate")
	if filters.get("itemcode"):
		conditions.append("si.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	rows = frappe.db.sql(
		f"""SELECT
			si.invdate AS tdate,
			si.location_id,
			si.itemcode,
			item.itemname AS item_name,
			SUM(COALESCE(d.netweight, 0)) AS total_weight,
			SUM(COALESCE(d.totalamnt, 0)) AS total_amount,
			COUNT(DISTINCT si.name) AS invoice_count
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Detail` d ON d.parent = si.name
		LEFT JOIN `tabItem Setup` item ON item.name = si.itemcode
		WHERE {" AND ".join(conditions)}
		GROUP BY si.invdate, si.location_id, si.itemcode, item.itemname
		ORDER BY si.invdate, si.location_id, si.itemcode
		""",
		params,
		as_dict=True,
	)
	for row in rows:
		weight = flt(row.get("total_weight"))
		row["avg_rate"] = flt(row.get("total_amount")) / weight if weight else 0.0
	return rows


# --- Batch 19: payments, bank, bardana, stock bincard, expense ---

_PNR_KNOCKOFF_PARENTS = (
	PURCHASE_INVOICE_PAYMENT,
	SALES_INVOICE_RECEIPT,
	BROKER_INVOICE_PAYMENT,
	"Payment and Receipt Voucher",
)
_CNB_KNOCKOFF_PARENTS = (
	PAYMENT_VOUCHER,
	RECEIPT_VOUCHER,
	PARTY_PAYMENT_VOUCHER,
	PARTY_RECEIPT_VOUCHER,
	"Cash and Bank Voucher",
)
_ADJ_KNOCKOFF_PARENTS = (
	PAID_ADVANCE_ADJUSTMENT,
	RECEIVED_ADVANCE_ADJUSTMENT,
	"Advance Adjustment",
)


def _knockoff_date_conditions(filters: dict, alias: str, date_field: str) -> tuple[list[str], dict]:
	if filters.get("include_consider"):
		conditions = [f"{alias}.docstatus IN (0, 1)"]
	else:
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
	if filters.get("partyid"):
		conditions.append(f"{alias}.partyid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	return conditions, params


def _pnr_knockoff_rows(filters: dict, doctypeids: tuple[str, ...]) -> list[dict]:
	rows: list[dict] = []
	for parent_table in _PNR_KNOCKOFF_PARENTS:
		conditions, params = _knockoff_date_conditions(filters, "p", "pnrdate")
		conditions.append("ch.doctypeid IN %(doctypeids)s")
		params["doctypeids"] = doctypeids
		rows.extend(
			frappe.db.sql(
				f"""
				SELECT
					p.pnrno AS voucherno,
					p.pnrdate AS vouchdate,
					'PNR' AS source,
					p.pnrmode AS vouchmode,
					p.referno,
					p.location_id,
					p.partyid,
					ch.doctypeid,
					ch.documentid,
					ch.docbalamnt,
					ch.amount
				FROM `tabPayment and Receipt Document` ch
				INNER JOIN `tab{parent_table}` p ON p.name = ch.parent
				WHERE {" AND ".join(conditions)}
				ORDER BY p.pnrdate, p.pnrno, ch.idx
				""",
				params,
				as_dict=True,
			)
		)
	return sorted(rows, key=lambda r: (str(r.get("vouchdate") or ""), str(r.get("voucherno") or "")))


def _cnb_knockoff_rows(filters: dict, doctypeids: tuple[str, ...]) -> list[dict]:
	rows: list[dict] = []
	for parent_table in _CNB_KNOCKOFF_PARENTS:
		conditions, params = _knockoff_date_conditions(filters, "p", "vouchdate")
		conditions.append("ch.doctypeid IN %(doctypeids)s")
		params["doctypeids"] = doctypeids
		rows.extend(
			frappe.db.sql(
				f"""
				SELECT
					p.cnbvno AS voucherno,
					p.vouchdate AS vouchdate,
					'CNB' AS source,
					p.vouchmode,
					p.referno,
					p.location_id,
					ch.partyid,
					ch.doctypeid,
					ch.documentid,
					ch.docbalamnt,
					ch.amount
				FROM `tabCash and Bank Voucher Document` ch
				INNER JOIN `tab{parent_table}` p ON p.name = ch.parent
				WHERE {" AND ".join(conditions)}
				ORDER BY p.vouchdate, p.cnbvno, ch.idx
				""",
				params,
				as_dict=True,
			)
		)
	return sorted(rows, key=lambda r: (str(r.get("vouchdate") or ""), str(r.get("voucherno") or "")))


def _advance_adj_knockoff_rows(filters: dict, *, received: bool) -> list[dict]:
	doctypeid = RECEIVED_ADVANCE_ADJUSTMENT if received else PAID_ADVANCE_ADJUSTMENT
	rows: list[dict] = []
	for parent_table in _ADJ_KNOCKOFF_PARENTS:
		conditions, params = _knockoff_date_conditions(filters, "aa", "adjdate")
		if parent_table == "Advance Adjustment":
			conditions.append("aa.doctypeid = %(doctypeid)s")
			params["doctypeid"] = doctypeid
		rows.extend(
			frappe.db.sql(
				f"""
				SELECT
					aa.adjid AS voucherno,
					aa.adjdate AS vouchdate,
					'Advance Adjustment' AS source,
					'' AS vouchmode,
					'' AS referno,
					aa.location_id,
					aa.partyid,
					ch.doctypeid,
					ch.documentid,
					0 AS docbalamnt,
					ch.amount
				FROM `tabAdjustment Invoice` ch
				INNER JOIN `tab{parent_table}` aa ON aa.name = ch.parent
				WHERE {" AND ".join(conditions)}
				ORDER BY aa.adjdate, aa.adjid, ch.idx
				""",
				params,
				as_dict=True,
			)
		)
	return sorted(rows, key=lambda r: (str(r.get("vouchdate") or ""), str(r.get("voucherno") or "")))


def _enrich_purch_inv_payment_rows(rows: list[dict], filters: dict | None = None) -> list[dict]:
	filters = filters or {}
	invoice_cache: dict[str, dict] = {}
	out: list[dict] = []
	for row in rows:
		partyid = row.get("partyid")
		if partyid:
			row.setdefault("party_name", frappe.db.get_value("Party", partyid, "party_name"))
		docid = str(row.get("documentid") or "")
		doctypeid = row.get("doctypeid") or ""
		if doctypeid == PURCHASE_INVOICE and docid:
			if docid not in invoice_cache:
				invoice_cache[docid] = frappe.db.get_value(
					"Purchase Invoice",
					{"purchinvno": docid},
					["itemcode", "amount", "payable", "supplierid"],
					as_dict=True,
				) or {}
			inv = invoice_cache[docid]
			row["itemcode"] = inv.get("itemcode")
			row["invoice_amount"] = flt(inv.get("payable") or inv.get("amount"))
			if inv.get("itemcode"):
				row["item_name"] = frappe.db.get_value("Item Setup", inv["itemcode"], "itemname")
		if filters.get("itemcode") and row.get("itemcode") != filters["itemcode"]:
			continue
		out.append(row)
	return out


def get_purch_inv_payment_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PurchInvPayDetl — knockoff lines against purchase invoices."""
	filters = normalize_report_dates(filters or {})
	rows: list[dict] = []
	rows.extend(_pnr_knockoff_rows(filters, (PURCHASE_INVOICE, PURCHASE_OTHER_BILL)))
	rows.extend(_cnb_knockoff_rows(filters, (PURCHASE_INVOICE, PURCHASE_OTHER_BILL)))
	rows.extend(_advance_adj_knockoff_rows(filters, received=False))
	rows = _enrich_purch_inv_payment_rows(rows, filters)
	return sorted(rows, key=lambda r: (r.get("vouchdate") or "", r.get("voucherno") or 0))


def get_purch_inv_payment_register_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PurchInvPayment.RDF — payment voucher register (aggregated by voucher)."""
	rows = get_purch_inv_payment_rows(filters)
	agg: dict[tuple, dict] = {}
	for row in rows:
		key = (row.get("source") or "", row.get("voucherno") or "")
		bucket = agg.get(key)
		if not bucket:
			bucket = {**row, "amount": 0.0, "line_count": 0}
			agg[key] = bucket
		bucket["amount"] += flt(row.get("amount"))
		bucket["line_count"] += 1
		bucket.pop("documentid", None)
		bucket.pop("doctypeid", None)
		bucket.pop("docbalamnt", None)
		bucket.pop("itemcode", None)
		bucket.pop("item_name", None)
		bucket.pop("invoice_amount", None)
	return sorted(agg.values(), key=lambda r: (r.get("vouchdate") or "", r.get("voucherno") or ""))


def _enrich_sales_inv_receipt_rows(rows: list[dict], filters: dict | None = None) -> list[dict]:
	filters = filters or {}
	invoice_cache: dict[str, dict] = {}
	out: list[dict] = []
	for row in rows:
		partyid = row.get("partyid")
		if partyid:
			row.setdefault("party_name", frappe.db.get_value("Party", partyid, "party_name"))
		docid = str(row.get("documentid") or "")
		doctypeid = row.get("doctypeid") or ""
		if doctypeid == SALES_INVOICE and docid:
			if docid not in invoice_cache:
				invoice_cache[docid] = frappe.db.get_value(
					"Sales Invoice",
					{"salesinvno": docid},
					["itemcode", "amount", "receivable", "customerid"],
					as_dict=True,
				) or {}
			inv = invoice_cache[docid]
			row["itemcode"] = inv.get("itemcode")
			row["invoice_amount"] = flt(inv.get("receivable") or inv.get("amount"))
			if inv.get("itemcode"):
				row["item_name"] = frappe.db.get_value("Item Setup", inv["itemcode"], "itemname")
		if filters.get("itemcode") and row.get("itemcode") != filters["itemcode"]:
			continue
		out.append(row)
	return out


def get_sales_inv_receipt_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SalesInvRcptDetl — knockoff lines against sales invoices."""
	filters = normalize_report_dates(filters or {})
	rows: list[dict] = []
	rows.extend(_pnr_knockoff_rows(filters, (SALES_INVOICE, SALES_OTHER_BILL)))
	rows.extend(_cnb_knockoff_rows(filters, (SALES_INVOICE, SALES_OTHER_BILL)))
	rows.extend(_advance_adj_knockoff_rows(filters, received=True))
	rows = _enrich_sales_inv_receipt_rows(rows, filters)
	return sorted(rows, key=lambda r: (r.get("vouchdate") or "", r.get("voucherno") or 0))


def get_sales_inv_receipt_register_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SalesInvReceipt.RDF — receipt voucher register (aggregated by voucher)."""
	rows = get_sales_inv_receipt_rows(filters)
	agg: dict[tuple, dict] = {}
	for row in rows:
		key = (row.get("source") or "", row.get("voucherno") or "")
		bucket = agg.get(key)
		if not bucket:
			bucket = {**row, "amount": 0.0, "line_count": 0}
			agg[key] = bucket
		bucket["amount"] += flt(row.get("amount"))
		bucket["line_count"] += 1
		bucket.pop("documentid", None)
		bucket.pop("doctypeid", None)
		bucket.pop("docbalamnt", None)
		bucket.pop("itemcode", None)
		bucket.pop("item_name", None)
		bucket.pop("invoice_amount", None)
	return sorted(agg.values(), key=lambda r: (r.get("vouchdate") or "", r.get("voucherno") or ""))


def get_sip_outstanding_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SIPOutstanding.RDF — SI receivable totals by customer."""
	rows = get_si_outstanding_rows(filters)
	by_party: dict[str, dict] = {}
	for row in rows:
		party = row.get("partyid")
		if not party:
			continue
		entry = by_party.setdefault(
			party,
			{
				"partyid": party,
				"party_name": row.get("party_name") or "",
				"location_id": row.get("location_id"),
				"invoice_count": 0,
				"invoice_amount": 0.0,
				"applied": 0.0,
				"docbalamnt": 0.0,
			},
		)
		if not entry.get("party_name"):
			entry["party_name"] = row.get("party_name") or ""
		entry["invoice_count"] += 1
		entry["invoice_amount"] += flt(row.get("invoice_amount"))
		entry["applied"] += flt(row.get("applied"))
		entry["docbalamnt"] += flt(row.get("docbalamnt"))
	for entry in by_party.values():
		if not entry.get("party_name"):
			entry["party_name"] = (
				frappe.db.get_value("Party", entry.get("partyid"), "party_name") or entry.get("partyid") or ""
			)
	return sorted(by_party.values(), key=lambda r: r.get("party_name") or r.get("partyid") or "")


def get_bank_status_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle BankStatus.RDF — all bank accounts with opening + period + closing balance."""
	from frappe.utils import add_days, getdate

	from millitrix.utils.gl_reports import format_balance_side

	filters = normalize_report_dates(filters or {})
	opening_end = str(add_days(getdate(filters["from_date"]), -1))
	opening_balances = aggregate_account_balances(filters, before_date=opening_end)
	closing_balances = aggregate_account_balances(filters)
	query_filters: dict = {}
	if filters.get("location_id"):
		query_filters["location_id"] = filters["location_id"]
	bank_rows = frappe.get_all(
		"Bank Account",
		filters=query_filters or None,
		fields=["bankaccid", "location_id", "accid", "acc_description", "amntlimit"],
		order_by="location_id asc, bankaccid asc",
	)
	if not bank_rows:
		bank_accounts = set(get_bank_account_accids())
		out: list[dict] = []
		for accid in sorted(bank_accounts):
			open_bucket = opening_balances.get(accid, {"debit": 0.0, "credit": 0.0})
			close_bucket = closing_balances.get(accid, {"debit": 0.0, "credit": 0.0})
			open_dr = flt(open_bucket.get("debit"))
			open_cr = flt(open_bucket.get("credit"))
			period_dr = flt(close_bucket.get("debit")) - open_dr
			period_cr = flt(close_bucket.get("credit")) - open_cr
			opening_balance = open_dr - open_cr
			balance = flt(close_bucket.get("debit")) - flt(close_bucket.get("credit"))
			if not filters.get("show_zero_values") and not balance and not opening_balance:
				continue
			out.append(
				{
					"bankaccid": None,
					"accid": accid,
					"account_name": frappe.db.get_value("Chart of Accounting", accid, "description") or accid,
					"opening_balance": opening_balance,
					"debit": period_dr,
					"credit": period_cr,
					"balance": balance,
					"balance_side": format_balance_side(balance, "Assets"),
					"amntlimit": 0,
					"limit_balance": balance,
				}
			)
		return out

	out: list[dict] = []
	for row in bank_rows:
		if not row.accid:
			continue
		open_bucket = opening_balances.get(row.accid, {"debit": 0.0, "credit": 0.0})
		close_bucket = closing_balances.get(row.accid, {"debit": 0.0, "credit": 0.0})
		open_dr = flt(open_bucket.get("debit"))
		open_cr = flt(open_bucket.get("credit"))
		period_dr = flt(close_bucket.get("debit")) - open_dr
		period_cr = flt(close_bucket.get("credit")) - open_cr
		opening_balance = open_dr - open_cr
		balance = flt(close_bucket.get("debit")) - flt(close_bucket.get("credit"))
		limit = flt(row.amntlimit)
		if not filters.get("show_zero_values") and not balance and not opening_balance and not period_dr and not period_cr:
			continue
		out.append(
			{
				"bankaccid": row.bankaccid,
				"location_id": row.location_id,
				"accid": row.accid,
				"account_name": row.acc_description or frappe.db.get_value("Chart of Accounting", row.accid, "description") or row.accid,
				"opening_balance": opening_balance,
				"debit": period_dr,
				"credit": period_cr,
				"balance": balance,
				"balance_side": format_balance_side(balance, "Assets"),
				"amntlimit": limit,
				"limit_balance": flt(balance + limit) if limit else balance,
			}
		)
	return out


def get_bank_finance_status_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle BankFinanceStatus.RDF — finance accounts with limit and OD balance."""
	from frappe.utils import add_days, getdate

	from millitrix.utils.finance_reports import _BANK_FINANCE_NATURES
	from millitrix.utils.gl_reports import format_balance_side

	filters = normalize_report_dates(filters or {})
	opening_end = str(add_days(getdate(filters["from_date"]), -1))
	opening_balances = aggregate_account_balances(filters, before_date=opening_end)
	closing_balances = aggregate_account_balances(filters)
	query_filters: dict = {}
	if filters.get("location_id"):
		query_filters["location_id"] = filters["location_id"]
	bank_rows = frappe.get_all(
		"Bank Account",
		filters=query_filters or None,
		fields=[
			"bankaccid",
			"location_id",
			"location_description",
			"accid",
			"acc_description",
			"ac_nature",
			"amntlimit",
		],
		order_by="location_id asc, bankaccid asc",
	)
	out: list[dict] = []
	for row in bank_rows:
		if row.ac_nature not in _BANK_FINANCE_NATURES:
			continue
		open_bucket = opening_balances.get(row.accid, {"debit": 0.0, "credit": 0.0})
		close_bucket = closing_balances.get(row.accid, {"debit": 0.0, "credit": 0.0})
		opening_balance = flt(open_bucket.get("debit")) - flt(open_bucket.get("credit"))
		balance = flt(close_bucket.get("debit")) - flt(close_bucket.get("credit"))
		limit = flt(row.amntlimit)
		od_balance = flt(balance + limit)
		out.append(
			{
				"bankaccid": row.bankaccid,
				"location_id": row.location_id,
				"mill_name": row.location_description,
				"accid": row.accid,
				"account_name": row.acc_description,
				"ac_nature": row.ac_nature,
				"amntlimit": limit,
				"opening_balance": opening_balance,
				"balance": balance,
				"balance_side": format_balance_side(balance, "Assets"),
				"od_balance": od_balance,
				"available": flt(limit - balance) if limit else None,
			}
		)
	return out


def get_item_bincard_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle ItemBinCard.RDF — item/store ledger with opening B/F and running balance."""
	from frappe.utils import add_days, getdate

	if not (filters or {}).get("itemcode"):
		frappe.throw("Item is required for Item Bin Card")

	filters = normalize_report_dates(filters or {})
	itemcode = filters["itemcode"]
	item_name = frappe.db.get_value("Item Setup", itemcode, "itemname") or itemcode
	from_date = filters.get("from_date")
	store_filter = filters.get("storeid")

	opening_end = str(add_days(getdate(from_date), -1)) if from_date else None
	opening_by_store: dict[str, float] = {}
	if opening_end:
		open_filters = {**filters, "to_date": opening_end}
		open_filters.pop("from_date", None)
		for row in get_item_ledger_rows(open_filters):
			store = row.get("storeid") or ""
			qty = flt(row.get("qty"))
			if row.get("movement") == "IN":
				opening_by_store[store] = opening_by_store.get(store, 0.0) + qty
			else:
				opening_by_store[store] = opening_by_store.get(store, 0.0) - qty

	store_names = {
		row.name: row.description
		for row in frappe.get_all("Store Setup", fields=["name", "description"])
	}

	def _store_name(storeid: str | None) -> str:
		if not storeid:
			return ""
		return store_names.get(storeid) or storeid

	out: list[dict] = []
	balances: dict[str, float] = dict(opening_by_store)

	def _append_opening(storeid: str, balance: float) -> None:
		if abs(balance) <= 0.0001:
			return
		out.append(
			{
				"tdate": from_date,
				"location_id": filters.get("location_id") or "",
				"storeid": storeid,
				"store_name": _store_name(storeid),
				"itemcode": itemcode,
				"item_name": item_name,
				"movement": "",
				"qty": 0.0,
				"balance": flt(balance),
				"source": "",
				"documentid": "",
				"detail": _("Opening Balance"),
			}
		)

	if store_filter:
		_append_opening(store_filter, balances.get(store_filter, 0.0))
	else:
		for storeid in sorted(opening_by_store):
			_append_opening(storeid, opening_by_store[storeid])

	period_rows = sorted(
		get_item_ledger_rows(filters),
		key=lambda r: (r.get("tdate") or "", r.get("storeid") or "", r.get("documentid") or ""),
	)
	seen_stores: set[str] = set(opening_by_store)
	for row in period_rows:
		store = row.get("storeid") or ""
		if store not in seen_stores:
			seen_stores.add(store)
			_append_opening(store, balances.get(store, 0.0))
		qty = flt(row.get("qty"))
		if row.get("movement") == "IN":
			balances[store] = balances.get(store, 0.0) + qty
		else:
			balances[store] = balances.get(store, 0.0) - qty
		out.append(
			{
				**row,
				"store_name": _store_name(store),
				"item_name": item_name,
				"balance": flt(balances.get(store, 0.0)),
			}
		)
	return out


def get_item_daily_stock_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle ItemDailyStock.RDF — daily in/out with opening and closing balance per store/item."""
	from millitrix.utils.stock_reports import (
		_compute_stock_opening,
		_stock_ledger_key,
		_stock_name_maps,
	)

	filters = normalize_report_dates(filters or {})
	store_names, item_names, _party_names = _stock_name_maps()
	carry: dict[tuple[str, str], float] = _compute_stock_opening(filters)
	rows = get_item_ledger_rows(filters)
	agg: dict[tuple, dict] = {}
	for row in rows:
		key = (row.get("tdate"), row.get("location_id"), row.get("storeid"), row.get("itemcode"))
		bucket = agg.setdefault(
			key,
			{
				"tdate": row.get("tdate"),
				"location_id": row.get("location_id"),
				"storeid": row.get("storeid"),
				"itemcode": row.get("itemcode"),
				"stock_in": 0.0,
				"stock_out": 0.0,
			},
		)
		qty = flt(row.get("qty"))
		if row.get("movement") == "IN":
			bucket["stock_in"] += qty
		else:
			bucket["stock_out"] += qty

	out: list[dict] = []
	for key in sorted(agg.keys()):
		tdate, location_id, storeid, itemcode = key
		bucket = agg[key]
		si_key = (storeid or "", itemcode or "")
		opening_balance = flt(carry.get(si_key, 0.0))
		closing_balance = flt(opening_balance + bucket["stock_in"] - bucket["stock_out"])
		carry[si_key] = closing_balance
		out.append(
			{
				**bucket,
				"store_name": store_names.get(storeid or "") or storeid,
				"item_name": item_names.get(itemcode or "") or itemcode,
				"opening_balance": opening_balance,
				"closing_balance": closing_balance,
				"net_movement": flt(bucket["stock_in"] - bucket["stock_out"]),
			}
		)
	return out


def get_monthly_item_purch_rows(filters: dict | None = None) -> list[dict]:
	daily = get_daily_item_purch_rows(filters)
	agg: dict[tuple, dict] = {}
	for row in daily:
		month = str(row["tdate"])[:7] if row.get("tdate") else ""
		key = (month, row.get("location_id"), row.get("itemcode"))
		bucket = agg.setdefault(
			key,
			{
				"month": month,
				"location_id": row.get("location_id"),
				"itemcode": row.get("itemcode"),
				"item_name": row.get("item_name"),
				"total_weight": 0.0,
				"total_amount": 0.0,
				"invoice_count": 0,
			},
		)
		if not bucket.get("item_name"):
			bucket["item_name"] = row.get("item_name")
		bucket["total_weight"] += flt(row.get("total_weight"))
		bucket["total_amount"] += flt(row.get("total_amount"))
		bucket["invoice_count"] += int(row.get("invoice_count") or 0)
	rows_out: list[dict] = []
	for bucket in agg.values():
		weight = flt(bucket.get("total_weight"))
		bucket["avg_rate"] = flt(bucket.get("total_amount")) / weight if weight else 0.0
		rows_out.append(bucket)
	return sorted(rows_out, key=lambda r: (r["month"], r.get("itemcode") or ""))


def get_monthly_item_sales_rows(filters: dict | None = None) -> list[dict]:
	daily = get_daily_item_sales_rows(filters)
	agg: dict[tuple, dict] = {}
	for row in daily:
		month = str(row["tdate"])[:7] if row.get("tdate") else ""
		key = (month, row.get("location_id"), row.get("itemcode"))
		bucket = agg.setdefault(
			key,
			{
				"month": month,
				"location_id": row.get("location_id"),
				"itemcode": row.get("itemcode"),
				"item_name": row.get("item_name"),
				"total_weight": 0.0,
				"total_amount": 0.0,
				"invoice_count": 0,
			},
		)
		if not bucket.get("item_name"):
			bucket["item_name"] = row.get("item_name")
		bucket["total_weight"] += flt(row.get("total_weight"))
		bucket["total_amount"] += flt(row.get("total_amount"))
		bucket["invoice_count"] += int(row.get("invoice_count") or 0)
	rows_out: list[dict] = []
	for bucket in agg.values():
		weight = flt(bucket.get("total_weight"))
		bucket["avg_rate"] = flt(bucket.get("total_amount")) / weight if weight else 0.0
		rows_out.append(bucket)
	return sorted(rows_out, key=lambda r: (r["month"], r.get("itemcode") or ""))


def get_party_bardana_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PartyBardana.RDF — party bardana stock in hand by store."""
	filters = filters or {}
	conditions = ["(isi.partyid IS NOT NULL AND isi.partyid != '' OR UPPER(isi.bags_are) IN ('PA', 'PARTY'))"]
	params: dict = {}
	if filters.get("location_id"):
		conditions.append("ms.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("partyid"):
		conditions.append("isi.partyid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	if filters.get("storeid"):
		conditions.append("isi.storeid = %(storeid)s")
		params["storeid"] = filters["storeid"]
	if filters.get("itemcode"):
		conditions.append("isi.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if not filters.get("show_zero_stock"):
		conditions.append("isi.stock_in_hand != 0")
	return frappe.db.sql(
		f"""SELECT
			ms.location_id,
			ms.description AS store_name,
			isi.storeid,
			isi.partyid,
			party.party_name,
			isi.itemcode,
			item.itemname AS item_name,
			isi.bagitemcode,
			bag.itemname AS bag_item_name,
			CASE
				WHEN UPPER(isi.bags_are) = 'PA' THEN 'Party'
				WHEN UPPER(isi.bags_are) = 'OUR' THEN 'Our'
				ELSE isi.bags_are
			END AS bags_are,
			isi.opening_stock,
			isi.stock_in_hand,
			isi.bagweight,
			isi.ltdate
		FROM `tabStock In Hand` isi
		INNER JOIN `tabStore Setup` ms ON ms.name = isi.storeid
		LEFT JOIN `tabParty` party ON party.name = isi.partyid
		LEFT JOIN `tabItem Setup` item ON item.name = isi.itemcode
		LEFT JOIN `tabItem Setup` bag ON bag.name = isi.bagitemcode
		WHERE {" AND ".join(conditions)}
		ORDER BY ms.location_id, isi.partyid, isi.storeid, isi.itemcode
		""",
		params,
		as_dict=True,
	)


def get_expense_register_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle Expanse_Register.RDF — Expense Voucher (EV) detail lines with acc/cash-bank desc."""
	from millitrix.utils.finance_reports import _register_date_filters

	filters = normalize_report_dates(filters or {})
	conditions, params = _register_date_filters(filters, "ev", prefix="ev")
	return frappe.db.sql(
		f"""SELECT
			ev.location_id,
			ev.cnbvno AS documentid,
			ev.vouchdate AS doc_date,
			CASE
				WHEN UPPER(ev.paymode) = 'CASH' THEN 'Cash'
				ELSE TRIM(CONCAT(COALESCE(ba.acc_description, ''), ' ', COALESCE(cash_coa.description, '')))
			END AS description,
			ev.referno,
			ev.referdate,
			ev.paymode AS instrument,
			ev.amount AS doc_amount,
			COALESCE(tl.description, coa.description, d.accid) AS acc_desc,
			d.amount,
			d.detail,
			ev.narration
		FROM `tabExpense Voucher` ev
		INNER JOIN `tabExpense Voucher Detail` d ON d.parent = ev.name
		LEFT JOIN `tabTransaction List` tl ON tl.name = d.trans_id
		LEFT JOIN `tabChart of Accounting` coa ON coa.name = d.accid
		LEFT JOIN `tabBank Account` ba ON ba.accid = ev.bankaccid
		LEFT JOIN `tabChart of Accounting` cash_coa ON cash_coa.name = ev.bankaccid
		WHERE {" AND ".join(conditions)}
		ORDER BY ev.vouchdate, ev.cnbvno, d.idx
		""",
		params,
		as_dict=True,
	)


def _line_description(line: dict, *, party_names: dict, item_names: dict) -> str:
	partyid = line.get("partyid")
	if partyid:
		if partyid not in party_names:
			party_names[partyid] = frappe.db.get_value("Party", partyid, "party_name") or partyid
		return party_names[partyid]
	itemcode = line.get("itemcode")
	if itemcode:
		if itemcode not in item_names:
			item_names[itemcode] = frappe.db.get_value("Item Setup", itemcode, "itemname") or itemcode
		return item_names[itemcode]
	if line.get("detail"):
		return line["detail"]
	return line.get("account_name") or ""


def _voucher_counterpart_desc(
	filters: dict,
	*,
	cash_acc: str,
	bank_accounts: set[str],
) -> dict[str, str]:
	liquid = {cash_acc} | bank_accounts
	by_voucher: dict[str, list[dict]] = {}
	for line in get_voucher_gl_lines(filters):
		voucher_name = line.get("voucher_name")
		if not voucher_name:
			continue
		by_voucher.setdefault(voucher_name, []).append(line)

	party_names: dict[str, str] = {}
	item_names: dict[str, str] = {}
	counterparts: dict[str, str] = {}
	for voucher_name, lines in by_voucher.items():
		descs: list[str] = []
		for line in lines:
			if line.get("accid") in liquid:
				continue
			desc = _line_description(line, party_names=party_names, item_names=item_names)
			if desc and desc not in descs:
				descs.append(desc)
		counterparts[voucher_name] = ", ".join(descs)
	return counterparts


def get_cash_flow_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle CashFlow.RDF — cash + bank GL lines with Cash/Bank grouping."""
	from millitrix.utils.mill_setting import get_setting_account

	filters = normalize_report_dates(filters or {})
	cash_acc = get_setting_account("Cash")
	bank_accounts = set(get_bank_account_accids())
	counterpart_desc = _voucher_counterpart_desc(filters, cash_acc=cash_acc, bank_accounts=bank_accounts)

	cash_rows = get_cash_book_rows(filters, include_opening_bf=False)
	bank_rows = [row for row in get_voucher_gl_lines(filters) if row.get("accid") in bank_accounts]
	rows = cash_rows + bank_rows
	rows.sort(key=lambda r: (r.get("vouchdate") or "", r.get("voucherno") or 0))

	party_names: dict[str, str] = {}
	item_names: dict[str, str] = {}
	out: list[dict] = []
	for row in rows:
		accid = row.get("accid")
		cash_flow = "Bank" if accid in bank_accounts else "Cash"
		cash_desc = _line_description(row, party_names=party_names, item_names=item_names)
		voucher_name = row.get("voucher_name") or ""
		acc_desc = counterpart_desc.get(voucher_name, "")
		out.append(
			{
				**row,
				"cash_flow": cash_flow,
				"cash_desc": cash_desc,
				"acc_desc": acc_desc,
				"trans_type": row.get("vouchertype_id") or row.get("doctypeid") or "",
			}
		)
	if filters.get("cash_flow"):
		want = str(filters["cash_flow"]).strip().lower()
		out = [row for row in out if str(row.get("cash_flow") or "").lower() == want]
	return out
