# Shared Paid / Received Advance Adjustment logic (Oracle AdvanceAdjustment.fmb).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.advance_pnr import get_advance_applied_by_pnr
from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import (
	ADVANCE_PAYMENT,
	ADVANCE_PNR,
	ADVANCE_RECEIPT,
	PAID_ADVANCE_ADJUSTMENT,
	PURCHASE_INVOICE,
	PURCHASE_OTHER_BILL,
	RECEIVED_ADVANCE_ADJUSTMENT,
	SALES_INVOICE,
	SALES_OTHER_BILL,
)
from millitrix.utils.child_table_helpers import strip_blank_rows_for_doc
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import mark_posted, mark_unposted

_RECEIPT_INVOICES = frozenset({SALES_INVOICE, SALES_OTHER_BILL})
_PAYMENT_INVOICES = frozenset({PURCHASE_INVOICE, PURCHASE_OTHER_BILL})


def validate_adjustment_doc(
	doc,
	*,
	doctype_id: str,
	flow: str,
	party_pcats: tuple[str, ...],
	advance_doctype: str,
) -> None:
	strip_blank_rows_for_doc(doc)
	check_posted(doc)
	doc.doctypeid = doctype_id
	validate_fiscal_period(doc.adjdate)

	pcat = str(frappe.db.get_value("Party", doc.partyid, "pcat_id") or "")
	if pcat not in party_pcats:
		frappe.throw(_("Invalid party category for {0}").format(doc.doctype))

	if not doc.pnr_lines:
		frappe.throw(_("Add at least one advance PNR line"))
	if not doc.invoice_lines:
		frappe.throw(_("Add at least one invoice line"))

	pnr_total = sum(flt(line.amount) for line in doc.pnr_lines or [])
	inv_total = sum(flt(line.amount) for line in doc.invoice_lines or [])
	if abs(pnr_total - inv_total) > 0.01:
		frappe.throw(_("PNR total {0} must equal invoice total {1}").format(pnr_total, inv_total))
	doc.amount = flt(pnr_total, 2)

	_validate_invoice_lines(doc, flow=flow)
	_validate_advance_pnr_lines(doc, advance_doctype=advance_doctype, flow=flow)

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def _validate_invoice_lines(doc, *, flow: str) -> None:
	for line in doc.invoice_lines or []:
		if flow == "receipt" and line.doctypeid not in _RECEIPT_INVOICES:
			frappe.throw(_("Only customer invoices allowed on {0}").format(doc.doctype))
		if flow == "payment" and line.doctypeid not in _PAYMENT_INVOICES:
			frappe.throw(_("Only supplier invoices allowed on {0}").format(doc.doctype))
		if line.partyid and line.partyid != doc.partyid:
			frappe.throw(
				_("Invoice {0} belongs to party {1}, not {2}").format(
					line.documentid, line.partyid, doc.partyid
				)
			)


def _validate_advance_pnr_lines(doc, *, advance_doctype: str, flow: str) -> None:
	requested: dict[str, float] = {}
	for line in doc.pnr_lines or []:
		pnrno = str(line.pnrno or "").strip()
		if not pnrno:
			frappe.throw(_("Advance PNR number is required"))
		requested[pnrno] = requested.get(pnrno, 0) + flt(line.amount)

	applied = get_advance_applied_by_pnr(list(requested))
	for pnrno, req_amt in requested.items():
		from millitrix.utils.advance_pnr import advance_exists

		if not advance_exists(pnrno, partyid=doc.partyid, location_id=doc.location_id):
			frappe.throw(_("Advance PNR {0} not found or not submitted").format(pnrno))

		pnr = _load_advance_pnr(pnrno, flow=flow)
		if pnr.partyid != doc.partyid:
			frappe.throw(_("Advance PNR {0} belongs to a different party").format(pnrno))
		if pnr.location_id != doc.location_id:
			frappe.throw(_("Advance PNR {0} belongs to a different location").format(pnrno))
		outstanding = flt(pnr.amount) - flt(applied.get(pnrno))
		if req_amt > outstanding + 0.01:
			frappe.throw(
				_("Advance PNR {0} balance {1} is less than applied amount {2}").format(
					pnrno, outstanding, req_amt
				)
			)


def _load_advance_pnr(pnrno, *, flow: str):
	filters = {"pnrno": str(pnrno), "docstatus": 1}
	flow_label = "Payment" if flow == "payment" else "Receipt"
	row = frappe.db.get_value(
		ADVANCE_PNR,
		{**filters, "advance_flow": flow_label},
		["amount", "partyid", "location_id"],
		as_dict=True,
	)
	if row:
		return row
	legacy_table = ADVANCE_PAYMENT if flow == "payment" else ADVANCE_RECEIPT
	row = frappe.db.get_value(
		legacy_table,
		filters,
		["amount", "partyid", "location_id"],
		as_dict=True,
	)
	if row:
		return row
	legacy_filters = {**filters, "pnr_type": "Advance"}
	row = frappe.db.get_value(
		"Payment and Receipt Voucher",
		legacy_filters,
		["amount", "partyid", "location_id"],
		as_dict=True,
	)
	if row:
		return row
	frappe.throw(_("Advance PNR {0} not found").format(pnrno))


def submit_adjustment_doc(doc, *, flow: str) -> None:
	doc_key = resolve_document_key(doc, "adjid")
	batch = _build_adjustment_transactions(doc, flow=flow, doc_key=doc_key)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.adjdate,
		narration=doc.narration or f"{doc.doctype} {doc.adjid}",
	)
	mark_posted(doc)


def cancel_adjustment_doc(doc) -> None:
	doc_key = resolve_document_key(doc, "adjid")
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": doc.doctypeid, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, doc.doctypeid, doc_key)
	mark_unposted(doc)


def preview_adjustment_accounting_lines(doc, *, flow: str) -> list[dict]:
	batch = _build_adjustment_transactions(doc, flow=flow)
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


def get_posted_adjustment_accounting_lines(doc) -> list[dict]:
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
			"documentid": resolve_document_key(doc, "adjid"),
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


def _build_adjustment_transactions(doc, *, flow: str, doc_key: str | None = None) -> DocTranBatch:
	doc_key = doc_key or resolve_document_key(doc, "adjid")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	party_acc = get_party_accid(doc.partyid)

	for line in doc.invoice_lines or []:
		amt = flt(line.amount)
		detail = f"Apply advance to {line.doctypeid} {line.documentid}"
		if flow == "receipt":
			batch.dr(party_acc, amt, partyid=doc.partyid, detail=detail)
		else:
			batch.cr(party_acc, amt, partyid=doc.partyid, detail=detail)

	for line in doc.pnr_lines or []:
		amt = flt(line.amount)
		detail = f"Advance PNR {line.pnrno}"
		if flow == "receipt":
			batch.cr(party_acc, amt, partyid=doc.partyid, detail=detail)
		else:
			batch.dr(party_acc, amt, partyid=doc.partyid, detail=detail)

	return batch
