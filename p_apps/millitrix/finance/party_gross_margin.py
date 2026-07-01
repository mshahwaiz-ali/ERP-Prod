# Copyright (c) 2026, Millitrix and contributors
# Blueprint 12.48 — GM_PARTY_A / B party gross margin allocation

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import (
	PARTY_GROSS_MARGIN,
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

_RECEIPT_DOCS = frozenset({SALES_INVOICE, SALES_OTHER_BILL})
_PAYMENT_DOCS = frozenset({PURCHASE_INVOICE, PURCHASE_OTHER_BILL})


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = PARTY_GROSS_MARGIN
	validate_fiscal_period(doc.pgdate)
	if not doc.party_b_lines:
		frappe.throw(_("Add at least one Party B line"))

	header_amt = flt(doc.amount)
	party_b_total = sum(flt(line.amount) for line in doc.party_b_lines or [])
	invoice_total = sum(flt(line.amount) for line in doc.invoices or [])
	if header_amt <= 0:
		header_amt = max(party_b_total, invoice_total)
		doc.amount = header_amt
	if party_b_total > 0 and abs(party_b_total - header_amt) > 0.01:
		frappe.throw(_("Party B total {0} must equal header amount {1}").format(party_b_total, header_amt))
	if invoice_total > 0 and abs(invoice_total - header_amt) > 0.01:
		frappe.throw(_("Invoice total {0} must equal header amount {1}").format(invoice_total, header_amt))

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "pgmid")
	batch = _build_party_gm_transactions(doc, doc_key=doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.pgdate,
		narration=doc.narration or f"Party GM {doc.pgmid}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _is_debit_mode(mode: str | None) -> bool:
	return (mode or "").upper() in ("DR", "D", "DEBIT", "P", "PAYMENT")


def _build_party_gm_transactions(doc, *, doc_key: str | None = None) -> DocTranBatch:
	doc_key = doc_key or resolve_document_key(doc, "pgmid")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	header_amt = flt(doc.amount)
	header_debit = _is_debit_mode(doc.pgmode)
	header_acc = doc.accid
	header_party = doc.partyid

	if header_debit:
		batch.dr(
			header_acc,
			header_amt,
			partyid=header_party,
			itemcode=doc.itemcode,
			detail=doc.narration or f"Party GM A {doc.pgmid}",
			trans_id=doc.trans_id,
		)
	else:
		batch.cr(
			header_acc,
			header_amt,
			partyid=header_party,
			itemcode=doc.itemcode,
			detail=doc.narration or f"Party GM A {doc.pgmid}",
			trans_id=doc.trans_id,
		)

	for line in doc.party_b_lines or []:
		amt = flt(line.amount)
		if amt <= 0:
			continue
		acc = line.accid
		detail = line.narration or f"Party GM B {line.partyid or ''}".strip()
		if header_debit:
			batch.cr(acc, amt, partyid=line.partyid, itemcode=line.itemcode, detail=detail, trans_id=line.trans_id)
		else:
			batch.dr(acc, amt, partyid=line.partyid, itemcode=line.itemcode, detail=detail, trans_id=line.trans_id)

	if doc.invoices:
		flow = _invoice_flow(doc.invoices)
		for inv in doc.invoices or []:
			amt = flt(inv.amount)
			if amt <= 0:
				continue
			party_acc = get_party_accid(header_party) if header_party else header_acc
			detail = f"Party GM knockoff {inv.doctypeid} {inv.documentid}"
			if flow == "receipt":
				batch.cr(party_acc, amt, partyid=header_party, detail=detail)
			else:
				batch.dr(party_acc, amt, partyid=header_party, detail=detail)
			suspense = flt(inv.suspense)
			if suspense > 0:
				suspense_acc = get_setting_account("Suspense")
				if flow == "receipt":
					batch.cr(suspense_acc, suspense, detail="Party GM suspense")
				else:
					batch.dr(suspense_acc, suspense, detail="Party GM suspense")

	return batch


def _invoice_flow(documents) -> str:
	modes: set[str] = set()
	for line in documents or []:
		if line.doctypeid in _RECEIPT_DOCS:
			modes.add("receipt")
		elif line.doctypeid in _PAYMENT_DOCS:
			modes.add("payment")
		else:
			frappe.throw(_("Unsupported party gross margin document type {0}").format(line.doctypeid))
	if len(modes) != 1:
		frappe.throw(_("Party gross margin invoices cannot mix receipt and payment document types"))
	return modes.pop()
