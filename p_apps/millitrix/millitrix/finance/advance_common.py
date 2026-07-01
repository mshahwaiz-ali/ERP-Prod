# Shared Advance Payment / Advance Receipt submit logic (Oracle PNRAdvance.fmb).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import ADVANCE_PAYMENT, ADVANCE_RECEIPT
from millitrix.utils.field_normalizers import normalize_payment_mode
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import mark_posted, mark_unposted


def advance_flow_key(advance_flow: str | None) -> str:
	"""Map Advance PNR flow label to payment/receipt logic key."""
	return "receipt" if (advance_flow or "").strip().lower() == "receipt" else "payment"


def validate_advance_doc(doc, *, flow: str) -> None:
	"""Client Advance Payment / Advance Receipt — header fields only (no invoice grid)."""
	check_posted(doc)
	doc.doctypeid = ADVANCE_PAYMENT if flow == "payment" else ADVANCE_RECEIPT
	validate_fiscal_period(doc.pnrdate)

	if flow == "payment":
		pcat = frappe.db.get_value("Party", doc.partyid, "pcat_id")
		if str(pcat or "") not in ("12",):
			frappe.throw(_("Advance Payment requires a Supplier party"))
	elif flow == "receipt":
		pcat = frappe.db.get_value("Party", doc.partyid, "pcat_id")
		if str(pcat or "") not in ("13",):
			frappe.throw(_("Advance Receipt requires a Customer party"))

	amount = flt(doc.amount)
	if amount <= 0:
		frappe.throw(_("Advance amount must be greater than zero"))
	if not doc.pnrmode:
		frappe.throw(_("Payment mode is required"))

	mode = normalize_payment_mode(doc.pnrmode)
	if mode != "CA" and not doc.bankaccid:
		frappe.throw(_("Bank account is required for {0}").format(doc.pnrmode))

	if doc.is_new() or flt(doc.balance) <= 0:
		doc.balance = amount

	_sync_instrument_from_header(doc)


def _sync_instrument_from_header(doc) -> None:
	"""Oracle PNRAdvance uses header payment fields — one instrument row."""
	doc.set("instruments", [])
	doc.append(
		"instruments",
		{
			"pnrmode": doc.pnrmode,
			"bankaccid": doc.bankaccid,
			"referno": doc.referno,
			"referdate": doc.referdate,
			"amount": flt(doc.amount),
		},
	)


def submit_advance_doc(doc, *, flow: str) -> None:
	doc_key = resolve_document_key(doc, "pnrno")
	batch = _build_advance_transactions(doc, flow=flow)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.pnrdate,
		narration=doc.narration or f"{doc.doctype} {doc.pnrno} — {doc.partyid}",
	)
	mark_posted(doc)


def cancel_advance_doc(doc) -> None:
	doc_key = resolve_document_key(doc, "pnrno")
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": doc.doctypeid, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, doc.doctypeid, doc_key)
	mark_unposted(doc)


def _resolve_bank_acc(doc, instrument) -> str:
	from millitrix.utils.finance_reports import resolve_bank_accid

	raw = instrument.bankaccid or doc.bankaccid
	if raw in (None, ""):
		return get_setting_account("Cash")
	if frappe.db.exists("Chart of Accounting", str(raw)):
		return str(raw)
	if frappe.db.exists("Bank Account", str(raw)):
		accid = frappe.db.get_value("Bank Account", raw, "accid")
		if accid:
			return accid
	if frappe.db.exists("Chart of Accounting", str(raw)):
		return str(raw)
	if str(raw).isdigit():
		accid = resolve_bank_accid(int(raw))
		if accid:
			return accid
	return get_setting_account("Cash")


def preview_advance_accounting_lines(doc, *, flow: str) -> list[dict]:
	"""Oracle accounting grid preview before submit."""
	batch = _build_advance_transactions(doc, flow=flow)
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


def get_posted_advance_accounting_lines(doc) -> list[dict]:
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


def _build_advance_transactions(doc, *, flow: str) -> DocTranBatch:
	doc_key = resolve_document_key(doc, "pnrno")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	party_acc = get_party_accid(doc.partyid)
	party_total = sum(flt(line.amount) for line in doc.instruments or [])
	detail = f"Advance {flow} {doc.doctype} {doc.pnrno}"

	if flow == "receipt":
		batch.cr(party_acc, party_total, partyid=doc.partyid, detail=detail)
	else:
		batch.dr(party_acc, party_total, partyid=doc.partyid, detail=detail)

	for instrument in doc.instruments or []:
		bank_acc = _resolve_bank_acc(doc, instrument)
		amt = flt(instrument.amount)
		inst_detail = f"{instrument.pnrmode} {instrument.referno or ''}".strip()
		if flow == "receipt":
			batch.dr(bank_acc, amt, detail=inst_detail, bnkcash_gl=1)
		else:
			batch.cr(bank_acc, amt, detail=inst_detail, bnkcash_gl=1)

	return batch
