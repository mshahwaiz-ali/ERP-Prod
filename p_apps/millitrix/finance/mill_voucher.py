# Copyright (c) 2026, Millitrix and contributors
# Blueprint 9.17 — manual journal (Transaction.fmx)

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.child_table_helpers import strip_blank_rows_for_doc
from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import MILL_VOUCHER
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.stock import mark_posted, mark_unposted
from millitrix.utils.voucher_balance import batch_from_voucher_details, validate_dr_cr_balance


def validate(doc, method=None):
	strip_blank_rows_for_doc(doc)
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = MILL_VOUCHER
	if not doc.vouchertype_id:
		doc.vouchertype_id = "1"
	validate_fiscal_period(doc.vouchdate)
	if not doc.details:
		frappe.throw(_("Add at least one voucher line"))
	validate_dr_cr_balance(doc.details)
	doc.total_debit = sum(flt(line.debit) for line in doc.details or [])
	doc.total_credit = sum(flt(line.credit) for line in doc.details or [])
	if not doc.documentid:
		doc.documentid = doc.voucherno

	from millitrix.utils.list_view_summary import sync_list_summary_fields

	sync_list_summary_fields(doc)


def on_submit(doc, method=None):
	doc_key = resolve_document_key(doc, "voucherno")
	batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
	batch_from_voucher_details(batch, doc.details)
	persist_doc_transactions(batch)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)