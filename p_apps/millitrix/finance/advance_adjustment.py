# Copyright (c) 2026, Millitrix and contributors
# Blueprint 9.19 — RAA / PAA advance knockoff (legacy combined doctype)

from __future__ import annotations

import frappe
from frappe import _

from millitrix.finance.advance_adjustment_common import (
	cancel_adjustment_doc,
	submit_adjustment_doc,
	validate_adjustment_doc,
)
from millitrix.utils.doctype_ids import (
	ADVANCE_PNR,
	PAID_ADVANCE_ADJUSTMENT,
	PURCHASE_INVOICE,
	PURCHASE_OTHER_BILL,
	RECEIVED_ADVANCE_ADJUSTMENT,
	SALES_INVOICE,
	SALES_OTHER_BILL,
)

_RECEIPT_INVOICES = frozenset({SALES_INVOICE, SALES_OTHER_BILL})
_PAYMENT_INVOICES = frozenset({PURCHASE_INVOICE, PURCHASE_OTHER_BILL})


def validate(doc, method=None):
	_infer_adjustment_type(doc)
	flow, doctype_id, party_pcats = _resolve_legacy_flow(doc)
	validate_adjustment_doc(
		doc,
		doctype_id=doctype_id,
		flow=flow,
		party_pcats=party_pcats,
		advance_doctype=ADVANCE_PNR,
	)


def on_submit(doc, method=None):
	flow = _adjustment_flow(doc.invoice_lines)
	submit_adjustment_doc(doc, flow=flow)


def on_cancel(doc, method=None):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _infer_adjustment_type(doc) -> None:
	if doc.doctypeid in (RECEIVED_ADVANCE_ADJUSTMENT, PAID_ADVANCE_ADJUSTMENT):
		return
	flow = _adjustment_flow(doc.invoice_lines)
	doc.doctypeid = RECEIVED_ADVANCE_ADJUSTMENT if flow == "receipt" else PAID_ADVANCE_ADJUSTMENT


def _adjustment_flow(invoice_lines) -> str:
	modes: set[str] = set()
	for line in invoice_lines or []:
		if line.doctypeid in _RECEIPT_INVOICES:
			modes.add("receipt")
		elif line.doctypeid in _PAYMENT_INVOICES:
			modes.add("payment")
		else:
			frappe.throw(_("Unsupported invoice type {0}").format(line.doctypeid))
	if len(modes) != 1:
		frappe.throw(_("Cannot mix customer and supplier invoices in one adjustment"))
	return modes.pop()


def _resolve_legacy_flow(doc) -> tuple[str, str, tuple[str, ...]]:
	flow = _adjustment_flow(doc.invoice_lines)
	if flow == "receipt":
		return flow, RECEIVED_ADVANCE_ADJUSTMENT, ("13",)
	return flow, PAID_ADVANCE_ADJUSTMENT, ("12",)
