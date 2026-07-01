# Shared Payment / Receipt / Expense Voucher logic (Oracle CNBVoucher.fmb).
# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.finance.cnb_voucher import _build_cnb_transactions, _voucher_document_id
from millitrix.utils.doc_transaction import persist_doc_transactions
from millitrix.utils.child_table_helpers import strip_blank_rows_for_doc
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.stock import mark_posted, mark_unposted


def validate_cnb_general_doc(doc, *, doctype_id: str, voucher_mode: str) -> None:
	"""General CNB — detail grid only (no party knockoff documents)."""
	strip_blank_rows_for_doc(doc)
	check_posted(doc)
	doc.doctypeid = doctype_id
	validate_fiscal_period(doc.vouchdate)

	if doc.documents:
		frappe.throw(_("This voucher type does not use document knockoff lines"))
	if not doc.details:
		frappe.throw(_("Add at least one account detail line"))

	require_trans = doc.doctype == "Expense Voucher"
	for line in doc.details or []:
		if require_trans and not line.trans_id:
			frappe.throw(_("Trans Id is required on each expense line"))
		if line.trans_id:
			from millitrix.utils.transaction_gl import get_transaction_accid

			line.accid = get_transaction_accid(line.trans_id)
		elif not line.accid:
			frappe.throw(_("Account or Transaction is required on each line"))

	line_total = sum(flt(line.amount) for line in doc.details or [])
	doc_total = flt(doc.amount) or line_total
	if line_total > 0 and abs(line_total - doc_total) > 0.01:
		frappe.throw(_("Line total {0} must equal voucher amount {1}").format(line_total, doc_total))
	doc.amount = doc_total

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def submit_cnb_general_doc(doc) -> None:
	doc_key = _voucher_document_id(doc)
	batch = _build_cnb_transactions(doc)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.vouchdate,
		narration=doc.narration or f"{doc.doctype} {doc.cnbvno}",
	)
	mark_posted(doc)


def cancel_cnb_general_doc(doc) -> None:
	doc_key = _voucher_document_id(doc)
	frappe.db.delete(
		"Document Transaction",
		{"location_id": doc.location_id, "doctypeid": doc.doctypeid, "documentid": doc_key},
	)
	delete_voucher_for_document(doc.location_id, doc.doctypeid, doc_key)
	mark_unposted(doc)
