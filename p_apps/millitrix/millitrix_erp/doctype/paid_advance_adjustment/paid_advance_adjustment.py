# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class PaidAdvanceAdjustment(Document):
	def before_insert(self):
		assign_numeric_id(self, "adjid")

	def validate(self):
		from millitrix.finance.advance_adjustment_common import validate_adjustment_doc
		from millitrix.utils.doctype_ids import ADVANCE_PNR
		validate_adjustment_doc(
			self,
			doctype_id="Paid Advance Adjustment",
			flow="payment",
			party_pcats=('12',),
			advance_doctype=ADVANCE_PNR,
		)

	def on_submit(self):
		from millitrix.finance.advance_adjustment_common import submit_adjustment_doc

		submit_adjustment_doc(self, flow="payment")

	def on_cancel(self):
    # DISABLED: routed to finance/unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)