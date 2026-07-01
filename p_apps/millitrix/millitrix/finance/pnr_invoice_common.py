# Shared Purchase / Sales / Broker Invoice PNR logic (Oracle PNRVoucher.fmb).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.field_normalizers import normalize_payment_mode
from millitrix.utils.doctype_ids import (
	PURCHASE_INVOICE,
	PURCHASE_OTHER_BILL,
	SALES_INVOICE,
	SALES_OTHER_BILL,
)
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import mark_posted, mark_unposted

_RECEIPT_DOCTYPES = frozenset({SALES_INVOICE, SALES_OTHER_BILL})
_PAYMENT_DOCTYPES = frozenset({PURCHASE_INVOICE, PURCHASE_OTHER_BILL})
_BROKER_DOCTYPES = frozenset({PURCHASE_INVOICE, SALES_INVOICE})


def validate_pnr_invoice_doc(
	doc,
	*,
	doctype_id: str,
	flow: str,
	party_pcats: tuple[str, ...],
	allowed_doctypes: frozenset[str],
) -> None:
	check_posted(doc)
	doc.doctypeid = doctype_id
	validate_fiscal_period(doc.pnrdate)

	pcat = str(frappe.db.get_value("Party", doc.partyid, "pcat_id") or "")
	if pcat not in party_pcats:
		frappe.throw(_("Invalid party category for {0}").format(doc.doctype))

	if not doc.documents:
		frappe.throw(_("Add at least one knockoff document"))
	if not doc.instruments:
		frappe.throw(_("Add at least one payment instrument"))

	doc_total = sum(flt(line.amount) for line in doc.documents or [])
	inst_total = sum(flt(line.amount) for line in doc.instruments or [])
	suspense_total = sum(flt(line.suspense) for line in doc.documents or [])
	if abs(doc_total + suspense_total - inst_total) > 0.01:
		frappe.throw(
			_("Document allocation {0} plus suspense {1} must equal instrument total {2}").format(
				doc_total, suspense_total, inst_total
			)
		)
	doc.amount = flt(doc_total, 2)
	doc.balance = 0

	for line in doc.documents or []:
		if line.doctypeid not in allowed_doctypes:
			frappe.throw(_("Unsupported knockoff document type {0}").format(line.doctypeid))
		if flow == "receipt" and line.doctypeid not in _RECEIPT_DOCTYPES:
			frappe.throw(_("Only customer invoices allowed on {0}").format(doc.doctype))
		if flow == "payment" and line.doctypeid not in _PAYMENT_DOCTYPES and line.doctypeid not in _BROKER_DOCTYPES:
			frappe.throw(_("Only supplier/broker invoices allowed on {0}").format(doc.doctype))

	_validate_knockoff_document_lines(doc)
	_sync_document_line_balances(doc)
	_validate_payment_instruments(doc)

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def _sync_document_line_balances(doc) -> None:
	"""Oracle PNRDETAIL.DEFER = DocBalAmnt - (Amount + Suspense)."""
	for idx, line in enumerate(doc.documents or [], start=1):
		defer = flt(line.docbalamnt) - flt(line.amount) - flt(line.suspense)
		line.balance = flt(defer, 2)
		if defer < -0.01:
			frappe.throw(
				_("Row {0}: paid amount plus suspense exceeds document balance {1}").format(
					idx, flt(line.docbalamnt)
				)
			)


def _knockoff_document_party(doctypeid: str, documentid: str, *, payer_pcat: str) -> str | None:
	if doctypeid == PURCHASE_INVOICE:
		field = "brokerid" if payer_pcat == "11" else "supplierid"
		return frappe.db.get_value("Purchase Invoice", documentid, field)
	if doctypeid == PURCHASE_OTHER_BILL:
		return frappe.db.get_value("Purchase Other Bill", documentid, "partyid")
	if doctypeid == SALES_INVOICE:
		field = "brokerid" if payer_pcat == "11" else "customerid"
		return frappe.db.get_value("Sales Invoice", documentid, field)
	if doctypeid == SALES_OTHER_BILL:
		return frappe.db.get_value("Sales Other Bill", documentid, "partyid")
	return None


def _validate_knockoff_document_lines(doc) -> None:
	payer_pcat = str(frappe.db.get_value("Party", doc.partyid, "pcat_id") or "")
	seen: set[tuple[str, str]] = set()
	for idx, line in enumerate(doc.documents or [], start=1):
		key = (str(line.doctypeid or ""), str(line.documentid or ""))
		if not key[0] or not key[1]:
			frappe.throw(_("Row {0}: document type and document id are required").format(idx))
		if key in seen:
			frappe.throw(
				_("Row {0}: duplicate knockoff for {1} {2}").format(idx, key[0], key[1])
			)
		seen.add(key)

		inv_party = _knockoff_document_party(key[0], key[1], payer_pcat=payer_pcat)
		if inv_party and inv_party != doc.partyid:
			frappe.throw(
				_("Row {0}: document {1} belongs to party {2}, not {3}").format(
					idx, key[1], inv_party, doc.partyid
				)
			)

		paid = flt(line.amount)
		if paid <= 0:
			frappe.throw(_("Row {0}: paid amount must be greater than zero").format(idx))

		outstanding = flt(line.balance) if line.get("balance") is not None else flt(line.docbalamnt)
		if outstanding and paid - outstanding > 0.01:
			frappe.throw(
				_("Row {0}: paid amount {1} exceeds outstanding balance {2}").format(
					idx, paid, outstanding
				)
			)


def _validate_payment_instruments(doc) -> None:
	for instrument in doc.instruments or []:
		mode = normalize_payment_mode(instrument.pnrmode)
		if mode == "CA":
			if instrument.bankaccid:
				frappe.throw(
					_("Row {0}: Bank account must be empty for Cash payment mode").format(instrument.idx)
				)
		elif mode in ("CH", "BK", "TC"):
			if not instrument.bankaccid and not doc.bankaccid:
				frappe.throw(
					_("Row {0}: Bank account is required for {1} payment mode").format(
						instrument.idx, instrument.pnrmode
					)
				)


def submit_pnr_invoice_doc(doc, *, flow: str) -> None:
	doc_key = resolve_document_key(doc, "pnrno")
	batch = _build_pnr_invoice_transactions(doc, flow=flow)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.pnrdate,
		narration=doc.narration or f"{doc.doctype} {doc.pnrno} — {doc.partyid}",
	)
	mark_posted(doc)


def cancel_pnr_invoice_doc(doc) -> None:
	doc_key = resolve_document_key(doc, "pnrno")
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": doc.doctypeid, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, doc.doctypeid, doc_key)
	mark_unposted(doc)


def _resolve_bank_acc(doc, instrument) -> str:
	from millitrix.utils.finance_reports import resolve_bank_accid

	accid = resolve_bank_accid(instrument.bankaccid)
	if not accid and doc.bankaccid:
		if frappe.db.exists("Chart of Accounting", doc.bankaccid):
			accid = doc.bankaccid
		else:
			accid = resolve_bank_accid(doc.bankaccid)
	if accid:
		return accid
	return get_setting_account("Cash")


def preview_pnr_invoice_accounting_lines(doc, *, flow: str) -> list[dict]:
	"""Oracle Accounting grid — broker/party DR and bank/cash CR before submit."""
	batch = _build_pnr_invoice_transactions(doc, flow=flow)
	lines: list[dict] = []
	for row in batch.rows:
		lines.append(
			{
				"accid": row.accid,
				"account": frappe.db.get_value("Chart of Accounting", row.accid, "description")
				or row.accid,
				"debit": flt(row.debit, 2),
				"credit": flt(row.credit, 2),
				"detail": row.detail or "",
				"partyid": row.partyid,
			}
		)
	return lines


def get_posted_pnr_accounting_lines(doc) -> list[dict]:
	doc_key = resolve_document_key(doc, "pnrno")
	rows = frappe.db.sql(
		"""
		SELECT
			vd.accid,
			COALESCE(coa.description, vd.accid) AS account,
			vd.partyid,
			COALESCE(vd.debit, 0) AS debit,
			COALESCE(vd.credit, 0) AS credit,
			vd.detail
		FROM `tabVoucher Transaction` vt
		INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = vt.name
		LEFT JOIN `tabChart of Accounting` coa ON coa.name = vd.accid
		WHERE vt.location_id = %(location_id)s
			AND vt.doctypeid = %(doctypeid)s
			AND vt.documentid = %(documentid)s
			AND vt.docstatus = 1
		ORDER BY vd.idx
		""",
		{
			"location_id": doc.location_id,
			"doctypeid": doc.doctypeid,
			"documentid": doc_key,
		},
		as_dict=True,
	)
	return [
		{
			"accid": row.accid,
			"account": row.account,
			"debit": flt(row.debit, 2),
			"credit": flt(row.credit, 2),
			"detail": row.detail or "",
			"partyid": row.partyid,
		}
		for row in rows
	]


def _build_pnr_invoice_transactions(doc, *, flow: str) -> DocTranBatch:
	doc_key = resolve_document_key(doc, "pnrno")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	party_acc = get_party_accid(doc.partyid)

	suspense_total = sum(flt(line.suspense) for line in doc.documents or [])
	for line in doc.documents or []:
		detail = f"Knockoff {line.doctypeid} {line.documentid}"
		if flow == "receipt":
			batch.cr(party_acc, flt(line.amount), partyid=doc.partyid, detail=detail)
		else:
			batch.dr(party_acc, flt(line.amount), partyid=doc.partyid, detail=detail)

	if suspense_total > 0:
		suspense_acc = get_setting_account("Suspense")
		if flow == "receipt":
			batch.cr(suspense_acc, suspense_total, detail="PNR Suspense")
		else:
			batch.dr(suspense_acc, suspense_total, detail="PNR Suspense")

	for instrument in doc.instruments or []:
		bank_acc = _resolve_bank_acc(doc, instrument)
		amt = flt(instrument.amount)
		detail = f"{instrument.pnrmode} {instrument.referno or ''}".strip()
		if flow == "receipt":
			batch.dr(bank_acc, amt, detail=detail, bnkcash_gl=1)
		else:
			batch.cr(bank_acc, amt, detail=detail, bnkcash_gl=1)

	return batch
