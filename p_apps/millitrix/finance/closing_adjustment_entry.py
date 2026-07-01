# Copyright (c) 2026, Millitrix and contributors
# Blueprint — Closing_Transaction.fmx

from __future__ import annotations

import frappe
from frappe import _

from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import CLOSING_ADJUSTMENT_ENTRY
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.stock import mark_posted, mark_unposted
from millitrix.utils.voucher_balance import batch_from_voucher_details, validate_dr_cr_balance


def validate(doc, method=None):
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = CLOSING_ADJUSTMENT_ENTRY
	validate_fiscal_period(doc.vouchdate)
	if not doc.details:
		frappe.throw(_("Add at least one closing/adjustment line"))
	validate_dr_cr_balance(doc.details)
	doc.total_debit = sum(flt(line.debit) for line in doc.details or [])
	doc.total_credit = sum(flt(line.credit) for line in doc.details or [])
	if doc.voucherno and not doc.documentid:
		doc.documentid = resolve_document_key(doc, "voucherno")

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "voucherno")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	batch_from_voucher_details(batch, doc.details)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.vouchdate,
		narration=doc.narration or f"Closing Adjustment {doc.voucherno}",
		vouchertype_id=doc.vouchertype_id or "1",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)