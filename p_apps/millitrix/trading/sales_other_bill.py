from __future__ import annotations
from millitrix.utils.posting_lock import atomic_posting
# Copyright (c) 2026, Millitrix and contributors


import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import SALES_OTHER_BILL
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.stock_key import StockKey
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import mark_posted, mark_unposted, apply_stock_out


def validate(doc, method=None):
    check_posted(doc)
    if not doc.doctypeid:
        doc.doctypeid = SALES_OTHER_BILL
    validate_fiscal_period(doc.billdate)
    from millitrix.utils.child_table_helpers import strip_blank_child_rows

    strip_blank_child_rows(doc, "details", "Sales Other Bill Detail")
    if not doc.details:
        frappe.throw(_("Add bill lines"))
    total = 0.0
    for line in doc.details or []:
        line.amount = round(flt(flt(line.quantity) * flt(line.rate)), 2)
        total += flt(line.amount)
    doc.amount = round(flt(total), 2)



def on_submit(doc, method=None):
    from millitrix.utils.posting_lock import atomic_posting

    with atomic_posting():

        doc_key = resolve_document_key(doc, "sbillno")
        batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)

        rev_acc = get_setting_account("Sales OtherBill")
        party_acc = get_party_accid(doc.partyid)

        total = 0.0

        for line in (doc.details or []):

            amt = flt(line.quantity) * flt(line.rate)
            total += amt

            stock_key = StockKey(
                storeid=doc.location_id,
                itemcode=line.itemcode,
                bags_are="Our"
            )

            apply_stock_out(
                stock_key,
                flt(line.quantity),
                movement_date=doc.billdate,
                check_reserved=False
            )

            batch.cr(
                rev_acc,
                amt,
                itemcode=line.itemcode,
                detail=f"Other Bill {doc.sbillno}"
            )

            batch.dr(
                party_acc,
                amt,
                partyid=doc.partyid,
                detail=f"Sales Other Bill {doc.sbillno}"
            )

        doc.amount = round(flt(total), 2)
        doc.db_set("amount", total)

        persist_doc_transactions(batch)

        generate_gl(
            location_id=doc.location_id,
            doctypeid=doc.doctypeid,
            documentid=doc_key,
            vouchdate=doc.billdate,
            narration=f"Sales Other Bill {doc.sbillno}",
        )

        mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
