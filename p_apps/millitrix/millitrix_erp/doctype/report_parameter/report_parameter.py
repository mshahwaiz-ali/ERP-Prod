# Copyright (c) 2026, Millitrix and contributors
# Oracle REPORT_PARA — last-used report filter cache per user / location / module.

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from millitrix.utils.naming import assign_numeric_id


class ReportParameter(Document):

	def before_insert(self):
		assign_numeric_id(self, "paraid")

	def validate(self):
		if self.from_date and self.to_date and getdate(self.from_date) > getdate(self.to_date):
			frappe.throw(_("From Date cannot be after To Date"))
