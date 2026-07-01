# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from millitrix.api.permissions import require_permission


class GLStatements(Document):
	def before_insert(self):
		from millitrix.utils.naming import assign_numeric_id

		assign_numeric_id(self, "statementid")

	def validate(self):
		self._assign_sub_statement_ids()
		self._normalize_operations()
		self._validate_gl_links()
		from millitrix.utils.list_view_summary import sync_list_summary_fields

		sync_list_summary_fields(self)

	def _assign_sub_statement_ids(self):
		seq = 0
		for row in self.sub_statements or []:
			seq += 1
			if not row.sub_statementid:
				row.sub_statementid = f"{self.statementid}-{seq}"

	def _normalize_operations(self):
		for row in self.sub_statements or []:
			row.operation = _normalize_operation(row.operation)
		self.operation = _normalize_operation(self.operation)

	def _validate_gl_links(self):
		sub_names = {row.name for row in (self.sub_statements or []) if row.name}
		for row in self.gl_accounts or []:
			if row.sub_statement_ref and row.sub_statement_ref not in sub_names:
				frappe.throw(
					_("GL Code row is linked to a statement line that no longer exists. Refresh and save again.")
				)


def _normalize_operation(value: str | None) -> str:
	if value in ("+", "Add"):
		return "Add"
	if value in ("-", "Subtract"):
		return "Subtract"
	return value or "Add"


@frappe.whitelist()
def get_accounts_by_type(statement_type: str | None = None):
	"""Oracle GET_GL — level-5 accounts for the selected statement line Type (nature)."""
	require_permission("Chart of Accounting", "read")
	if not statement_type:
		frappe.throw(_("Type is required on the statement line."))

	return frappe.get_all(
		"Chart of Accounting",
		filters={"chartlevel": 5, "nature": statement_type, "transflag": "Yes"},
		fields=["name", "description"],
		order_by="name asc",
	)
