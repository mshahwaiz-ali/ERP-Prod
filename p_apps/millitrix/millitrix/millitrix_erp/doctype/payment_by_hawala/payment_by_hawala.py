# Copyright (c) 2026, Millitrix and contributors
# For license information, see license.txt

import frappe
from frappe.model.document import Document

from millitrix.utils.naming import assign_numeric_id

_CREDIT_LINE_FIELDS = (
	"partyid",
	"itemcode",
	"accid",
	"gmmode",
	"referno",
	"referdate",
	"amount",
	"narration",
)


class PaymentByHawala(Document):

	def before_insert(self):
		assign_numeric_id(self, "gmid", date_field="gmdate")

	def onload(self):
		self._sync_party_b_line_to_credit_fields()

	def before_validate(self):
		self._sync_credit_fields_to_party_b_line()

	def _credit_field(self, line_field: str) -> str:
		return f"b_{line_field}"

	def _sync_party_b_line_to_credit_fields(self):
		line = (self.party_b_lines or [None])[0]
		if not line:
			return
		for field in _CREDIT_LINE_FIELDS:
			credit_field = self._credit_field(field)
			if not self.get(credit_field) and line.get(field) not in (None, ""):
				self.set(credit_field, line.get(field))

	def _sync_credit_fields_to_party_b_line(self):
		line_data = {
			field: self.get(self._credit_field(field))
			for field in _CREDIT_LINE_FIELDS
		}
		line_data["gmmode"] = line_data.get("gmmode") or "GL Code"
		if not any(line_data.get(field) for field in _CREDIT_LINE_FIELDS):
			return
		if not self.party_b_lines:
			self.append("party_b_lines", line_data)
			return
		row = self.party_b_lines[0]
		for field, value in line_data.items():
			row.set(field, value)
		while len(self.party_b_lines) > 1:
			self.remove(self.party_b_lines[-1])
