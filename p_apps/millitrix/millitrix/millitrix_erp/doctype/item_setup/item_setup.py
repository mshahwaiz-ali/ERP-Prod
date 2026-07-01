# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from millitrix.utils.invoice_fields import mundtype_code_from_value
from millitrix.utils.mund import default_bag_weight
from millitrix.utils.naming import assign_numeric_id, clear_duplicate_autoname


class ItemSetup(Document):
	def before_insert(self):
		clear_duplicate_autoname(self, "itemcode")
		if not self.itemcode:
			assign_numeric_id(self, "itemcode")

	def validate(self):
		if self.iclassid and not frappe.db.exists("Item Class", self.iclassid):
			frappe.throw(f"Item Class {self.iclassid} not found in master setup")

		code = mundtype_code_from_value(self.mundtype)
		if code not in ("N", "O", "Q"):
			frappe.throw("Mund Type must be New Mund, Old Mund, or Quantity")

		if not flt(self.bagweight):
			self.bagweight = default_bag_weight(code)

		if flt(self.bagweight) <= 0:
			frappe.throw("Bag Weight must be greater than zero")
