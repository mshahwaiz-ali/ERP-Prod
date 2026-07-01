# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class PayableDiscountNote(Document):
	def before_insert(self):
		assign_numeric_id(self, "pnrno")

	def validate(self):
		from millitrix.finance.pnr_discount_common import validate_pnr_discount_doc
		validate_pnr_discount_doc(
			self,
			doctype_id="Payable Discount Note",
			flow="payment",
			party_pcats=('12',),
		)

	def on_submit(self):
		from millitrix.finance.pnr_discount_common import submit_pnr_discount_doc

		submit_pnr_discount_doc(self, flow="payment")

	def on_cancel(self):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)