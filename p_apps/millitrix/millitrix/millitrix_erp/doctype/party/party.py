# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document

from millitrix.utils.brokery import validate_party_item_row, validate_unique_party_items
from millitrix.utils.party import get_next_party_id, validate_party_id_for_category


class Party(Document):
	def before_insert(self):
		from millitrix.utils.naming import clear_duplicate_autoname

		clear_duplicate_autoname(self, "partyid")
		if not self.partyid:
			if not self.pcat_id:
				frappe.throw("Party Category is required before saving Party")
			self.partyid = get_next_party_id(self.pcat_id)

	def validate(self):
		if not self.pcat_id:
			frappe.throw("Party Category is required")

		if self.partyid:
			validate_party_id_for_category(self.partyid, self.pcat_id)

		validate_unique_party_items(self.party_items)
		for row in self.party_items or []:
			validate_party_item_row(row)
