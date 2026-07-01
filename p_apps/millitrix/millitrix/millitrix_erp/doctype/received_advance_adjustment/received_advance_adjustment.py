# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class ReceivedAdvanceAdjustment(Document):
	def before_insert(self):
		assign_numeric_id(self, "adjid")

	def validate(self):
		from millitrix.finance.advance_adjustment_common import validate_adjustment_doc
		from millitrix.utils.doctype_ids import ADVANCE_PNR
		validate_adjustment_doc(
			self,
			doctype_id="Received Advance Adjustment",
			flow="receipt",
			party_pcats=('13',),
			advance_doctype=ADVANCE_PNR,
		)

	def on_submit(self):
		from millitrix.finance.advance_adjustment_common import submit_adjustment_doc

		submit_adjustment_doc(self, flow="receipt")

	def on_cancel(self):
		from millitrix.finance.advance_adjustment_common import cancel_adjustment_doc

		cancel_adjustment_doc(self)
