# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class AdvancePayment(Document):
	def before_insert(self):
		if not self.pnrdate:
			self.pnrdate = frappe.utils.today()
		assign_numeric_id(self, "pnrno")
		if self.amount and not self.balance:
			self.balance = self.amount

	def validate(self):
		from millitrix.finance.advance_common import validate_advance_doc
		validate_advance_doc(self, flow="payment")

	def on_submit(self):
		from millitrix.finance.advance_common import submit_advance_doc

		submit_advance_doc(self, flow="payment")

	def on_cancel(self):
		from millitrix.finance.advance_common import cancel_advance_doc

		cancel_advance_doc(self)
