# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from millitrix.utils.invoice_fields import mundtype_code_from_value
from millitrix.utils.mund import default_bag_weight


class ItemPriceList(Document):
	def validate(self):
		if not self.location_id:
			from millitrix.utils.erpnext_compat import set_session_location

			set_session_location(self)
		if not self.location_id:
			frappe.throw(_("Location is required — set your mill/location in user settings"))

		if frappe.db.exists(
			"Item Price List",
			{
				"location_id": self.location_id,
				"itemcode": self.itemcode,
				"ipdate": self.ipdate,
				"name": ("!=", self.name),
			},
		):
			frappe.throw(
				"Item Price List already exists for this Location, Item and Date"
			)

		if self.itemcode and not frappe.db.exists("Item Setup", self.itemcode):
			frappe.throw(_("Item {0} not found in master setup").format(self.itemcode))

		if self.itemcode and not flt(self.bagweight):
			item_mund = frappe.db.get_value("Item Setup", self.itemcode, "mundtype")
			item_bag = frappe.db.get_value("Item Setup", self.itemcode, "bagweight")
			code = mundtype_code_from_value(item_mund)
			self.bagweight = flt(item_bag) or default_bag_weight(code)

		if flt(self.purchrate) < 0 or flt(self.salesrate) < 0:
			frappe.throw("Purchase Rate and Sales Rate cannot be negative")
