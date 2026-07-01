# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doctype_ids import (
	ADVANCE_PAYMENT,
	ADVANCE_PNR,
	ADVANCE_RECEIPT,
	BROKER_INVOICE_PAYMENT,
	PAID_ADVANCE_ADJUSTMENT,
	PARTY_PAYMENT_VOUCHER,
	PARTY_RECEIPT_VOUCHER,
	PAYABLE_DISCOUNT_NOTE,
	PAYMENT_VOUCHER,
	PURCHASE_INVOICE,
	PURCHASE_INVOICE_PAYMENT,
	PURCHASE_OTHER_BILL,
	RECEIPT_VOUCHER,
	RECEIVABLE_DISCOUNT_NOTE,
	RECEIVED_ADVANCE_ADJUSTMENT,
	SALES_INVOICE,
	SALES_INVOICE_RECEIPT,
	SALES_OTHER_BILL,
)
from millitrix.utils.gl_reports import (
	aggregate_account_balances,
	format_balance_side,
	get_trial_balance_rows,
	get_voucher_gl_lines,
)
from millitrix.utils.report_filters import normalize_report_dates

_PNR_PAYMENT_DOCTYPES = (PURCHASE_INVOICE, PURCHASE_OTHER_BILL)
_PNR_RECEIPT_DOCTYPES = (SALES_INVOICE, SALES_OTHER_BILL)
_LEGACY_PNR = "Payment and Receipt Voucher"
_LEGACY_CNB = "Cash and Bank Voucher"
_LEGACY_ADJ = "Advance Adjustment"
_ADVANCE_PCAT = {"payment": "12", "receipt": "13"}
_BANK_FINANCE_NATURES = (
	"Cash Finance Account",
	"Running Finance Account",
	"FM Finance Account",
)


def _register_date_filters(filters: dict, date_field: str, *, prefix: str = "doc") -> tuple[list[str], dict]:
	conditions = [f"{prefix}.docstatus = 1"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append(f"{prefix}.{date_field} >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append(f"{prefix}.{date_field} <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append(f"{prefix}.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("partyid"):
		conditions.append(f"{prefix}.partyid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	return conditions, params


def _query_pnr_register(parent_table: str, filters: dict) -> list[dict]:
	conditions, params = _register_date_filters(filters, "pnrdate", prefix="doc")
	return frappe.db.sql(
		f"""SELECT doc.pnrno, doc.pnrdate, doc.location_id, doc.partyid, doc.amount, doc.posted, doc.narration
		FROM `tab{parent_table}` doc
		WHERE {" AND ".join(conditions)}
		ORDER BY doc.pnrdate, doc.pnrno
		""",
		params,
		as_dict=True,
	)


def _query_advance_pnr_register(parent_table: str, filters: dict, *, pcat_id: str | None = None) -> list[dict]:
	conditions, params = _register_date_filters(filters, "pnrdate", prefix="doc")
	join_party = "LEFT JOIN `tabParty` party ON party.name = doc.partyid"
	if pcat_id:
		conditions.append("party.pcat_id = %(pcat_id)s")
		params["pcat_id"] = pcat_id
	return frappe.db.sql(
		f"""SELECT doc.pnrno, doc.pnrdate, doc.referdate, doc.referno, doc.pnrmode,
			doc.location_id, doc.partyid, party.party_name AS party_name,
			doc.amount, doc.posted, doc.narration
		FROM `tab{parent_table}` doc
		{join_party}
		WHERE {" AND ".join(conditions)}
		ORDER BY doc.pnrdate, doc.pnrno
		""",
		params,
		as_dict=True,
	)


def _query_cnb_register(parent_table: str, filters: dict) -> list[dict]:
	conditions, params = _register_date_filters(filters, "vouchdate", prefix="doc")
	return frappe.db.sql(
		f"""SELECT doc.cnbvno, doc.vouchdate, doc.location_id, doc.vouchmode, doc.amount, doc.posted, doc.narration
		FROM `tab{parent_table}` doc
		WHERE {" AND ".join(conditions)}
		ORDER BY doc.vouchdate, doc.cnbvno
		""",
		params,
		as_dict=True,
	)


def _query_adj_register(parent_table: str, filters: dict) -> list[dict]:
	conditions, params = _register_date_filters(filters, "adjdate", prefix="doc")
	return frappe.db.sql(
		f"""SELECT doc.adjid, doc.adjdate, doc.location_id, doc.partyid, doc.amount, doc.narration, doc.posted
		FROM `tab{parent_table}` doc
		WHERE {" AND ".join(conditions)}
		ORDER BY doc.adjdate, doc.adjid
		""",
		params,
		as_dict=True,
	)


def _legacy_pnr_register(filters: dict, *, flow: str | None = None, pnr_type: str | None = None) -> list[dict]:
	conditions, params = _register_date_filters(filters, "pnrdate", prefix="pnr")
	if pnr_type:
		conditions.append("pnr.pnr_type = %(pnr_type)s")
		params["pnr_type"] = pnr_type
	if flow == "payment":
		conditions.append(
			"""EXISTS (
				SELECT 1 FROM `tabPayment and Receipt Document` pd
				WHERE pd.parent = pnr.name AND pd.doctypeid IN %(pnr_payment_doctypes)s
			)"""
		)
		params["pnr_payment_doctypes"] = _PNR_PAYMENT_DOCTYPES
	elif flow == "receipt":
		conditions.append(
			"""EXISTS (
				SELECT 1 FROM `tabPayment and Receipt Document` pd
				WHERE pd.parent = pnr.name AND pd.doctypeid IN %(pnr_receipt_doctypes)s
			)"""
		)
		params["pnr_receipt_doctypes"] = _PNR_RECEIPT_DOCTYPES
	return frappe.db.sql(
		f"""SELECT pnr.pnrno, pnr.pnrdate, pnr.location_id, pnr.partyid, pnr.amount, pnr.posted, pnr.narration
		FROM `tab{_LEGACY_PNR}` pnr
		WHERE {" AND ".join(conditions)}
		ORDER BY pnr.pnrdate, pnr.pnrno
		""",
		params,
		as_dict=True,
	)


def _legacy_cnb_register(filters: dict, *, receipt: bool | None, party_only: bool = False) -> list[dict]:
	conditions, params = _register_date_filters(filters, "vouchdate", prefix="cnb")
	if receipt is True:
		conditions.append("UPPER(cnb.vouchmode) IN ('R', 'RECEIPT')")
	elif receipt is False:
		conditions.append("UPPER(cnb.vouchmode) IN ('P', 'PAYMENT')")
	if party_only:
		conditions.append(
			"""EXISTS (
				SELECT 1 FROM `tabCash and Bank Voucher Document` cd
				WHERE cd.parent = cnb.name AND cd.partyid IS NOT NULL AND cd.partyid != ''
			)"""
		)
	party_select = ""
	if party_only:
		party_select = """,
			(SELECT cd.partyid FROM `tabCash and Bank Voucher Document` cd
			 WHERE cd.parent = cnb.name AND cd.partyid IS NOT NULL AND cd.partyid != ''
			 ORDER BY cd.idx LIMIT 1) AS partyid"""
	if filters.get("partyid"):
		conditions.append(
			"""EXISTS (
				SELECT 1 FROM `tabCash and Bank Voucher Document` cd
				WHERE cd.parent = cnb.name AND cd.partyid = %(partyid)s
			)"""
		)
		params["partyid"] = filters["partyid"]
	return frappe.db.sql(
		f"""SELECT cnb.cnbvno, cnb.vouchdate, cnb.location_id, cnb.vouchmode, cnb.amount, cnb.posted, cnb.narration{party_select}
		FROM `tab{_LEGACY_CNB}` cnb
		WHERE {" AND ".join(conditions)}
		ORDER BY cnb.vouchdate, cnb.cnbvno
		""",
		params,
		as_dict=True,
	)


def _legacy_adj_register(filters: dict, *, doctypeid: str) -> list[dict]:
	conditions, params = _register_date_filters(filters, "adjdate", prefix="aa")
	conditions.append("aa.doctypeid = %(doctypeid)s")
	params["doctypeid"] = doctypeid
	return frappe.db.sql(
		f"""SELECT aa.adjid, aa.adjdate, aa.location_id, aa.partyid, aa.amount, aa.narration, aa.posted
		FROM `tab{_LEGACY_ADJ}` aa
		WHERE {" AND ".join(conditions)}
		ORDER BY aa.adjdate, aa.adjid
		""",
		params,
		as_dict=True,
	)


def _merge_sorted(rows: list[dict], *keys: str) -> list[dict]:
	return sorted(rows, key=lambda r: tuple(str(r.get(k) or "") for k in keys))


def get_cash_book_rows(filters: dict | None = None, *, include_opening_bf: bool = True) -> list[dict]:
	"""Oracle CashBook.RDF — cash GL lines; optional opening B/F + running balance."""
	from millitrix.utils.gl_reports import get_account_ledger_with_balance_rows
	from millitrix.utils.mill_setting import get_setting_account

	filters = normalize_report_dates(filters or {})
	cash_acc = get_setting_account("Cash")
	filters["accid"] = cash_acc
	if include_opening_bf:
		return get_account_ledger_with_balance_rows(filters)
	return get_voucher_gl_lines(filters)


def get_bank_account_accids(*, exclude_cash: bool = True) -> list[str]:
	from millitrix.utils.mill_setting import get_setting_account

	cash_acc = get_setting_account("Cash") if exclude_cash else None
	rows = frappe.db.sql(
		"""
		SELECT DISTINCT accid
		FROM `tabBank Account`
		WHERE accid IS NOT NULL AND accid != ''
		""",
		as_dict=True,
	)
	accids = [row.accid for row in rows if row.accid and row.accid != cash_acc]
	return accids


def resolve_bank_accid(bankaccid=None, accid: str | None = None) -> str | None:
	if accid:
		return accid
	if bankaccid in (None, ""):
		return None
	raw = str(bankaccid)
	if frappe.db.exists("Bank Account", raw):
		return frappe.db.get_value("Bank Account", raw, "accid")
	if raw.isdigit():
		return frappe.db.get_value("Bank Account", {"bankaccid": int(raw)}, "accid")
	return None


def get_bank_book_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle BankBook.RDF — all bank GL lines with opening B/F and running balance."""
	from frappe.utils import add_days, getdate

	from millitrix.utils.gl_reports import split_balance

	filters = normalize_report_dates(filters or {})
	target_accid = resolve_bank_accid(filters.get("bankaccid"), filters.get("accid"))
	if target_accid:
		bank_accounts = {target_accid}
	else:
		bank_accounts = set(get_bank_account_accids())
	if not bank_accounts:
		return []

	from_date = filters["from_date"]
	opening_end = str(add_days(getdate(from_date), -1))
	opening_totals = aggregate_account_balances(filters, before_date=opening_end)
	open_dr = sum(flt(opening_totals.get(acc, {}).get("debit")) for acc in bank_accounts)
	open_cr = sum(flt(opening_totals.get(acc, {}).get("credit")) for acc in bank_accounts)
	opening_net = open_dr - open_cr

	lines = [line for line in get_voucher_gl_lines(filters) if line.get("accid") in bank_accounts]
	rows: list[dict] = []
	balance = opening_net
	if opening_net:
		open_debit, opening_credit = split_balance(opening_net)
		rows.append(
			{
				"vouchdate": from_date,
				"voucherno": "",
				"doctypeid": "",
				"documentid": "",
				"accid": "",
				"account_name": "",
				"partyid": "",
				"debit": open_debit,
				"credit": opening_credit,
				"detail": _("Balance B/F"),
				"narration": "",
				"balance": flt(opening_net),
			}
		)
	for line in lines:
		balance += flt(line.debit) - flt(line.credit)
		rows.append({**line, "balance": flt(balance)})
	return rows


def get_bank_ledger_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle BankLedger.RDF — single bank account ledger with opening B/F + running balance."""
	from millitrix.utils.gl_reports import get_account_ledger_with_balance_rows

	filters = normalize_report_dates(filters or {})
	accid = resolve_bank_accid(filters.get("bankaccid"), filters.get("accid"))
	if not accid:
		frappe.throw(_("Bank account is required"))
	filters["accid"] = accid
	return get_account_ledger_with_balance_rows(filters)


def get_pnr_register_rows(filters: dict | None = None, *, flow: str | None = None) -> list[dict]:
	"""Invoice knockoff PNR register (legacy helper — prefer split DocType reports)."""
	filters = normalize_report_dates(filters or {})
	return _legacy_pnr_register(filters, flow=flow)


def _query_party_cnb_register(parent_table: str, filters: dict) -> list[dict]:
	conditions, params = _register_date_filters(filters, "vouchdate", prefix="doc")
	if filters.get("partyid"):
		conditions.append("doc.partyid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	if filters.get("pcat_id"):
		conditions.append("party.pcat_id = %(pcat_id)s")
		params["pcat_id"] = filters["pcat_id"]
	return frappe.db.sql(
		f"""SELECT doc.cnbvno, doc.vouchdate, doc.location_id, doc.partyid,
			party.party_name, doc.paymode AS vouchmode, doc.amount, doc.posted, doc.narration,
			doc.referno, doc.referdate, doc.bankaccid
		FROM `tab{parent_table}` doc
		LEFT JOIN `tabParty` party ON party.name = doc.partyid
		WHERE {" AND ".join(conditions)}
		ORDER BY doc.vouchdate, doc.cnbvno
		""",
		params,
		as_dict=True,
	)


def get_party_voucher_register_rows(filters: dict | None = None, *, receipt: bool = False) -> list[dict]:
	"""Oracle PartyPRegister / PartyRRegister — Party Payment/Receipt Voucher."""
	filters = normalize_report_dates(filters or {})
	table = PARTY_RECEIPT_VOUCHER if receipt else PARTY_PAYMENT_VOUCHER
	rows = _query_party_cnb_register(table, filters)
	for row in _legacy_cnb_register(filters, receipt=receipt, party_only=True):
		partyid = row.get("partyid")
		if partyid:
			row.setdefault("party_name", frappe.db.get_value("Party", partyid, "party_name"))
		rows.append(row)
	return _merge_sorted(rows, "vouchdate", "cnbvno")


def get_advance_pnr_register_rows(filters: dict | None = None, *, flow: str) -> list[dict]:
	"""PNR advance mode (Oracle AdvanceP/RRegister) — no invoice knockoff."""
	from millitrix.utils.knockoff_flow import resolve_knockoff_flow

	filters = normalize_report_dates(filters or {})
	flow_label = "Payment" if flow == "payment" else "Receipt"
	pcat_id = _ADVANCE_PCAT.get(flow)
	conditions, params = _register_date_filters(filters, "pnrdate", prefix="doc")
	conditions.append("doc.docstatus = 1")
	conditions.append("doc.advance_flow = %(advance_flow)s")
	params["advance_flow"] = flow_label
	if pcat_id and not filters.get("partyid"):
		conditions.append("party.pcat_id = %(pcat_id)s")
		params["pcat_id"] = pcat_id
	rows = frappe.db.sql(
		f"""SELECT doc.pnrno, doc.pnrdate, doc.referdate, doc.referno, doc.pnrmode,
			doc.location_id, doc.partyid, party.party_name AS party_name,
			doc.amount, doc.posted, doc.narration
		FROM `tab{ADVANCE_PNR}` doc
		LEFT JOIN `tabParty` party ON party.name = doc.partyid
		WHERE {" AND ".join(conditions)}
		ORDER BY doc.pnrdate, doc.pnrno
		""",
		params,
		as_dict=True,
	)
	legacy_table = ADVANCE_PAYMENT if flow == "payment" else ADVANCE_RECEIPT
	rows.extend(_query_advance_pnr_register(legacy_table, filters, pcat_id=pcat_id if not filters.get("partyid") else None))
	for row in _legacy_pnr_register(filters, pnr_type="Advance"):
		try:
			if resolve_knockoff_flow(row.partyid) != flow:
				continue
			if pcat_id and not filters.get("partyid"):
				party_pcat = frappe.db.get_value("Party", row.partyid, "pcat_id")
				if str(party_pcat) != pcat_id:
					continue
			row.setdefault("party_name", frappe.db.get_value("Party", row.partyid, "party_name"))
			rows.append(row)
		except Exception:
			frappe.log_error(
				title=f"Advance register flow skip ({row.get('partyid')})",
				message=frappe.get_traceback(),
			)
			continue
	return _merge_sorted(rows, "pnrdate", "pnrno")


def get_discount_pnr_register_rows(filters: dict | None = None, *, flow: str) -> list[dict]:
	"""PNR discount notes with invoice knockoff lines (Oracle PayableDRegister / ReceivableDRegister)."""
	from millitrix.utils.knockoff_flow import resolve_knockoff_flow

	filters = normalize_report_dates(filters or {})
	table = RECEIVABLE_DISCOUNT_NOTE if flow == "receipt" else PAYABLE_DISCOUNT_NOTE
	rows = _query_discount_pnr_register_detail(table, filters)
	for row in _legacy_pnr_register(filters, pnr_type="Discount"):
		try:
			if resolve_knockoff_flow(row.partyid) != flow:
				continue
			if filters.get("partyid") and row.partyid != filters["partyid"]:
				continue
			parent_name = frappe.db.get_value(_LEGACY_PNR, {"pnrno": row.pnrno}, "name")
			if not parent_name:
				continue
			row.setdefault("party_name", frappe.db.get_value("Party", row.partyid, "party_name"))
			rows.extend(_expand_pnr_discount_parent({**row, "name": parent_name, "pnrno": row.pnrno}))
		except Exception:
			frappe.log_error(
				title=f"Discount register flow skip ({row.get('partyid')})",
				message=frappe.get_traceback(),
			)
			continue
	return _merge_sorted(rows, "pnrdate", "pnrno")


def _query_discount_pnr_register_detail(parent_table: str, filters: dict) -> list[dict]:
	conditions, params = _register_date_filters(filters, "pnrdate", prefix="doc")
	if filters.get("partyid"):
		conditions.append("doc.partyid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	parents = frappe.db.sql(
		f"""SELECT doc.name, doc.pnrno, doc.pnrdate, doc.location_id, doc.partyid,
			party.party_name, doc.amount, doc.narration, doc.posted, doc.referno, doc.referdate
		FROM `tab{parent_table}` doc
		LEFT JOIN `tabParty` party ON party.name = doc.partyid
		WHERE {" AND ".join(conditions)}
		ORDER BY doc.pnrdate, doc.pnrno
		""",
		params,
		as_dict=True,
	)
	rows: list[dict] = []
	for parent in parents:
		rows.extend(_expand_pnr_discount_parent(parent))
	return rows


def _expand_pnr_discount_parent(parent: dict) -> list[dict]:
	doc_lines = frappe.get_all(
		"Payment and Receipt Document",
		filters={"parent": parent["name"]},
		fields=["documentid", "party_name", "item_name", "docbalamnt", "amount", "idx"],
		order_by="idx asc",
	)
	base = {
		"pnrno": parent.get("pnrno"),
		"pnrdate": parent.get("pnrdate"),
		"location_id": parent.get("location_id"),
		"partyid": parent.get("partyid"),
		"party_name": parent.get("party_name"),
		"doc_amount": flt(parent.get("amount")),
		"narration": parent.get("narration"),
		"posted": parent.get("posted"),
		"referno": parent.get("referno"),
		"referdate": parent.get("referdate"),
	}
	if not doc_lines:
		return [{**base, "invoice_no": "", "item_name": "", "docbalamnt": 0, "amount": flt(parent.get("amount"))}]
	return [
		{
			**base,
			"invoice_no": line.documentid,
			"item_name": line.item_name or "",
			"docbalamnt": flt(line.docbalamnt),
			"amount": flt(line.amount),
		}
		for line in doc_lines
	]


def get_payment_register_detail_rows(filters: dict | None = None, *, receipt: bool | None = None) -> list[dict]:
	"""Oracle Payment_Register / Receipt_Register — CNB header + GL detail lines."""
	filters = normalize_report_dates(filters or {})
	table = RECEIPT_VOUCHER if receipt else PAYMENT_VOUCHER
	rows = _query_cnb_register_detail(table, filters)
	for parent in _legacy_cnb_register(filters, receipt=receipt):
		parent_name = frappe.db.get_value(_LEGACY_CNB, {"cnbvno": parent.cnbvno}, "name")
		if parent_name:
			rows.extend(
				_expand_cnb_register_parent(
					{
						**parent,
						"name": parent_name,
						"paymode": parent.get("vouchmode"),
						"bank_desc": parent.get("vouchmode") or "Cash",
					}
				)
			)
	return _merge_sorted(rows, "vouchdate", "cnbvno")


def _query_cnb_register_detail(parent_table: str, filters: dict) -> list[dict]:
	conditions, params = _register_date_filters(filters, "vouchdate", prefix="doc")
	parents = frappe.db.sql(
		f"""SELECT doc.name, doc.cnbvno, doc.vouchdate, doc.location_id, doc.paymode, doc.amount,
			doc.posted, doc.narration, doc.referno, doc.referdate, doc.bankaccid, doc.primary_acc,
			COALESCE(coa.description, doc.paymode, 'Cash') AS bank_desc
		FROM `tab{parent_table}` doc
		LEFT JOIN `tabChart of Accounting` coa ON coa.name = COALESCE(doc.bankaccid, doc.primary_acc)
		WHERE {" AND ".join(conditions)}
		ORDER BY doc.vouchdate, doc.cnbvno
		""",
		params,
		as_dict=True,
	)
	rows: list[dict] = []
	for parent in parents:
		rows.extend(_expand_cnb_register_parent(parent))
	return rows


def _expand_cnb_register_parent(parent: dict) -> list[dict]:
	details = frappe.get_all(
		"Cash and Bank Voucher Detail",
		filters={"parent": parent["name"]},
		fields=["accid", "amount", "detail", "idx"],
		order_by="idx asc",
	)
	paymode_desc = parent.get("bank_desc") or parent.get("paymode") or "Cash"
	base = {
		"cnbvno": parent.get("cnbvno"),
		"vouchdate": parent.get("vouchdate"),
		"location_id": parent.get("location_id"),
		"paymode_desc": paymode_desc,
		"referno": parent.get("referno"),
		"referdate": parent.get("referdate"),
		"doc_amount": flt(parent.get("amount")),
		"narration": parent.get("narration"),
		"posted": parent.get("posted"),
	}
	if not details:
		return [
			{
				**base,
				"accid": parent.get("bankaccid") or parent.get("primary_acc") or "",
				"account_name": paymode_desc,
				"amount": flt(parent.get("amount")),
				"detail": parent.get("narration") or "",
			}
		]
	out: list[dict] = []
	for line in details:
		acc_name = (
			frappe.db.get_value("Chart of Accounting", line.accid, "description") if line.accid else paymode_desc
		)
		out.append(
			{
				**base,
				"accid": line.accid or "",
				"account_name": acc_name or paymode_desc,
				"amount": flt(line.amount),
				"detail": line.detail or "",
			}
		)
	return out


def get_cnb_register_rows(filters: dict | None = None, *, receipt: bool | None = None) -> list[dict]:
	filters = normalize_report_dates(filters or {})
	table = RECEIPT_VOUCHER if receipt else PAYMENT_VOUCHER
	rows = _query_cnb_register(table, filters)
	rows.extend(_legacy_cnb_register(filters, receipt=receipt))
	return _merge_sorted(rows, "vouchdate", "cnbvno")


def _query_adj_register_detail(parent_table: str, filters: dict, *, pcat_id: str | None = None) -> list[dict]:
	conditions, params = _register_date_filters(filters, "adjdate", prefix="doc")
	join_party = "LEFT JOIN `tabParty` party ON party.name = doc.partyid"
	if pcat_id:
		conditions.append("party.pcat_id = %(pcat_id)s")
		params["pcat_id"] = pcat_id
	parents = frappe.db.sql(
		f"""SELECT doc.name, doc.adjid, doc.adjdate, doc.location_id, doc.partyid,
			party.party_name, doc.amount, doc.narration, doc.posted
		FROM `tab{parent_table}` doc
		{join_party}
		WHERE {" AND ".join(conditions)}
		ORDER BY doc.adjdate, doc.adjid
		""",
		params,
		as_dict=True,
	)
	rows: list[dict] = []
	for parent in parents:
		invoice_lines = frappe.get_all(
			"Adjustment Invoice",
			filters={"parent": parent.name},
			fields=["documentid", "party_name", "item_name", "docbalamnt", "amount", "idx"],
			order_by="idx asc",
		)
		pnr_lines = frappe.get_all(
			"Adjustment PNR",
			filters={"parent": parent.name},
			fields=["pnrno", "amount", "idx"],
			order_by="idx asc",
		)
		pnr_by_idx = {int(row.idx): row for row in pnr_lines if row.idx}
		if not invoice_lines:
			rows.append(
				{
					"adjid": parent.adjid,
					"adjdate": parent.adjdate,
					"location_id": parent.location_id,
					"partyid": parent.partyid,
					"party_name": parent.party_name,
					"doc_amount": flt(parent.amount),
					"narration": parent.narration,
					"posted": parent.posted,
					"item_name": "",
					"invoice_no": "",
					"inv_amount": 0,
					"sub_doc_id": "",
					"sub_doc_amount": 0,
					"line_amount": flt(parent.amount),
				}
			)
			continue
		for inv in invoice_lines:
			pnr = pnr_by_idx.get(int(inv.idx or 0))
			rows.append(
				{
					"adjid": parent.adjid,
					"adjdate": parent.adjdate,
					"location_id": parent.location_id,
					"partyid": parent.partyid,
					"party_name": parent.party_name or inv.party_name,
					"doc_amount": flt(parent.amount),
					"narration": parent.narration,
					"posted": parent.posted,
					"item_name": inv.item_name,
					"invoice_no": inv.documentid,
					"inv_amount": flt(inv.docbalamnt),
					"sub_doc_id": pnr.pnrno if pnr else "",
					"sub_doc_amount": flt(pnr.amount) if pnr else 0,
					"line_amount": flt(inv.amount),
				}
			)
	return rows


def get_advance_adjustment_register(filters: dict | None = None, *, received: bool = True) -> list[dict]:
	filters = normalize_report_dates(filters or {})
	table = RECEIVED_ADVANCE_ADJUSTMENT if received else PAID_ADVANCE_ADJUSTMENT
	pcat_id = _ADVANCE_PCAT["receipt" if received else "payment"]
	rows = _query_adj_register_detail(table, filters, pcat_id=pcat_id if not filters.get("partyid") else None)
	legacy_doctypeid = table
	for legacy in _legacy_adj_register(filters, doctypeid=legacy_doctypeid):
		if pcat_id and not filters.get("partyid"):
			party_pcat = frappe.db.get_value("Party", legacy.partyid, "pcat_id")
			if str(party_pcat) != pcat_id:
				continue
		legacy.setdefault("party_name", frappe.db.get_value("Party", legacy.partyid, "party_name"))
		legacy["doc_amount"] = flt(legacy.pop("amount", 0))
		legacy["line_amount"] = legacy["doc_amount"]
		legacy.setdefault("item_name", "")
		legacy.setdefault("invoice_no", "")
		legacy.setdefault("inv_amount", 0)
		legacy.setdefault("sub_doc_id", "")
		legacy.setdefault("sub_doc_amount", 0)
		rows.append(legacy)
	return _merge_sorted(rows, "adjdate", "adjid")


def get_hawala_register_rows(filters: dict | None = None) -> list[dict]:
	filters = normalize_report_dates(filters or {})
	conditions = ["gm.docstatus = 1"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append("gm.gmdate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("gm.gmdate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append("gm.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	return frappe.db.sql(
		f"""SELECT gm.gmid, gm.gmdate, gm.location_id, gm.partyid, gm.gmmode, gm.amount, gm.posted, gm.narration
		FROM `tabPayment By Hawala` gm
		WHERE {" AND ".join(conditions)}
		ORDER BY gm.gmdate, gm.gmid
		""",
		params,
		as_dict=True,
	)


def get_income_statement_rows(filters: dict | None = None) -> list[dict]:
	from millitrix.utils.field_normalizers import nature_matches

	rows = _get_gl_statement_rows(filters, statement="Income Statement")
	if rows is not None:
		return rows
	rows = get_trial_balance_rows(filters)
	out = []
	for row in rows:
		nature = frappe.db.get_value("Chart of Accounting", row["accid"], "nature")
		if nature and nature_matches(nature, "R", "E"):
			out.append({**row, "nature": nature})
	return out


def _pnl_signed_amount(debit: float, credit: float, nature: str | None) -> float:
	from millitrix.utils.field_normalizers import nature_matches

	net = flt(debit) - flt(credit)
	if nature and nature_matches(nature, "R", "L", "C"):
		return flt(credit) - flt(debit)
	return net


def get_pnl_report_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PNL.RDF — income statement with nature-based balance column."""
	rows = get_income_statement_rows(filters)
	out: list[dict] = []
	for row in rows:
		nature = row.get("nature")
		opening_balance = _pnl_signed_amount(row.get("opening_debit"), row.get("opening_credit"), nature)
		balance = _pnl_signed_amount(row.get("closing_debit"), row.get("closing_credit"), nature)
		out.append(
			{
				**row,
				"opening_balance": flt(opening_balance),
				"balance": flt(balance),
				"balance_side": format_balance_side(balance, nature),
			}
		)
	return out


def get_balance_sheet_rows(filters: dict | None = None) -> list[dict]:
	from millitrix.utils.field_normalizers import nature_matches

	rows = _get_gl_statement_rows(filters, statement="Balance Sheet")
	if rows is not None:
		return rows
	rows = get_trial_balance_rows(filters)
	out = []
	for row in rows:
		nature = frappe.db.get_value("Chart of Accounting", row["accid"], "nature")
		if nature and nature_matches(nature, "A", "L", "C"):
			out.append({**row, "nature": nature})
	return out


def _get_gl_statement_rows(filters: dict | None, *, statement: str) -> list[dict] | None:
	"""Build report from active GL Statements template (Oracle View_GL_Statements)."""
	filters = normalize_report_dates(filters or {})
	templates = frappe.get_all(
		"GL Statements",
		filters={"statement": statement, "active": "Yes"},
		fields=["name", "description", "statementid"],
		order_by="statementid asc",
	)
	if not templates:
		return None

	tb_by_acc = {row["accid"]: row for row in get_trial_balance_rows(filters)}
	rows: list[dict] = []
	for tmpl in templates:
		doc = frappe.get_doc("GL Statements", tmpl.name)
		if not doc.gl_accounts:
			continue
		for gl_row in doc.gl_accounts:
			tb = tb_by_acc.get(gl_row.accid)
			if not tb:
				continue
			closing_debit = flt(tb.get("closing_debit"))
			closing_credit = flt(tb.get("closing_credit"))
			if not filters.get("show_zero_values") and not closing_debit and not closing_credit:
				continue
			nature = frappe.db.get_value("Chart of Accounting", gl_row.accid, "nature")
			rows.append(
				{
					"statement_line": doc.description,
					"accid": gl_row.accid,
					"account_name": gl_row.account_description or tb.get("account_name"),
					"nature": nature,
					"opening_debit": flt(tb.get("opening_debit")),
					"opening_credit": flt(tb.get("opening_credit")),
					"debit": flt(tb.get("debit")),
					"credit": flt(tb.get("credit")),
					"closing_debit": closing_debit,
					"closing_credit": closing_credit,
				}
			)
	return rows or None


def get_party_balance_report_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PartyBalance.RDF — party GL opening + period Dr/Cr + nature-based balance."""
	from frappe.utils import add_days, getdate

	filters = normalize_report_dates(filters or {})
	party_query: dict = {}
	if filters.get("pcat_id"):
		party_query["pcat_id"] = filters["pcat_id"]
	if filters.get("partyid"):
		party_query["name"] = filters["partyid"]
	parties = frappe.get_all(
		"Party",
		filters=party_query or None,
		fields=["name", "party_name", "pcat_id"],
		order_by="name",
	)
	if not parties:
		return []

	pcat_meta: dict[str, dict] = {}
	for row in frappe.get_all("Party Category", fields=["pcat_id", "description", "accid"]):
		nature = frappe.db.get_value("Chart of Accounting", row.accid, "nature") if row.accid else None
		pcat_meta[str(row.pcat_id)] = {"status": row.description, "nature": nature}

	opening_end = str(add_days(getdate(filters["from_date"]), -1))
	show_zero = int(filters.get("show_zero_balance") or 0)
	rows: list[dict] = []
	for party in parties:
		partyid = party.name
		meta = pcat_meta.get(str(party.pcat_id or ""), {})
		nature = meta.get("nature")

		open_filters = {**filters, "partyid": partyid, "to_date": opening_end}
		open_filters.pop("from_date", None)
		open_lines = get_voucher_gl_lines(open_filters)
		open_dr = sum(flt(line.debit) for line in open_lines)
		open_cr = sum(flt(line.credit) for line in open_lines)
		opening_net = flt(open_dr - open_cr)

		period_filters = {**filters, "partyid": partyid}
		period_lines = get_voucher_gl_lines(period_filters)
		period_dr = sum(flt(line.debit) for line in period_lines)
		period_cr = sum(flt(line.credit) for line in period_lines)
		balance = flt(opening_net + period_dr - period_cr)

		if not show_zero and not any(
			abs(v) > 0.009 for v in (opening_net, period_dr, period_cr, balance)
		):
			continue
		rows.append(
			{
				"partyid": partyid,
				"party_name": party.party_name or partyid,
				"pcat_id": party.pcat_id,
				"party_status": meta.get("status") or "",
				"opening_balance": opening_net,
				"total_debit": period_dr,
				"total_credit": period_cr,
				"payment_total": period_cr,
				"balance": balance,
				"balance_side": format_balance_side(balance, nature),
			}
		)
	return rows


def get_party_ledger_summary_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle PartyLedgerSummary.RDF — party-wise GL opening + period Dr/Cr + balance."""
	rows = get_party_balance_report_rows(filters)
	return [
		{
			"partyid": row["partyid"],
			"party_name": row["party_name"],
			"opening_balance": row["opening_balance"],
			"total_debit": row["total_debit"],
			"total_credit": row["total_credit"],
			"balance": row["balance"],
		}
		for row in rows
	]


def get_party_balance_summary(filters: dict | None = None) -> list[dict]:
	filters = normalize_report_dates(filters or {})
	conditions = ["mv.docstatus = 1", "vd.partyid IS NOT NULL AND vd.partyid != ''"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append("mv.vouchdate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("mv.vouchdate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append("mv.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("partyid"):
		conditions.append("vd.partyid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	return frappe.db.sql(
		f"""SELECT vd.partyid,
			SUM(vd.debit) AS total_debit,
			SUM(vd.credit) AS total_credit,
			SUM(vd.debit) - SUM(vd.credit) AS balance
		FROM `tabVoucher Transaction` mv
		INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
		WHERE {" AND ".join(conditions)}
		GROUP BY vd.partyid
		ORDER BY vd.partyid
		""",
		params,
		as_dict=True,
	)


def get_coa_report_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle COA.RDF — VIEW_COA_LEVELS style L1–L5 hierarchy per account."""
	filters = filters or {}
	level = int(filters.get("chartlevel") or 0)
	accounts = frappe.get_all(
		"Chart of Accounting",
		fields=["name", "accid", "description", "nature", "chartlevel", "parentid", "transflag"],
		order_by="accid",
	)
	by_name = {row.name: row for row in accounts}
	rows: list[dict] = []
	for acc in accounts:
		if level and int(acc.chartlevel or 0) != level:
			continue
		chain: list[dict] = []
		current = acc.name
		seen: set[str] = set()
		while current and current not in seen:
			seen.add(current)
			node = by_name.get(current)
			if not node:
				break
			chain.insert(0, node)
			current = node.parentid or ""
		row = {
			"name": acc.name,
			"accid": acc.accid or acc.name,
			"description": acc.description,
			"nature": acc.nature,
			"chartlevel": acc.chartlevel,
			"parentid": acc.parentid,
			"transflag": acc.transflag,
		}
		for idx in range(1, 6):
			node = chain[idx - 1] if idx <= len(chain) else None
			row[f"l{idx}_accid"] = (node.accid or node.name) if node else ""
			row[f"l{idx}_acc_desc"] = node.description if node else ""
		rows.append(row)
	return rows
