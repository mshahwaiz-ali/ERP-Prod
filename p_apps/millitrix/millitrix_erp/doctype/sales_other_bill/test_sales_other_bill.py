# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt


class TestSalesOtherBill(FrappeTestCase):
	def test_sob_10001_balanced_gl(self):
		if not frappe.db.exists("Sales Other Bill", {"sbillno": 10001, "docstatus": 1}):
			self.skipTest("SOB 10001 not seeded — run seed_v4_demo")
		rows = frappe.db.sql(
			"""
			SELECT SUM(vd.debit) AS dr, SUM(vd.credit) AS cr
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = 'Sales Other Bill' AND mv.documentid = 10001
			""",
			as_dict=True,
		)[0]
		self.assertAlmostEqual(flt(rows.dr), flt(rows.cr), places=2)
