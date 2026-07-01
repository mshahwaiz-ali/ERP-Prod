# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.finance.advance_common import advance_flow_key, validate_advance_doc
from millitrix.utils.naming import assign_numeric_id


class AdvancePNR(Document):
	def before_insert(self):
		if not self.pnrdate:
			self.pnrdate = frappe.utils.today()
		assign_numeric_id(self, "pnrno")
		if self.amount and not self.balance:
			self.balance = self.amount

	def validate(self):
		validate_advance_doc(self, flow=advance_flow_key(self.advance_flow))

	def on_submit(self):
		from millitrix.finance.advance_common import submit_advance_doc

		submit_advance_doc(self, flow=advance_flow_key(self.advance_flow))

	def on_cancel(self):
		from millitrix.finance.unsubmit import on_cancel as unified_cancel

		return unified_cancel(self)