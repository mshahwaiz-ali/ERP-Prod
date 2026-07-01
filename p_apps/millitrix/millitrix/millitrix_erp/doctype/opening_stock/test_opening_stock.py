# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt


class TestOpeningStock(IntegrationTestCase):
	def test_opening_10001_gl_balanced(self):
		if not frappe.db.exists("Opening Stock", {"sopenid": 10001, "docstatus": 1}):
			self.skipTest("Opening Stock 10001 not seeded — run complete_setup")
		rows = frappe.db.sql(
			"""
			SELECT SUM(vd.debit) AS dr, SUM(vd.credit) AS cr
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = 'Opening Stock' AND mv.documentid = 10001
			""",
			as_dict=True,
		)[0]
		self.assertAlmostEqual(flt(rows.dr), flt(rows.cr), places=2)
		dt = frappe.db.count("Document Transaction", {"doctypeid": "Opening Stock", "documentid": 10001})
		self.assertGreater(dt, 0)
