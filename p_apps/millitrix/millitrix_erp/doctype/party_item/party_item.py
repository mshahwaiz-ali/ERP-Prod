# Copyright (c) 2026, Millitrix and contributors

from frappe.model.document import Document

from millitrix.utils.brokery import validate_party_item_row


class PartyItem(Document):
	def validate(self):
		validate_party_item_row(self)
