# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class ReceiptVoucher(Document):
	def before_insert(self):
		assign_numeric_id(self, "cnbvno")

	def validate(self):
		from millitrix.finance.cnb_general_common import validate_cnb_general_doc
		validate_cnb_general_doc(
			self,
			doctype_id="Receipt Voucher",
			voucher_mode="Receipt",
		)

	def on_submit(self):
		from millitrix.finance.cnb_general_common import submit_cnb_general_doc

		submit_cnb_general_doc(self)

	def on_cancel(self):
		from millitrix.finance.cnb_general_common import cancel_cnb_general_doc

		cancel_cnb_general_doc(self)
