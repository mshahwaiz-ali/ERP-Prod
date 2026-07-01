# Copyright (c) 2026, Millitrix and contributors
# For license information, see license.txt

import frappe
from frappe.model.document import Document

from millitrix.utils.doctype_ids import GATE_PASS
from millitrix.utils.naming import assign_numeric_id


class InOutGatePass(Document):

	def before_insert(self):
		assign_numeric_id(self, "gatepassno")
		if not self.doctypeid:
			self.doctypeid = GATE_PASS
		if not self.doc_type:
			self.doc_type = "TSTK"
