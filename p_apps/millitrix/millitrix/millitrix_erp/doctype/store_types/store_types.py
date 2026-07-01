# Copyright (c) 2026, Millitrix and contributors

from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class StoreTypes(Document):
	def before_insert(self):
		assign_numeric_id(self, "storetypeid")
