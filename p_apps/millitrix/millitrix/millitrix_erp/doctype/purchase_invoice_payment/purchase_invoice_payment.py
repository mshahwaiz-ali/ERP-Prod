# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class PurchaseInvoicePayment(Document):
	def before_insert(self):
		assign_numeric_id(self, "pnrno")

	def validate(self):
		from millitrix.finance.pnr_invoice_common import validate_pnr_invoice_doc
		validate_pnr_invoice_doc(
			self,
			doctype_id="Purchase Invoice Payment",
			flow="payment",
			party_pcats=('12',),
			allowed_doctypes=frozenset({"Purchase Invoice", "Purchase Other Bill"}),
		)

	def on_submit(self):
		from millitrix.finance.pnr_invoice_common import submit_pnr_invoice_doc

		submit_pnr_invoice_doc(self, flow="payment")

	def on_cancel(self):
		from millitrix.finance.pnr_invoice_common import cancel_pnr_invoice_doc

		cancel_pnr_invoice_doc(self)
