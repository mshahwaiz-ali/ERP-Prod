# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt


class TestMillitrixAdvanceAdjustment(FrappeTestCase):
	def test_advance_adjustment_10001_balanced(self):
		if not frappe.db.exists("Advance Adjustment", {"adjid": 10001, "docstatus": 1}):
			self.skipTest("Advance Adjustment 10001 not seeded — run seed_v4_demo")
		doctypeid = frappe.db.get_value("Advance Adjustment", {"adjid": 10001}, "doctypeid")
		rows = frappe.db.sql(
			"""SELECT SUM(vd.debit) AS dr, SUM(vd.credit) AS cr
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = %s AND mv.documentid = 10001""",
			(doctypeid,),
			as_dict=True,
		)[0]
		self.assertAlmostEqual(flt(rows.dr), flt(rows.cr), places=2)
