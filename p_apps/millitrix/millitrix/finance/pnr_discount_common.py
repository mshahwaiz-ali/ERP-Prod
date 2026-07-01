# Shared Payable / Receivable Discount Note logic (Oracle PNRDiscount.fmb).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import (
	PURCHASE_INVOICE,
	PURCHASE_OTHER_BILL,
	SALES_INVOICE,
	SALES_OTHER_BILL,
)
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_discount_account, get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import mark_posted, mark_unposted

_RECEIPT_DOCTYPES = frozenset({SALES_INVOICE, SALES_OTHER_BILL})
_PAYMENT_DOCTYPES = frozenset({PURCHASE_INVOICE, PURCHASE_OTHER_BILL})


def validate_pnr_discount_doc(
	doc,
	*,
	doctype_id: str,
	flow: str,
	party_pcats: tuple[str, ...],
) -> None:
	check_posted(doc)
	doc.doctypeid = doctype_id
	validate_fiscal_period(doc.pnrdate)

	pcat = str(frappe.db.get_value("Party", doc.partyid, "pcat_id") or "")
	if pcat not in party_pcats:
		frappe.throw(_("Invalid party category for {0}").format(doc.doctype))

	if doc.instruments:
		frappe.throw(_("Discount note cannot have payment instruments"))
	if not doc.documents:
		frappe.throw(_("Add at least one discount amount"))

	doc_total = sum(flt(line.amount) for line in doc.documents or [])
	if doc_total <= 0:
		frappe.throw(_("Add at least one discount amount"))
	doc.amount = flt(doc_total, 2)

	for line in doc.documents or []:
		if flow == "receipt" and line.doctypeid not in _RECEIPT_DOCTYPES:
			frappe.throw(_("Only customer invoices allowed on {0}").format(doc.doctype))
		if flow == "payment" and line.doctypeid not in _PAYMENT_DOCTYPES:
			frappe.throw(_("Only supplier invoices allowed on {0}").format(doc.doctype))

	_validate_discount_document_lines(doc)

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def _validate_discount_document_lines(doc) -> None:
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

		discount = flt(line.amount)
		if discount <= 0:
			frappe.throw(_("Row {0}: discount amount must be greater than zero").format(idx))

		outstanding = flt(line.docbalamnt)
		if outstanding and discount - outstanding > 0.01:
			frappe.throw(
				_("Row {0}: discount {1} exceeds outstanding balance {2}").format(
					idx, discount, outstanding
				)
			)


def submit_pnr_discount_doc(doc, *, flow: str) -> None:
	doc_key = resolve_document_key(doc, "pnrno")
	batch = _build_discount_transactions(doc, flow=flow, doc_key=doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.pnrdate,
		narration=doc.narration or f"{doc.doctype} {doc.pnrno} — {doc.partyid}",
	)
	mark_posted(doc)


def cancel_pnr_discount_doc(doc) -> None:
	doc_key = resolve_document_key(doc, "pnrno")
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": doc.doctypeid, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, doc.doctypeid, doc_key)
	mark_unposted(doc)


def preview_pnr_discount_accounting_lines(doc, *, flow: str) -> list[dict]:
	doc_key = resolve_document_key(doc, "pnrno")
	batch = _build_discount_transactions(doc, flow=flow, doc_key=doc_key)
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


def get_posted_pnr_discount_accounting_lines(doc) -> list[dict]:
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


def _build_discount_transactions(doc, *, flow: str, doc_key: str | None = None) -> DocTranBatch:
	doc_key = doc_key or resolve_document_key(doc, "pnrno")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	party_acc = get_party_accid(doc.partyid)
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

	return batch
