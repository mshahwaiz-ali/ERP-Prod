# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.tests.utils import FrappeTestCase

from millitrix.finance.unsubmit import SUPPORTED_UNSUBMIT_DOCTYPES, resolve_target_doctype
from millitrix.utils.document_display import id_field_for, resolve_document_name


class TestDocumentDisplay(FrappeTestCase):
	def test_resolve_document_name_by_prefixed_id(self):
		pi = frappe.db.get_value(
			"Purchase Invoice",
			{"purchinvno": ["is", "set"], "docstatus": ["<", 2]},
			["name", "purchinvno"],
			as_dict=True,
		)
		if not pi:
			self.skipTest("No Purchase Invoice in site")
		resolved = resolve_document_name("Purchase Invoice", pi.purchinvno)
		self.assertEqual(resolved, pi.name)

	def test_resolve_document_name_by_frappe_name(self):
		pi = frappe.db.get_value("Purchase Invoice", {}, "name")
		if not pi:
			self.skipTest("No Purchase Invoice in site")
		self.assertEqual(resolve_document_name("Purchase Invoice", pi), pi)

	def test_resolve_document_name_missing(self):
		self.assertIsNone(resolve_document_name("Purchase Invoice", "PI-9999-999"))

	def test_unsubmit_supported_doctypes_have_id_field(self):
		missing = [dt for dt in SUPPORTED_UNSUBMIT_DOCTYPES if not id_field_for(dt)]
		self.assertEqual(missing, [])

	def test_unsubmit_resolves_prefixed_document(self):
		for doctype in ("Purchase Invoice", "Sales Invoice", "Voucher Transaction"):
			if doctype not in SUPPORTED_UNSUBMIT_DOCTYPES:
				continue
			id_field = id_field_for(doctype)
			row = frappe.db.get_value(
				doctype,
				{id_field: ["is", "set"]},
				["name", id_field],
				as_dict=True,
			)
			if not row:
				continue
			self.assertEqual(resolve_document_name(doctype, row[id_field]), row.name)
			return
		self.skipTest("No transaction docs with prefixed ids")

	def test_resolve_target_doctype_from_module(self):
		module = frappe.db.get_value(
			"Module",
			{"doctypeid": ["in", list(SUPPORTED_UNSUBMIT_DOCTYPES)], "moduletype": "F"},
			"name",
		)
		if not module:
			self.skipTest("No Module row for unsubmit doctypes")
		doc = frappe._dict(usdoctype=module)
		target = resolve_target_doctype(doc)
		self.assertIn(target, SUPPORTED_UNSUBMIT_DOCTYPES)

	def test_resolve_target_doctype_legacy_doctype_name(self):
		doc = frappe._dict(usdoctype="Purchase Invoice")
		self.assertEqual(resolve_target_doctype(doc), "Purchase Invoice")
