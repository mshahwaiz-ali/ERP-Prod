# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt


class TestClosingStock(FrappeTestCase):
	def test_closing_10001_gl_balanced(self):
		if not frappe.db.exists("Closing Stock", {"sopenid": 10001, "docstatus": 1}):
			self.skipTest("Closing Stock 10001 not seeded — run complete_setup")
		rows = frappe.db.sql(
			"""
			SELECT SUM(vd.debit) AS dr, SUM(vd.credit) AS cr
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = 'Closing Stock' AND mv.documentid = 10001
			""",
			as_dict=True,
		)[0]
		self.assertAlmostEqual(flt(rows.dr), flt(rows.cr), places=2)
