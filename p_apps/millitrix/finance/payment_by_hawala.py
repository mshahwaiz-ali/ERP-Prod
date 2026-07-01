# Copyright (c) 2026, Millitrix and contributors
# Blueprint 9.20 — GM_PARTY_A / B dual-party hawala

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.child_table_helpers import strip_blank_rows_for_doc
from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import (
	PAYMENT_BY_HAWALA,
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

_CREDIT_LINE_FIELDS = (
	"partyid",
	"itemcode",
	"accid",
	"gmmode",
	"referno",
	"referdate",
	"amount",
	"narration",
)


def sync_hawala_credit_section(doc) -> None:
	"""Sync flat credit fields ↔ party_b_lines (API/import paths)."""
	line_data = {field: doc.get(f"b_{field}") for field in _CREDIT_LINE_FIELDS}
	line_data["gmmode"] = line_data.get("gmmode") or "GL Code"
	if not any(line_data.get(field) for field in _CREDIT_LINE_FIELDS):
		return
	if not doc.party_b_lines:
		doc.append("party_b_lines", line_data)
		return
	row = doc.party_b_lines[0]
	for field, value in line_data.items():
		row.set(field, value)
	while len(doc.party_b_lines) > 1:
		doc.remove(doc.party_b_lines[-1])


def validate(doc, method=None):
	sync_hawala_credit_section(doc)
	strip_blank_rows_for_doc(doc)
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = PAYMENT_BY_HAWALA
	validate_fiscal_period(doc.gmdate)

	if not doc.partyid:
		frappe.throw(_("Debit party is required"))
	if not doc.b_partyid:
		frappe.throw(_("Credit party is required"))
	if not doc.accid:
		frappe.throw(_("Debit account is required"))
	if not doc.b_accid:
		frappe.throw(_("Credit account is required"))

	if not doc.party_b_lines:
		frappe.throw(_("Complete the Credit section"))

	debit_amt = flt(doc.amount)
	credit_amt = flt(doc.b_amount) or sum(flt(line.amount) for line in doc.party_b_lines or [])
	invoice_total = sum(flt(line.amount) for line in doc.invoices or [])
	if debit_amt <= 0:
		debit_amt = max(credit_amt, invoice_total)
		doc.amount = debit_amt
	if debit_amt <= 0:
		frappe.throw(_("Debit amount must be greater than zero"))
	if credit_amt <= 0:
		frappe.throw(_("Credit amount must be greater than zero"))
	if abs(debit_amt - credit_amt) > 0.01:
		frappe.throw(
			_("Debit amount {0} must equal credit amount {1}").format(debit_amt, credit_amt)
		)
	if not flt(doc.b_amount):
		doc.b_amount = credit_amt


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "gmid")
	batch = _build_hawala_transactions(doc, doc_key=doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.gmdate,
		narration=doc.narration or f"Hawala {doc.gmid}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _is_debit_mode(mode: str | None) -> bool:
	return (mode or "").upper() in ("DR", "D", "DEBIT", "P", "PAYMENT")


def _build_hawala_transactions(doc, *, doc_key: str | None = None) -> DocTranBatch:
	doc_key = doc_key or resolve_document_key(doc, "gmid")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	header_amt = flt(doc.amount)
	header_debit = True
	header_acc = doc.accid
	header_party = doc.partyid

	if header_debit:
		batch.dr(
			header_acc,
			header_amt,
			partyid=header_party,
			itemcode=doc.itemcode,
			detail=doc.narration or f"Hawala A {doc.gmid}",
			trans_id=doc.trans_id,
		)
	else:
		batch.cr(
			header_acc,
			header_amt,
			partyid=header_party,
			itemcode=doc.itemcode,
			detail=doc.narration or f"Hawala A {doc.gmid}",
			trans_id=doc.trans_id,
		)

	for line in doc.party_b_lines or []:
		amt = flt(line.amount)
		if amt <= 0:
			continue
		acc = line.accid
		detail = line.narration or f"Hawala B {line.partyid or ''}".strip()
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
			detail = f"Hawala knockoff {inv.doctypeid} {inv.documentid}"
			if flow == "receipt":
				batch.cr(party_acc, amt, partyid=header_party, detail=detail)
			else:
				batch.dr(party_acc, amt, partyid=header_party, detail=detail)
			suspense = flt(inv.suspense)
			if suspense > 0:
				suspense_acc = get_setting_account("Suspense")
				if flow == "receipt":
					batch.cr(suspense_acc, suspense, detail="Hawala suspense")
				else:
					batch.dr(suspense_acc, suspense, detail="Hawala suspense")

	return batch


def preview_hawala_accounting_lines(doc) -> list[dict]:
	batch = _build_hawala_transactions(doc)
	lines: list[dict] = []
	for row in batch.rows:
		lines.append(
			{
				"accid": row.accid,
				"account": frappe.db.get_value("Chart of Accounting", row.accid, "description")
				or row.accid,
				"debit": round(flt(row.debit), 2),
				"credit": round(flt(row.credit), 2),
				"detail": row.detail or "",
				"partyid": row.partyid,
			}
		)
	return lines


def get_posted_hawala_accounting_lines(doc) -> list[dict]:
	doc_key = resolve_document_key(doc, "gmid")
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
			"debit": round(flt(row.debit), 2),
			"credit": round(flt(row.credit), 2),
			"detail": row.detail or "",
			"partyid": row.partyid,
		}
		for row in rows
	]


def _invoice_flow(documents) -> str:
	modes: set[str] = set()
	for line in documents or []:
		if line.doctypeid in _RECEIPT_DOCS:
			modes.add("receipt")
		elif line.doctypeid in _PAYMENT_DOCS:
			modes.add("payment")
		else:
			frappe.throw(_("Unsupported hawala document type {0}").format(line.doctypeid))
	if len(modes) != 1:
		frappe.throw(_("Hawala invoices cannot mix receipt and payment document types"))
	return modes.pop()
