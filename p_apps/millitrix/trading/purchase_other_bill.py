# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.doctype_ids import PURCHASE_OTHER_BILL
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.stock_key import StockKey
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import mark_posted, mark_unposted, apply_stock_in


def validate(doc, method=None):
    check_posted(doc)
    if not doc.doctypeid:
        doc.doctypeid = PURCHASE_OTHER_BILL
    validate_fiscal_period(doc.billdate)
    from millitrix.utils.child_table_helpers import strip_blank_child_rows

    strip_blank_child_rows(doc, "details", "Purchase Other Bill Detail")
    if not doc.details:
        frappe.throw(_("Add bill lines"))
    total = 0.0
    for line in doc.details or []:

        # P0-08 STOCK INTEGRATION
        if flt(line.quantity) > 0 and getattr(line, "itemcode", None):
                key = StockKey(
                        storeid=doc.location_id,
                        itemcode=line.itemcode,
                        bags_are="Our"
                )
                apply_stock_in(
                        key,
                        flt(line.quantity),
                        rate=flt(line.rate),
                        movement_date=doc.billdate
                )

        line.amount = round(flt(flt(line.quantity) * flt(line.rate)), 2)
        total += flt(line.amount)
    doc.amount = round(flt(total), 2)


def on_submit(doc, method=None):
    doc_key = resolve_document_key(doc, "pbillno")
    batch = DocTranBatch(doc.location_id, doc.doctypeid, doc_key)
    exp_acc = get_setting_account("Purchases OtherBill")
    party_acc = get_party_accid(doc.partyid)
    total = 0.0
    for line in doc.details or []:

        # P0-08 STOCK INTEGRATION
        if flt(line.quantity) > 0 and getattr(line, "itemcode", None):
                key = StockKey(
                        storeid=doc.location_id,
                        itemcode=line.itemcode,
                        bags_are="Our"
                )
                apply_stock_in(
                        key,
                        flt(line.quantity),
                        rate=flt(line.rate),
                        movement_date=doc.billdate
                )

        amt = flt(line.quantity) * flt(line.rate)
        total += amt
        batch.dr(exp_acc, amt, itemcode=line.itemcode, detail=f"Other bill {doc.pbillno}")
    batch.cr(party_acc, total, partyid=doc.partyid, detail=f"Purchase Other Bill {doc.pbillno}")
    doc.amount = total
    doc.db_set("amount", total)
    persist_doc_transactions(batch)
    generate_gl(
        location_id=doc.location_id,
        doctypeid=doc.doctypeid,
        documentid=doc_key,
        vouchdate=doc.billdate,
        narration=f"Purchase Other Bill {doc.pbillno}",
    )
    mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
