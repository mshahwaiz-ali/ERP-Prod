# Copyright (c) 2026, Millitrix and contributors

import unittest

import frappe

from millitrix.api.coa_setup import _cascade_nature


class TestCoaSetup(unittest.TestCase):
	def test_cascade_nature_updates_descendants(self):
		if not frappe.db.table_exists("tabChart of Accounting"):
			self.skipTest("Chart of Accounting not installed")

		l1 = frappe.get_doc(
			{
				"doctype": "Chart of Accounting",
				"description": "Test Assets Root",
				"nature": "Assets",
				"chartlevel": 1,
				"transflag": "No",
			}
		).insert(ignore_permissions=True)

		l2 = frappe.get_doc(
			{
				"doctype": "Chart of Accounting",
				"description": "Test Current Assets",
				"nature": "Assets",
				"chartlevel": 2,
				"parentid": l1.name,
				"transflag": "No",
			}
		).insert(ignore_permissions=True)

		_cascade_nature(l1.name, "Liabilities")
		self.assertEqual(
			frappe.db.get_value("Chart of Accounting", l2.name, "nature"),
			"Liabilities",
		)

		frappe.delete_doc("Chart of Accounting", l2.name, force=1, ignore_permissions=True)
		frappe.delete_doc("Chart of Accounting", l1.name, force=1, ignore_permissions=True)
