# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt


class TestMillitrixStockTransferNote(FrappeTestCase):
	def test_transfer_cartage_gl_balanced(self):
		if not frappe.db.exists("Stock Transfer Note", {"transferno": 10002, "docstatus": 1}):
			self.skipTest("Demo transfer 10002 not seeded — run seed_v4_demo")
		rows = frappe.db.sql(
			"""
			SELECT SUM(vd.debit) AS dr, SUM(vd.credit) AS cr
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = 'Stock Transfer Note' AND mv.documentid = 10002
			""",
			as_dict=True,
		)[0]
		self.assertAlmostEqual(flt(rows.dr), flt(rows.cr), places=2)
		self.assertGreater(flt(rows.dr), 0)
