# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id


class StoreSetup(Document):
	def before_insert(self):
		assign_numeric_id(self, "storeid")

	def validate(self):
		if self.parentid and self.parentid == self.name:
			frappe.throw("Store cannot be its own Parent Store")
		if self.location_id and not frappe.db.exists("Location", self.location_id):
			frappe.throw(f"Location {self.location_id} not found in master setup")
		if self.storetypeid and not frappe.db.exists("Store Types", self.storetypeid):
			frappe.throw(f"Store Type {self.storetypeid} not found in master setup")
		if self.parentid:
			parent_location = frappe.db.get_value(
				"Store Setup", self.parentid, "location_id"
			)
			if parent_location and parent_location != self.location_id:
				frappe.throw("Parent Store must belong to the same Location")
