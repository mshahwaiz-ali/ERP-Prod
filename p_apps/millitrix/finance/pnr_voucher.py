# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.6 — PNRSUBMIT / PNRAdvance / PNRDiscount

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.child_table_helpers import strip_blank_rows_for_doc
from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.field_normalizers import normalize_payment_mode
from millitrix.utils.doctype_ids import (
	PNR_ADVANCE,
	PNR_DISCOUNT,
	PNR_VOUCHER,
	PURCHASE_INVOICE,
	PURCHASE_OTHER_BILL,
	SALES_INVOICE,
	SALES_OTHER_BILL,
)
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.knockoff_flow import resolve_knockoff_flow
from millitrix.utils.mill_setting import get_discount_account, get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import mark_posted, mark_unposted
from millitrix.finance.pnr_invoice_common import _sync_document_line_balances

_RECEIPT_DOCTYPES = frozenset({SALES_INVOICE, SALES_OTHER_BILL})
_PAYMENT_DOCTYPES = frozenset({PURCHASE_INVOICE, PURCHASE_OTHER_BILL})


def _pnr_type(doc) -> str:
	return doc.get("pnr_type") or "Invoice"


def _is_advance(doc) -> bool:
	return _pnr_type(doc) == "Advance"


def _is_discount(doc) -> bool:
	return _pnr_type(doc) == "Discount"


def _set_doctypeid(doc) -> None:
	if _is_advance(doc):
		doc.doctypeid = PNR_ADVANCE
	elif _is_discount(doc):
		doc.doctypeid = PNR_DISCOUNT
	else:
		doc.doctypeid = PNR_VOUCHER


def validate(doc, method=None):
	strip_blank_rows_for_doc(doc)
	check_posted(doc)
	_set_doctypeid(doc)
	validate_fiscal_period(doc.pnrdate)

	advance = _is_advance(doc)
	discount = _is_discount(doc)

	if advance and doc.documents:
		frappe.throw(_("Advance PNR cannot have invoice knockoff lines"))
	if discount and doc.instruments:
		frappe.throw(_("Discount PNR cannot have payment instruments"))
	if not advance and not doc.documents:
		frappe.throw(_("Add at least one knockoff document"))

	doc_total = sum(flt(line.amount) for line in doc.documents or [])

	if advance:
		if not doc.instruments:
			frappe.throw(_("Add at least one payment instrument"))
		inst_total = sum(flt(line.amount) for line in doc.instruments or [])
		doc.amount = flt(inst_total, 2)
	elif discount:
		if doc_total <= 0:
			frappe.throw(_("Add at least one discount amount"))
		doc.amount = flt(doc_total, 2)
	else:
		if not doc.instruments:
			frappe.throw(_("Add at least one payment instrument"))
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
	_sync_document_line_balances(doc)

	if not discount:
		_validate_payment_instruments(doc)


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


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "pnrno")
	batch = _build_pnr_transactions(doc, doc_key=doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.pnrdate,
		narration=doc.narration or f"PNR {doc.pnrno} — {doc.partyid}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _resolve_bank_acc(doc, instrument) -> str:
	if instrument.bankaccid:
		acc = str(instrument.bankaccid)
		if frappe.db.exists("Chart of Accounting", acc):
			return acc
	if doc.bankaccid:
		acc = str(doc.bankaccid)
		if frappe.db.exists("Chart of Accounting", acc):
			return acc
	return get_setting_account("Cash")


def _pnr_flow(documents) -> str:
	modes: set[str] = set()
	for line in documents or []:
		if line.doctypeid in _RECEIPT_DOCTYPES:
			modes.add("receipt")
		elif line.doctypeid in _PAYMENT_DOCTYPES:
			modes.add("payment")
		else:
			frappe.throw(_("Unsupported knockoff document type {0}").format(line.doctypeid))
	if len(modes) != 1:
		frappe.throw(_("PNR cannot mix receipt and payment document types"))
	return modes.pop()


def _resolve_flow(doc) -> str:
	if _is_advance(doc):
		return resolve_knockoff_flow(doc.partyid)
	return _pnr_flow(doc.documents)


def _build_pnr_transactions(doc, *, doc_key: str | None = None) -> DocTranBatch:
	doc_key = doc_key or resolve_document_key(doc, "pnrno")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	flow = _resolve_flow(doc)
	party_acc = get_party_accid(doc.partyid)
	advance = _is_advance(doc)
	discount = _is_discount(doc)

	if advance:
		party_total = sum(flt(line.amount) for line in doc.instruments or [])
		detail = f"Advance {flow} PNR {doc.pnrno}"
		if flow == "receipt":
			batch.cr(party_acc, party_total, partyid=doc.partyid, detail=detail)
		else:
			batch.dr(party_acc, party_total, partyid=doc.partyid, detail=detail)
	elif discount:
		disc_acc = get_discount_account(flow)
		for line in doc.documents or []:
			amt = flt(line.amount)
			detail = f"Discount {line.doctypeid} {line.documentid}"
			if flow == "receipt":
				batch.cr(party_acc, amt, partyid=doc.partyid, detail=detail)
				batch.dr(disc_acc, amt, detail=detail)
			else:
				batch.dr(party_acc, amt, partyid=doc.partyid, detail=detail)
				batch.cr(disc_acc, amt, detail=detail)
		suspense_total = sum(flt(line.suspense) for line in doc.documents or [])
		if suspense_total > 0:
			suspense_acc = get_setting_account("Suspense")
			if flow == "receipt":
				batch.cr(suspense_acc, suspense_total, detail="PNR Discount Suspense")
			else:
				batch.dr(suspense_acc, suspense_total, detail="PNR Discount Suspense")
	else:
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

	if not discount:
		for instrument in doc.instruments or []:
			bank_acc = _resolve_bank_acc(doc, instrument)
			amt = flt(instrument.amount)
			detail = f"{instrument.pnrmode} {instrument.referno or ''}".strip()
			if flow == "receipt":
				batch.dr(bank_acc, amt, detail=detail, bnkcash_gl=1)
			else:
				batch.cr(bank_acc, amt, detail=detail, bnkcash_gl=1)

	return batch
