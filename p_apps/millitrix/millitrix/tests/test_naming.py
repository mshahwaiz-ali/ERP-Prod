# Copyright (c) 2026, Millitrix and contributors

import unittest
from unittest.mock import patch

from millitrix.utils.naming import (
	DOCTYPE_PREFIX,
	get_next_prefixed_no,
	resolve_doctype_prefix,
)


class TestNaming(unittest.TestCase):
	def test_all_transaction_doctypes_have_prefix(self):
		required = (
			"Purchase Invoice",
			"Sales Invoice",
			"Purchase Order",
			"Voucher Transaction",
			"Advance Payment",
		)
		for dt in required:
			self.assertIn(dt, DOCTYPE_PREFIX)

	def test_prefixed_format_four_digits(self):
		with patch("millitrix.utils.naming.frappe") as mock_frappe:
			mock_frappe.get_meta.return_value.has_field.return_value = False
			mock_frappe.db.sql.return_value = []
			value = get_next_prefixed_no(
				"Purchase Invoice",
				"purchinvno",
				"PI",
				"2026-06-19",
			)
		self.assertEqual(value, "PI-2606-0001")

	def test_prefixed_increments_sequence(self):
		with patch("millitrix.utils.naming.frappe") as mock_frappe:
			mock_frappe.get_meta.return_value.has_field.return_value = False
			mock_frappe.db.sql.return_value = [("PI-2606-0003",)]
			value = get_next_prefixed_no(
				"Purchase Invoice",
				"purchinvno",
				"PI",
				"2026-06-19",
			)
		self.assertEqual(value, "PI-2606-0004")

	def test_chart_of_accounting_excluded(self):
		doc = type("Doc", (), {"doctype": "Chart of Accounting"})()
		self.assertIsNone(resolve_doctype_prefix(doc))

	def test_advance_receipt_prefix(self):
		doc = type("Doc", (), {"doctype": "Advance Receipt", "get": lambda _s, k: None})()
		self.assertEqual(resolve_doctype_prefix(doc), "AR")
