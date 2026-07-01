# Copyright (c) 2026, Millitrix and contributors
# Oracle report helpers — batch 20 (final 11 reports).

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate

from millitrix.utils.doctype_ids import (
	ADVANCE_PAYMENT,
	BROKER_INVOICE_PAYMENT,
	PURCHASE_INVOICE,
	PURCHASE_OTHER_BILL,
	SALES_INVOICE,
)
from millitrix.utils.extended_reports import get_purch_inv_payment_rows
from millitrix.utils.finance_reports import get_party_balance_report_rows
from millitrix.utils.gl_reports import get_voucher_gl_lines
from millitrix.utils.report_filters import normalize_report_dates
from millitrix.utils.stock_reports import get_item_ledger_rows
from millitrix.utils.trading_reports import _date_location_conditions

_BROKER_PCAT = "11"


def _distinct_broker_ids() -> set[str]:
	rows = frappe.db.sql(
		"""
		SELECT DISTINCT brokerid AS partyid FROM `tabPurchase Invoice`
		WHERE docstatus = 1 AND brokerid IS NOT NULL AND brokerid != '' UNION
		SELECT DISTINCT brokerid FROM `tabSales Invoice`
		WHERE docstatus = 1 AND brokerid IS NOT NULL AND brokerid !=''
		""",
		as_dict=True,
	)
	return {row.partyid for row in rows if row.partyid}


def _broker_invoice_conditions(filters: dict, alias: str, date_field: str) -> tuple[list[str], dict]:
	conditions = [f"{alias}.docstatus = 1", f"{alias}.brokerid IS NOT NULL", f"{alias}.brokerid != ''"]
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
	if filters.get("brokerid"):
		conditions.append(f"{alias}.brokerid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	elif filters.get("require_broker_category"):
		conditions.append(
			f"EXISTS (SELECT 1 FROM `tabParty` bp WHERE bp.name = {alias}.brokerid AND bp.pcat_id = %(_broker_pcat)s)"
		)
		params["_broker_pcat"] = _BROKER_PCAT
	return conditions, params


def _party_gl_net(filters: dict, partyid: str, *, before_date: str | None = None) -> tuple[float, float, float]:
	query = dict(filters)
	if before_date:
		query = {**query, "to_date": before_date}
		query.pop("from_date", None)
	query["partyid"] = partyid
	lines = get_voucher_gl_lines(query)
	debit = sum(flt(line.debit) for line in lines)
	credit = sum(flt(line.credit) for line in lines)
	return debit, credit, flt(debit - credit)


def _broker_commission_sum(filters: dict, *, purchase: bool) -> dict[str, float]:
	table = "Purchase Invoice" if purchase else "Sales Invoice"
	alias = "pi" if purchase else "si"
	conditions, params = _broker_invoice_conditions({**filters, "require_broker_category": True}, alias, "invdate")
	amount_field = f"COALESCE({alias}.brokerypayable, {alias}.brokeramnt, 0)"
	rows = frappe.db.sql(
		f"""SELECT {alias}.brokerid, SUM({amount_field}) AS total
		FROM `tab{table}` {alias}
		WHERE {" AND ".join(conditions)}
		GROUP BY {alias}.brokerid
		""",
		params,
		as_dict=True,
	)
	return {row.brokerid: flt(row.total) for row in rows if row.brokerid}


def _broker_payment_sum(filters: dict) -> dict[str, float]:
	conditions = ["p.docstatus = 1"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append("p.pnrdate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("p.pnrdate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append("p.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("brokerid"):
		conditions.append("p.partyid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	else:
		conditions.append("broker.pcat_id = %(_broker_pcat)s")
		params["_broker_pcat"] = _BROKER_PCAT
	rows = frappe.db.sql(
		f"""SELECT p.partyid AS brokerid, SUM(p.amount) AS total
		FROM `tab{BROKER_INVOICE_PAYMENT}` p
		LEFT JOIN `tabParty` broker ON broker.name = p.partyid
		WHERE {" AND ".join(conditions)}
		GROUP BY p.partyid
		""",
		params,
		as_dict=True,
	)
	return {row.brokerid: flt(row.total) for row in rows if row.brokerid}


def _broker_advance_sum(filters: dict) -> dict[str, float]:
	conditions = ["p.docstatus = 1"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append("p.pnrdate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("p.pnrdate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append("p.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("brokerid"):
		conditions.append("p.partyid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	else:
		conditions.append("broker.pcat_id = %(_broker_pcat)s")
		params["_broker_pcat"] = _BROKER_PCAT
	rows = frappe.db.sql(
		f"""SELECT p.partyid AS brokerid, SUM(p.amount) AS total
		FROM `tab{ADVANCE_PAYMENT}` p
		LEFT JOIN `tabParty` broker ON broker.name = p.partyid
		WHERE {" AND ".join(conditions)}
		GROUP BY p.partyid
		""",
		params,
		as_dict=True,
	)
	return {row.brokerid: flt(row.total) for row in rows if row.brokerid}


def _broker_payment_knockoff_rows(filters: dict) -> list[dict]:
	conditions = ["p.docstatus = 1"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append("p.pnrdate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("p.pnrdate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append("p.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("brokerid"):
		conditions.append("p.partyid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	else:
		conditions.append("broker.pcat_id = %(_broker_pcat)s")
		params["_broker_pcat"] = _BROKER_PCAT
	conditions.append("ch.doctypeid IN %(inv_doctypes)s")
	params["inv_doctypes"] = (PURCHASE_INVOICE, SALES_INVOICE)
	return frappe.db.sql(
		f"""SELECT
			'Payment' AS row_type,
			p.pnrno AS doc_no,
			p.pnrdate AS doc_date,
			p.location_id,
			p.partyid AS brokerid,
			broker.party_name AS broker_name,
			p.pnrmode,
			p.referno,
			p.amount AS doc_amount,
			ch.doctypeid,
			ch.documentid AS invoice_no,
			ch.amount AS paid_amount,
			p.narration
		FROM `tabPayment and Receipt Document` ch
		INNER JOIN `tab{BROKER_INVOICE_PAYMENT}` p ON p.name = ch.parent
		LEFT JOIN `tabParty` broker ON broker.name = p.partyid
		WHERE {" AND ".join(conditions)}
		ORDER BY p.pnrdate, p.pnrno, ch.idx
		""",
		params,
		as_dict=True,
	)


def get_broker_invoice_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle BrokerInvPayment.RDF — broker commission invoices + payments."""
	return get_broker_inv_payment_register_rows(filters)


def get_broker_inv_payment_register_rows(filters: dict | None = None) -> list[dict]:
	filters = normalize_report_dates(filters or {})
	pi_conditions, pi_params = _broker_invoice_conditions({**filters, "require_broker_category": True}, "pi", "invdate")
	si_conditions, si_params = _broker_invoice_conditions({**filters, "require_broker_category": True}, "si", "invdate")
	params = {**pi_params, **si_params}
	invoice_rows = frappe.db.sql(
		f"""
		SELECT
			'Invoice' AS row_type,
			'Purchase' AS inv_type,
			pi.purchinvno AS doc_no,
			pi.invdate AS doc_date,
			pi.location_id,
			pi.supplierid AS partyid,
			sup.party_name AS party_name,
			pi.brokerid,
			br.party_name AS broker_name,
			pi.itemcode,
			it.itemname AS item_name,
			COALESCE(pi.brokerypayable, pi.brokeramnt, 0) AS doc_amount,
			pi.brokeramnt,
			pi.brokery,
			pi.brokerypayable,
			pi.brokery_dr_supplier,
			pi.doctypeid,
			pi.purchinvno AS documentid,
			'' AS pnrmode,
			'' AS referno,
			0 AS paid_amount
		FROM `tabPurchase Invoice` pi
		LEFT JOIN `tabParty` sup ON sup.name = pi.supplierid
		LEFT JOIN `tabParty` br ON br.name = pi.brokerid
		LEFT JOIN `tabItem Setup` it ON it.name = pi.itemcode
		WHERE {" AND ".join(pi_conditions)}
		UNION ALL
		SELECT
			'Invoice' AS row_type,
			'Sales' AS inv_type,
			si.salesinvno AS doc_no,
			si.invdate AS doc_date,
			si.location_id,
			si.customerid AS partyid,
			cust.party_name AS party_name,
			si.brokerid,
			br.party_name AS broker_name,
			si.itemcode,
			it.itemname AS item_name,
			COALESCE(si.brokerypayable, si.brokeramnt, 0) AS doc_amount,
			si.brokeramnt,
			si.brokery,
			si.brokerypayable,
			NULL AS brokery_dr_supplier,
			si.doctypeid,
			si.salesinvno AS documentid,
			'' AS pnrmode,
			'' AS referno,
			0 AS paid_amount
		FROM `tabSales Invoice` si
		LEFT JOIN `tabParty` cust ON cust.name = si.customerid
		LEFT JOIN `tabParty` br ON br.name = si.brokerid
		LEFT JOIN `tabItem Setup` it ON it.name = si.itemcode
		WHERE {" AND ".join(si_conditions)}
		""",
		params,
		as_dict=True,
	)
	payment_rows = _broker_payment_knockoff_rows(filters)
	rows = list(invoice_rows) + list(payment_rows)
	return sorted(rows, key=lambda r: (str(r.get("doc_date") or ""), str(r.get("doc_no") or "")))


def get_broker_inv_pay_detl_rows(filters: dict | None = None) -> list[dict]:
	filters = normalize_report_dates(filters or {})
	pi_conditions, pi_params = _broker_invoice_conditions({**filters, "require_broker_category": True}, "pi", "invdate")
	si_conditions, si_params = _broker_invoice_conditions({**filters, "require_broker_category": True}, "si", "invdate")
	params = {**pi_params, **si_params}
	rows = frappe.db.sql(
		f"""
		SELECT
			'Purchase' AS inv_type,
			pi.purchinvno AS invno,
			pi.invdate,
			pi.location_id,
			pi.supplierid AS partyid,
			sup.party_name AS party_name,
			pi.brokerid,
			br.party_name AS broker_name,
			pi.itemcode,
			it.itemname AS item_name,
			pi.brokery,
			pi.borrow,
			pi.brokerypayable,
			d.truckno,
			d.bagqty,
			d.netweight,
			d.brokeramnt,
			d.cartage,
			CASE WHEN pi.brokery = 'P' THEN COALESCE(d.brokeramnt, 0) ELSE 0 END AS less_brokery,
			CASE WHEN pi.borrow = 'D' THEN COALESCE(d.cartage, 0) ELSE 0 END AS less_cartage,
			pi.doctypeid,
			pi.purchinvno AS documentid
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Detail` d ON d.parent = pi.name
		LEFT JOIN `tabParty` sup ON sup.name = pi.supplierid
		LEFT JOIN `tabParty` br ON br.name = pi.brokerid
		LEFT JOIN `tabItem Setup` it ON it.name = pi.itemcode
		WHERE {" AND ".join(pi_conditions)}
		UNION ALL
		SELECT
			'Sales' AS inv_type,
			si.salesinvno AS invno,
			si.invdate,
			si.location_id,
			si.customerid AS partyid,
			cust.party_name AS party_name,
			si.brokerid,
			br.party_name AS broker_name,
			si.itemcode,
			it.itemname AS item_name,
			si.brokery,
			NULL AS borrow,
			si.brokerypayable,
			d.truckno,
			d.bagqty,
			d.netweight,
			d.brokeramnt,
			0 AS cartage,
			CASE WHEN si.brokery = 'P' THEN COALESCE(d.brokeramnt, 0) ELSE 0 END AS less_brokery,
			0 AS less_cartage,
			si.doctypeid,
			si.salesinvno AS documentid
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Detail` d ON d.parent = si.name
		LEFT JOIN `tabParty` cust ON cust.name = si.customerid
		LEFT JOIN `tabParty` br ON br.name = si.brokerid
		LEFT JOIN `tabItem Setup` it ON it.name = si.itemcode
		WHERE {" AND ".join(si_conditions)}
		ORDER BY invdate, invno, truckno
		""",
		params,
		as_dict=True,
	)
	return rows


def get_broker_ledger_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle BrokerLedgerSummary.RDF — broker-wise opening, commission, GL, payments."""
	filters = normalize_report_dates(filters or {})
	broker_ids = _distinct_broker_ids()
	if filters.get("brokerid"):
		broker_ids = {filters["brokerid"]} & broker_ids
	if not broker_ids:
		return []

	opening_end = str(add_days(getdate(filters["from_date"]), -1))
	purchase_map = _broker_commission_sum(filters, purchase=True)
	sales_map = _broker_commission_sum(filters, purchase=False)
	payment_map = _broker_payment_sum(filters)
	advance_map = _broker_advance_sum(filters)

	rows: list[dict] = []
	for brokerid in sorted(broker_ids):
		open_dr, open_cr, opening_net = _party_gl_net(filters, brokerid, before_date=opening_end)
		period_dr, period_cr, period_net = _party_gl_net(filters, brokerid)
		purchase = flt(purchase_map.get(brokerid))
		sales = flt(sales_map.get(brokerid))
		payment = flt(payment_map.get(brokerid))
		advance = flt(advance_map.get(brokerid))
		balance = flt(opening_net + purchase + sales - period_net - advance - payment)
		if not filters.get("show_zero_values") and not any(
			abs(v) > 0.009
			for v in (opening_net, purchase, sales, period_dr, period_cr, advance, payment, balance)
		):
			continue
		rows.append(
			{
				"partyid": brokerid,
				"party_name": frappe.db.get_value("Party", brokerid, "party_name") or brokerid,
				"opening_balance": opening_net,
				"purchase": purchase,
				"sales": sales,
				"advance": advance,
				"debit": period_dr,
				"credit": period_cr,
				"payment": payment,
				"balance": balance,
			}
		)
	return rows


def get_cash_flow_detail_rows(filters: dict | None = None) -> list[dict]:
	from millitrix.utils.extended_reports import get_cash_flow_rows

	filters = normalize_report_dates(filters or {})
	rows = get_cash_flow_rows(filters)
	out: list[dict] = []
	for row in rows:
		out.append(
			{
				**row,
				"net_amount": flt(row.get("debit")) - flt(row.get("credit")),
			}
		)
	return out


def get_cust_ord_inv_detl_rows(filters: dict | None = None) -> list[dict]:
	from millitrix.utils.extended_reports import get_so_inv_detail_rows

	return get_so_inv_detail_rows(filters)


def get_supp_ord_inv_detl_rows(filters: dict | None = None) -> list[dict]:
	from millitrix.utils.extended_reports import get_po_inv_detail_rows

	return get_po_inv_detail_rows(filters)


def get_party_bal_paid_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle Party_Bal_Paid.RDF — parties with payable (credit) balance and period payments."""
	filters = normalize_report_dates(filters or {})
	rows = get_party_balance_report_rows(filters)
	out: list[dict] = []
	for row in rows:
		balance = flt(row.get("balance"))
		if balance >= -0.009:
			continue
		payable = flt(-balance)
		payment_total = flt(row.get("payment_total"))
		out.append(
			{
				**row,
				"payable": payable,
				"payment_balance": flt(payable - payment_total),
			}
		)
	return out


def get_party_bardana_bincard_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PartyBardanaBincard.RDF — party bardana item ledger with opening B/F."""
	from frappe.utils import add_days, getdate

	from millitrix.utils.stock_reports import _stock_name_maps, get_item_ledger_rows

	filters = dict(filters or {})
	if not filters.get("partyid"):
		frappe.throw("Party is required for Party Bardana Bin Card")

	filters = normalize_report_dates(filters)
	partyid = filters["partyid"]
	party_name = frappe.db.get_value("Party", partyid, "party_name") or partyid
	store_filter = filters.get("storeid")
	item_filter = filters.get("itemcode")
	from_date = filters.get("from_date")
	store_names, item_names, _party_names = _stock_name_maps()

	opening_by_key: dict[tuple[str, str], float] = {}
	if from_date:
		opening_end = str(add_days(getdate(from_date), -1))
		open_filters = {**filters, "to_date": opening_end}
		open_filters.pop("from_date", None)
		for row in get_item_ledger_rows(open_filters):
			if row.get("partyid") != partyid:
				continue
			key = (row.get("storeid") or "", row.get("itemcode") or "")
			qty = flt(row.get("qty"))
			if row.get("movement") == "IN":
				opening_by_key[key] = opening_by_key.get(key, 0.0) + qty
			else:
				opening_by_key[key] = opening_by_key.get(key, 0.0) - qty

	balances = dict(opening_by_key)
	out: list[dict] = []

	def _append_opening(storeid: str, itemcode: str, balance: float) -> None:
		if abs(balance) <= 0.0001:
			return
		out.append(
			{
				"tdate": from_date,
				"location_id": filters.get("location_id") or "",
				"storeid": storeid,
				"store_name": store_names.get(storeid) or storeid,
				"itemcode": itemcode,
				"item_name": item_names.get(itemcode) or itemcode,
				"partyid": partyid,
				"party_name": party_name,
				"movement": "",
				"qty": 0.0,
				"balance": flt(balance),
				"source": "",
				"documentid": "",
				"detail": _("Opening Balance"),
			}
		)

	def _include_key(key: tuple[str, str]) -> bool:
		storeid, itemcode = key
		if store_filter and storeid != store_filter:
			return False
		if item_filter and itemcode != item_filter:
			return False
		return True

	for key in sorted(k for k in opening_by_key if _include_key(k)):
		_append_opening(key[0], key[1], opening_by_key[key])

	period_rows = sorted(
		[row for row in get_item_ledger_rows(filters) if row.get("partyid") == partyid],
		key=lambda r: (
			r.get("tdate") or "",
			r.get("itemcode") or "",
			r.get("storeid") or "",
			r.get("documentid") or "",
		),
	)
	seen_keys: set[tuple[str, str]] = {key for key in opening_by_key if _include_key(key)}
	for row in period_rows:
		key = (row.get("storeid") or "", row.get("itemcode") or "")
		if not _include_key(key):
			continue
		if key not in seen_keys:
			seen_keys.add(key)
			_append_opening(key[0], key[1], balances.get(key, 0.0))
		qty = flt(row.get("qty"))
		if row.get("movement") == "IN":
			balances[key] = balances.get(key, 0.0) + qty
		else:
			balances[key] = balances.get(key, 0.0) - qty
		out.append(
			{
				**row,
				"store_name": store_names.get(key[0]) or key[0],
				"item_name": item_names.get(key[1]) or key[1],
				"partyid": partyid,
				"party_name": party_name,
				"balance": flt(balances.get(key, 0.0)),
			}
		)
	return out


def get_stk_rece_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle StkRece_Summary.RDF — stock receipt totals by date/store/item."""
	from millitrix.utils.stock_reports import _stock_name_maps, get_item_ledger_rows

	rows = get_item_ledger_rows(normalize_report_dates(filters or {}))
	store_names, item_names, _party_names = _stock_name_maps()
	agg: dict[tuple, dict] = {}
	for row in rows:
		if row.get("movement") != "IN":
			continue
		key = (row.get("tdate"), row.get("location_id"), row.get("storeid"), row.get("itemcode"))
		bucket = agg.setdefault(
			key,
			{
				"tdate": row.get("tdate"),
				"location_id": row.get("location_id"),
				"storeid": row.get("storeid"),
				"store_name": store_names.get(row.get("storeid")) or row.get("storeid") or "",
				"itemcode": row.get("itemcode"),
				"item_name": item_names.get(row.get("itemcode")) or row.get("itemcode") or "",
				"total_qty": 0.0,
				"movement_count": 0,
			},
		)
		bucket["total_qty"] += flt(row.get("qty"))
		bucket["movement_count"] += 1
	return sorted(agg.values(), key=lambda r: (r["tdate"], r.get("storeid") or "", r.get("itemcode") or ""))


def get_supp_pay_and_inv_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SuppPayAndInv.RDF — PI detail lines with supplier payment knockoff."""
	filters = normalize_report_dates(filters or {})
	conditions, params = _date_location_conditions(filters, "pi", "invdate")
	if filters.get("supplierid"):
		conditions.append("pi.supplierid = %(supplierid)s")
		params["supplierid"] = filters["supplierid"]
	if filters.get("partyid"):
		conditions.append("pi.supplierid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	if filters.get("itemcode"):
		conditions.append("pi.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	invoices = frappe.db.sql(
		f"""SELECT
			pi.purchinvno,
			pi.invdate,
			pi.location_id,
			pi.supplierid,
			supplier.party_name AS supplier_name,
			pi.itemcode,
			item.itemname AS item_name,
			pi.payable AS header_payable,
			pi.amount AS header_amount,
			pi.doctypeid,
			d.storeid,
			store.description AS store_name,
			d.truckno,
			d.netweight,
			d.lessweight,
			d.totalamnt AS line_amount
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Detail` d ON d.parent = pi.name
		LEFT JOIN `tabParty` supplier ON supplier.name = pi.supplierid
		LEFT JOIN `tabItem Setup` item ON item.name = pi.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		WHERE {" AND ".join(conditions)}
		ORDER BY pi.invdate, pi.purchinvno, d.idx
		""",
		params,
		as_dict=True,
	)
	payments = get_purch_inv_payment_rows(filters)
	pay_map: dict[tuple, float] = {}
	for pay in payments:
		if pay.get("doctypeid") not in (PURCHASE_INVOICE, PURCHASE_OTHER_BILL):
			continue
		key = (pay.get("location_id"), pay.get("doctypeid"), str(pay.get("documentid")))
		pay_map[key] = pay_map.get(key, 0.0) + flt(pay.get("amount"))
	out: list[dict] = []
	for inv in invoices:
		key = (inv.location_id, inv.doctypeid, str(inv.purchinvno))
		applied = flt(pay_map.get(key))
		invoice_amount = flt(inv.header_payable or inv.header_amount)
		out.append(
			{
				**inv,
				"invoice_amount": invoice_amount,
				"applied": applied,
				"docbalamnt": flt(invoice_amount - applied),
			}
		)
	return out


def get_supp_inv_and_pay_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle SuppInvAndPay.RDF — SI detail lines with receipt knockoff."""
	from millitrix.utils.doctype_ids import SALES_INVOICE, SALES_OTHER_BILL
	from millitrix.utils.extended_reports import get_sales_inv_receipt_rows

	filters = normalize_report_dates(filters or {})
	conditions, params = _date_location_conditions(filters, "si", "invdate")
	if filters.get("customerid"):
		conditions.append("si.customerid = %(customerid)s")
		params["customerid"] = filters["customerid"]
	if filters.get("partyid"):
		conditions.append("si.customerid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	if filters.get("itemcode"):
		conditions.append("si.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	invoices = frappe.db.sql(
		f"""SELECT
			si.salesinvno,
			si.invdate,
			si.location_id,
			si.customerid,
			customer.party_name AS customer_name,
			si.itemcode,
			item.itemname AS item_name,
			si.receivable AS header_receivable,
			si.amount AS header_amount,
			si.doctypeid,
			d.storeid,
			store.description AS store_name,
			d.truckno,
			d.netweight,
			d.lessweight,
			d.totalamnt AS line_amount
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Detail` d ON d.parent = si.name
		LEFT JOIN `tabParty` customer ON customer.name = si.customerid
		LEFT JOIN `tabItem Setup` item ON item.name = si.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		WHERE {" AND ".join(conditions)}
		ORDER BY si.invdate, si.salesinvno, d.idx
		""",
		params,
		as_dict=True,
	)
	receipts = get_sales_inv_receipt_rows(filters)
	pay_map: dict[tuple, float] = {}
	for rcpt in receipts:
		if rcpt.get("doctypeid") not in (SALES_INVOICE, SALES_OTHER_BILL):
			continue
		key = (rcpt.get("location_id"), rcpt.get("doctypeid"), str(rcpt.get("documentid")))
		pay_map[key] = pay_map.get(key, 0.0) + flt(rcpt.get("amount"))
	out: list[dict] = []
	for inv in invoices:
		key = (inv.location_id, inv.doctypeid, str(inv.salesinvno))
		applied = flt(pay_map.get(key))
		invoice_amount = flt(inv.header_receivable or inv.header_amount)
		out.append(
			{
				**inv,
				"invoice_amount": invoice_amount,
				"applied": applied,
				"docbalamnt": flt(invoice_amount - applied),
			}
		)
	return out


def get_tstk_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle TStk_Summary.RDF — stock transfer lines (VIEW_STOCK_TRANSFER)."""
	filters = normalize_report_dates(filters or {})
	conditions = ["st.docstatus = 1"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append("st.tdate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("st.tdate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append("st.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("itemcode"):
		conditions.append("st.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("storeid"):
		conditions.append("(st.fromstoreid = %(storeid)s OR d.tostoreid = %(storeid)s)")
		params["storeid"] = filters["storeid"]
	return frappe.db.sql(
		f"""SELECT
			st.transferno,
			st.tdate,
			st.location_id,
			st.itemcode,
			item.itemname AS item_name,
			st.fromstoreid,
			from_store.description AS from_store_name,
			d.tostoreid,
			to_store.description AS to_store_name,
			st.partyid,
			party.party_name,
			d.bagqty,
			d.bagweight,
			(COALESCE(d.bagqty, 0) * COALESCE(d.bagweight, 0)) AS total_wgt,
			d.delikanta,
			d.netweight,
			d.transporter
		FROM `tabStock Transfer Note` st
		INNER JOIN `tabStock Transfer Detail` d ON d.parent = st.name
		LEFT JOIN `tabItem Setup` item ON item.name = st.itemcode
		LEFT JOIN `tabStore Setup` from_store ON from_store.name = st.fromstoreid
		LEFT JOIN `tabStore Setup` to_store ON to_store.name = d.tostoreid
		LEFT JOIN `tabParty` party ON party.name = st.partyid
		WHERE {" AND ".join(conditions)}
		ORDER BY st.tdate, st.transferno, d.idx
		""",
		params,
		as_dict=True,
	)
