# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class BrokerInvoicePayment(Document):
	def before_insert(self):
		if not self.pnrdate:
			self.pnrdate = frappe.utils.today()
		assign_numeric_id(self, "pnrno")

	def validate(self):
		from millitrix.finance.pnr_invoice_common import validate_pnr_invoice_doc
		validate_pnr_invoice_doc(
			self,
			doctype_id="Broker Invoice Payment",
			flow="payment",
			party_pcats=('11',),
			allowed_doctypes=frozenset({"Purchase Invoice", "Sales Invoice"}),
		)

	def on_submit(self):
		from millitrix.finance.pnr_invoice_common import submit_pnr_invoice_doc

		submit_pnr_invoice_doc(self, flow="payment")

	def on_cancel(self):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)