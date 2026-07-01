# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class PartyReceiptVoucher(Document):
	def before_insert(self):
		assign_numeric_id(self, "cnbvno")

	def validate(self):
		from millitrix.finance.cnb_party_common import validate_cnb_party_doc
		validate_cnb_party_doc(
			self,
			doctype_id="Party Receipt Voucher",
			voucher_mode="Receipt",
			party_pcats=("13",),
		)

	def on_submit(self):
		from millitrix.finance.cnb_party_common import submit_cnb_party_doc

		submit_cnb_party_doc(self)

	def on_cancel(self):
		from millitrix.finance.unsubmit import on_cancel as unified_cancel

		return unified_cancel(self)