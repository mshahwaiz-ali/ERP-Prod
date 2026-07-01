# Shared Party Payment / Receipt Voucher logic (Oracle CNBPartyVoucher.fmb).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.finance.cnb_voucher import _build_cnb_transactions
from millitrix.utils.doc_transaction import persist_doc_transactions
from millitrix.utils.child_table_helpers import strip_blank_rows_for_doc
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.stock import mark_posted, mark_unposted


def validate_cnb_party_doc(
	doc,
	*,
	doctype_id: str,
	voucher_mode: str,
	party_pcats: tuple[str, ...] | None = None,
) -> None:
	"""Party CNB — document knockoff grid only."""
	strip_blank_rows_for_doc(doc)
	check_posted(doc)
	doc.doctypeid = doctype_id
	validate_fiscal_period(doc.vouchdate)

	if party_pcats:
		for line in doc.documents or []:
			if not line.partyid:
				continue
			pcat = str(frappe.db.get_value("Party", line.partyid, "pcat_id") or "")
			if pcat not in party_pcats:
				frappe.throw(_("Invalid party category for {0}").format(line.partyid))

	if doc.partyid and party_pcats:
		header_pcat = str(frappe.db.get_value("Party", doc.partyid, "pcat_id") or "")
		if header_pcat not in party_pcats:
			frappe.throw(_("Invalid party category for header party {0}").format(doc.partyid))

	if doc.details:
		frappe.throw(_("This voucher type does not use account detail lines"))
	if not doc.documents:
		frappe.throw(_("Add at least one knockoff document line"))

	for line in doc.documents or []:
		if not line.partyid:
			frappe.throw(_("Party is required on each document line"))

	_validate_knockoff_document_lines(doc)

	knockoff_total = sum(flt(line.amount) for line in doc.documents or [])
	doc_total = flt(doc.amount) or knockoff_total
	if knockoff_total > 0 and abs(knockoff_total - doc_total) > 0.01:
		frappe.throw(_("Knockoff total {0} must equal voucher amount {1}").format(knockoff_total, doc_total))
	doc.amount = doc_total

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def _validate_knockoff_document_lines(doc) -> None:
	seen: set[tuple[str, str, str]] = set()
	for idx, line in enumerate(doc.documents or [], start=1):
		key = (
			str(line.partyid or ""),
			str(line.doctypeid or ""),
			str(line.documentid or ""),
		)
		if not key[0] or not key[2]:
			frappe.throw(_("Row {0}: party and document id are required").format(idx))
		if key in seen:
			frappe.throw(
				_("Row {0}: duplicate knockoff for party {1} document {2}").format(
					idx, key[0], key[2]
				)
			)
		seen.add(key)

		paid = flt(line.amount)
		if paid <= 0:
			frappe.throw(_("Row {0}: paid amount must be greater than zero").format(idx))

		outstanding = flt(line.docbalamnt)
		if outstanding and paid - outstanding > 0.01:
			frappe.throw(
				_("Row {0}: paid amount {1} exceeds outstanding balance {2}").format(
					idx, paid, outstanding
				)
			)


def submit_cnb_party_doc(doc) -> None:
	batch = _build_cnb_transactions(doc)
	persist_doc_transactions(batch)
	doc_key = resolve_document_key(doc, "cnbvno")
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.vouchdate,
		narration=doc.narration or f"{doc.doctype} {doc.cnbvno}",
	)
	mark_posted(doc)


def cancel_cnb_party_doc(doc) -> None:
	doc_key = resolve_document_key(doc, "cnbvno")
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": doc.doctypeid, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, doc.doctypeid, doc_key)
	mark_unposted(doc)
