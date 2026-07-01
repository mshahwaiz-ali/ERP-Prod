# Copyright (c) 2026, Millitrix and contributors
# Blueprint VIEW_KNOCKOFFDOCS — outstanding invoice balances for knockoff

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.doctype_ids import (
	PURCHASE_INVOICE,
	PURCHASE_OTHER_BILL,
	SALES_INVOICE,
	SALES_OTHER_BILL,
)

_PAYMENT_DOCTYPES = (PURCHASE_INVOICE, PURCHASE_OTHER_BILL)
_RECEIPT_DOCTYPES = (SALES_INVOICE, SALES_OTHER_BILL)

_PNR_PARENTS: tuple[str, ...] = (
	"Payment and Receipt Voucher",
	"Purchase Invoice Payment",
	"Sales Invoice Receipt",
	"Broker Invoice Payment",
	"Payable Discount Note",
	"Receivable Discount Note",
)

_ADJUSTMENT_PARENTS: tuple[str, ...] = (
	"Advance Adjustment",
	"Paid Advance Adjustment",
	"Received Advance Adjustment",
)

_KNOCKOFF_SOURCES: tuple[tuple[str, str, str], ...] = tuple(
	("Payment and Receipt Document", parent, "pnrdate") for parent in _PNR_PARENTS
) + tuple(
	("Adjustment Invoice", parent, "adjdate") for parent in _ADJUSTMENT_PARENTS
) + (
	("Hawala Invoice", "Payment By Hawala", "gmdate"),
	("Party Gross Margin Invoice", "Party Gross Margin", "pgdate"),
)

_CNB_PARTY_PARENTS: tuple[str, ...] = (
	"Cash and Bank Voucher",
	"Party Payment Voucher",
	"Party Receipt Voucher",
	"Employee Payment Voucher",
	"Employee Receipt Voucher",
)

_CNB_PARENTS: tuple[tuple[str, str], ...] = (
	("Payment Voucher", "vouchdate"),
	("Receipt Voucher", "vouchdate"),
	("Expense Voucher", "vouchdate"),
) + tuple((parent, "vouchdate") for parent in _CNB_PARTY_PARENTS)


def _doc_key(location_id: str, doctypeid: str, documentid) -> tuple[str, str, str]:
	return (location_id, doctypeid, str(documentid).strip())


def _knockoff_union_sql(*, as_of_date: str | None = None) -> tuple[str, dict]:
	parts: list[str] = []
	params: dict = {}
	if as_of_date:
		params["as_of_date"] = as_of_date

	for child, parent, date_field in _KNOCKOFF_SOURCES:
		conditions = ["p.docstatus = 1"]
		if as_of_date:
			conditions.append(f"p.{date_field} <= %(as_of_date)s")
		parts.append(
			f"""
			SELECT p.location_id, ch.doctypeid, ch.documentid, SUM(COALESCE(ch.amount, 0)) AS applied
			FROM `tab{child}` ch
			INNER JOIN `tab{parent}` p ON p.name = ch.parent
			WHERE {" AND ".join(conditions)}
			GROUP BY p.location_id, ch.doctypeid, ch.documentid
			"""
		)

	for parent, date_field in _CNB_PARENTS:
		conditions = ["p.docstatus = 1"]
		if as_of_date:
			conditions.append(f"p.{date_field} <= %(as_of_date)s")
		parts.append(
			f"""SELECT p.location_id, ch.doctypeid, ch.documentid, SUM(COALESCE(ch.amount, 0)) AS applied
			FROM `tabCash and Bank Voucher Document` ch
			INNER JOIN `tab{parent}` p ON p.name = ch.parent
			WHERE {" AND ".join(conditions)}
			GROUP BY p.location_id, ch.doctypeid, ch.documentid
			"""
		)

	union = " UNION ALL ".join(parts)
	query = f"""
		SELECT location_id, doctypeid, documentid, SUM(applied) AS applied
		FROM ({union}) knockoffs
		GROUP BY location_id, doctypeid, documentid
	"""
	return query, params


def get_knockoff_totals(*, as_of_date: str | None = None, doctypeids: tuple[str, ...] | None = None) -> dict[tuple[str, str, str], float]:
	"""Return applied knockoff amount keyed by (location_id, doctypeid, documentid)."""
	query, params = _knockoff_union_sql(as_of_date=as_of_date)
	if doctypeids:
		query = f"""
			SELECT location_id, doctypeid, documentid, applied
			FROM ({query}) totals
			WHERE doctypeid IN %(doctypeids)s
		"""
		params["doctypeids"] = doctypeids

	rows = frappe.db.sql(query, params, as_dict=True)
	out: dict[tuple[str, str, str], float] = {}
	for row in rows:
		if not row.doctypeid or row.documentid in (None, ""):
			continue
		key = _doc_key(row.location_id, row.doctypeid, row.documentid)
		out[key] = flt(row.applied)
	return out


def _enrich_knockoff_row(row: dict) -> dict:
	"""Add display names for Oracle-style knockoff grids."""
	party_name = ""
	if row.get("partyid"):
		party_name = (
			frappe.db.get_value("Party", {"partyid": row["partyid"]}, "party_name") or row["partyid"]
		)
	item_name = ""
	if row.get("itemcode"):
		item_name = frappe.db.get_value("Item Setup", row["itemcode"], "itemname") or row["itemcode"]
	row["party_name"] = party_name
	row["item_name"] = item_name
	return row


def get_document_outstanding(
	location_id: str,
	doctypeid: str,
	documentid,
	invoice_amount: float,
	*,
	as_of_date: str | None = None,
	knockoff_totals: dict[tuple[str, str, str], float] | None = None,
) -> float:
	"""Outstanding balance for one invoice document."""
	if knockoff_totals is None:
		knockoff_totals = get_knockoff_totals(as_of_date=as_of_date, doctypeids=(doctypeid,))
	key = _doc_key(location_id, doctypeid, documentid)
	applied = flt(knockoff_totals.get(key))
	return max(flt(invoice_amount) - applied, 0)


def get_outstanding_documents(
	partyid: str,
	location_id: str,
	flow: str,
	*,
	as_of_date: str | None = None,
) -> list[dict]:
	"""Outstanding invoices for PNR/CNB knockoff picker (VIEW_KNOCKOFFDOCS)."""
	flow = (flow or "").lower()
	if flow in ("p", "payment", "pay"):
		doctypeids = _PAYMENT_DOCTYPES
		rows = _fetch_payment_invoices(partyid, location_id, as_of_date=as_of_date)
	elif flow in ("r", "receipt", "recv"):
		doctypeids = _RECEIPT_DOCTYPES
		rows = _fetch_receipt_invoices(partyid, location_id, as_of_date=as_of_date)
	else:
		frappe.throw("flow must be payment or receipt")

	from millitrix.utils.party_gl import get_party_accid

	party_accid = get_party_accid(partyid)
	knockoff_totals = get_knockoff_totals(as_of_date=as_of_date, doctypeids=doctypeids)
	out: list[dict] = []
	for row in rows:
		docbal = get_document_outstanding(
			row["location_id"],
			row["doctypeid"],
			row["documentid"],
			row["invoice_amount"],
			knockoff_totals=knockoff_totals,
		)
		if docbal <= 0.009:
			continue
		out.append(
			_enrich_knockoff_row(
				{
					"doctypeid": row["doctypeid"],
					"documentid": str(row["documentid"]),
					"docbalamnt": round(flt(docbal), 2),
					"amount": round(flt(docbal), 2),
					"balance": 0,
					"invdate": row["invdate"],
					"partyid": row["partyid"],
					"itemcode": row.get("itemcode"),
					"location_id": row["location_id"],
					"accid": party_accid,
					"invoice_amount": round(flt(row["invoice_amount"]), 2),
					"applied": round(flt(row["invoice_amount"] - docbal), 2),
				}
			)
		)
	return out


def get_outstanding_broker_documents(
	brokerid: str,
	location_id: str,
	*,
	as_of_date: str | None = None,
) -> list[dict]:
	"""Outstanding broker commission (brokerypayable) for Broker Invoice Payment."""
	from millitrix.utils.party_gl import get_party_accid

	filters: dict = {"brokerid": brokerid, "location_id": location_id}
	if as_of_date:
		filters["to_date"] = as_of_date

	pi_conditions, pi_params = _broker_invoice_conditions(filters, "pi", "invdate")
	si_conditions, si_params = _broker_invoice_conditions(filters, "si", "invdate")
	params = {**pi_params, **si_params}

	rows = frappe.db.sql(
		f"""
		SELECT
			pi.purchinvno AS documentid,
			pi.doctypeid,
			pi.invdate,
			pi.location_id,
			pi.supplierid AS partyid,
			pi.itemcode,
			COALESCE(pi.brokerypayable, pi.brokeramnt, 0) AS invoice_amount
		FROM `tabPurchase Invoice` pi
		WHERE {" AND ".join(pi_conditions)}
		UNION ALL
		SELECT
			si.salesinvno AS documentid,
			si.doctypeid,
			si.invdate,
			si.location_id,
			si.customerid AS partyid,
			si.itemcode,
			COALESCE(si.brokerypayable, si.brokeramnt, 0) AS invoice_amount
		FROM `tabSales Invoice` si
		WHERE {" AND ".join(si_conditions)}
		""",
		params,
		as_dict=True,
	)

	doctypeids = (PURCHASE_INVOICE, SALES_INVOICE)
	knockoff_totals = get_knockoff_totals(as_of_date=as_of_date, doctypeids=doctypeids)
	party_accid = get_party_accid(brokerid)
	out: list[dict] = []
	for row in rows:
		docbal = get_document_outstanding(
			row["location_id"],
			row["doctypeid"],
			row["documentid"],
			row["invoice_amount"],
			knockoff_totals=knockoff_totals,
		)
		if docbal <= 0.009:
			continue
		out.append(
			_enrich_knockoff_row(
				{
					"doctypeid": row["doctypeid"],
					"documentid": str(row["documentid"]),
					"docbalamnt": round(flt(docbal), 2),
					"amount": round(flt(docbal), 2),
					"balance": 0,
					"invdate": row["invdate"],
					"partyid": row["partyid"],
					"itemcode": row.get("itemcode"),
					"location_id": row["location_id"],
					"accid": party_accid,
					"invoice_amount": round(flt(row["invoice_amount"]), 2),
					"applied": round(flt(row["invoice_amount"] - docbal), 2),
				}
			)
		)
	return out


def get_pi_outstanding_rows(filters: dict | None = None) -> list[dict]:
	return _outstanding_report_rows(filters, flow="payment")


def get_si_outstanding_rows(filters: dict | None = None) -> list[dict]:
	return _outstanding_report_rows(filters, flow="receipt")


def _outstanding_report_rows(filters: dict | None, *, flow: str) -> list[dict]:
	filters = filters or {}
	as_of_date = filters.get("as_of_date") or filters.get("to_date")
	show_zero = int(filters.get("show_zero") or 0)

	if flow == "payment":
		doctypeids = _PAYMENT_DOCTYPES
		invoices = _fetch_all_payment_invoices(filters)
	else:
		doctypeids = _RECEIPT_DOCTYPES
		invoices = _fetch_all_receipt_invoices(filters)

	knockoff_totals = get_knockoff_totals(as_of_date=as_of_date, doctypeids=doctypeids)
	rows: list[dict] = []
	for inv in invoices:
		docbal = get_document_outstanding(
			inv["location_id"],
			inv["doctypeid"],
			inv["documentid"],
			inv["invoice_amount"],
			knockoff_totals=knockoff_totals,
		)
		if docbal <= 0.009 and not show_zero:
			continue
		applied = flt(inv["invoice_amount"]) - docbal
		party_name = inv.get("party_name") or (
			frappe.db.get_value("Party", inv.get("partyid"), "party_name") if inv.get("partyid") else ""
		)
		item_name = inv.get("item_name") or (
			frappe.db.get_value("Item Setup", inv.get("itemcode"), "itemname") if inv.get("itemcode") else ""
		)
		rows.append(
			{
				**inv,
				"documentid": str(inv["documentid"]),
				"party_name": party_name or inv.get("partyid") or "",
				"item_name": item_name or inv.get("itemcode") or "",
				"invoice_amount": round(flt(inv["invoice_amount"]), 2),
				"applied": round(flt(applied), 2),
				"docbalamnt": round(flt(docbal), 2),
			}
		)
	return rows


def _fetch_payment_invoices(partyid: str, location_id: str, *, as_of_date: str | None = None) -> list[dict]:
	filters: dict = {"partyid": partyid, "location_id": location_id}
	if as_of_date:
		filters["to_date"] = as_of_date
	return _fetch_all_payment_invoices(filters)


def _fetch_receipt_invoices(partyid: str, location_id: str, *, as_of_date: str | None = None) -> list[dict]:
	filters: dict = {"partyid": partyid, "location_id": location_id}
	if as_of_date:
		filters["to_date"] = as_of_date
	return _fetch_all_receipt_invoices(filters)


def _fetch_all_payment_invoices(filters: dict) -> list[dict]:
	rows: list[dict] = []
	rows.extend(_sql_purchase_invoices(filters))
	rows.extend(_sql_purchase_other_bills(filters))
	return sorted(rows, key=lambda r: (r.get("invdate") or "", str(r.get("documentid") or "")))


def _fetch_all_receipt_invoices(filters: dict) -> list[dict]:
	rows: list[dict] = []
	rows.extend(_sql_sales_invoices(filters))
	rows.extend(_sql_sales_other_bills(filters))
	return sorted(rows, key=lambda r: (r.get("invdate") or "", str(r.get("documentid") or "")))


def _invoice_conditions(filters: dict, alias: str, date_field: str, party_field: str) -> tuple[list[str], dict]:
	conditions = [f"{alias}.docstatus = 1"]
	params: dict = {}
	if filters.get("location_id"):
		conditions.append(f"{alias}.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("partyid"):
		conditions.append(f"{alias}.{party_field} = %(partyid)s")
		params["partyid"] = filters["partyid"]
	if filters.get("itemcode"):
		conditions.append(f"{alias}.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("from_date"):
		conditions.append(f"{alias}.{date_field} >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append(f"{alias}.{date_field} <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	return conditions, params


def _broker_invoice_conditions(filters: dict, alias: str, date_field: str) -> tuple[list[str], dict]:
	conditions = [
		f"{alias}.docstatus = 1",
		f"{alias}.brokerid IS NOT NULL",
		f"{alias}.brokerid != ''",
	]
	params: dict = {}
	if filters.get("location_id"):
		conditions.append(f"{alias}.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("brokerid"):
		conditions.append(f"{alias}.brokerid = %(brokerid)s")
		params["brokerid"] = filters["brokerid"]
	if filters.get("to_date"):
		conditions.append(f"{alias}.{date_field} <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	return conditions, params


def _sql_purchase_invoices(filters: dict) -> list[dict]:
	conditions, params = _invoice_conditions(filters, "pi", "invdate", "supplierid")
	rows = frappe.db.sql(
		f"""SELECT
			pi.purchinvno AS documentid,
			pi.doctypeid,
			pi.invdate,
			pi.location_id,
			pi.supplierid AS partyid,
			party.party_name,
			pi.itemcode,
			item.itemname AS item_name,
			COALESCE(pi.payable, pi.amount, 0) AS invoice_amount,
			pi.remarks
		FROM `tabPurchase Invoice` pi
		LEFT JOIN `tabParty` party ON party.name = pi.supplierid
		LEFT JOIN `tabItem Setup` item ON item.name = pi.itemcode
		WHERE {" AND ".join(conditions)}
		""",
		params,
		as_dict=True,
	)
	return rows


def _sql_purchase_other_bills(filters: dict) -> list[dict]:
	conditions, params = _invoice_conditions(filters, "pb", "billdate", "partyid")
	rows = frappe.db.sql(
		f"""SELECT
			pb.pbillno AS documentid,
			pb.doctypeid,
			pb.billdate AS invdate,
			pb.location_id,
			pb.partyid,
			NULL AS itemcode,
			COALESCE(pb.amount, 0) AS invoice_amount,
			pb.remarks
		FROM `tabPurchase Other Bill` pb
		WHERE {" AND ".join(conditions)}
		""",
		params,
		as_dict=True,
	)
	return rows


def _sql_sales_invoices(filters: dict) -> list[dict]:
	conditions, params = _invoice_conditions(filters, "si", "invdate", "customerid")
	rows = frappe.db.sql(
		f"""SELECT
			si.salesinvno AS documentid,
			si.doctypeid,
			si.invdate,
			si.location_id,
			si.customerid AS partyid,
			party.party_name,
			si.itemcode,
			item.itemname AS item_name,
			COALESCE(si.receivable, si.amount, 0) AS invoice_amount,
			si.remarks
		FROM `tabSales Invoice` si
		LEFT JOIN `tabParty` party ON party.name = si.customerid
		LEFT JOIN `tabItem Setup` item ON item.name = si.itemcode
		WHERE {" AND ".join(conditions)}
		""",
		params,
		as_dict=True,
	)
	return rows


def _sql_sales_other_bills(filters: dict) -> list[dict]:
	conditions, params = _invoice_conditions(filters, "sb", "billdate", "partyid")
	rows = frappe.db.sql(
		f"""SELECT
			sb.sbillno AS documentid,
			sb.doctypeid,
			sb.billdate AS invdate,
			sb.location_id,
			sb.partyid,
			NULL AS itemcode,
			COALESCE(sb.amount, 0) AS invoice_amount,
			sb.remarks
		FROM `tabSales Other Bill` sb
		WHERE {" AND ".join(conditions)}
		""",
		params,
		as_dict=True,
	)
	return rows
