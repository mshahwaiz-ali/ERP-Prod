# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt


class TestMillitrixAccountsOpening(FrappeTestCase):
	def test_gl_opening_submitted_balanced(self):
		submitted = frappe.db.get_all(
			"Accounts Opening",
			filters={"docstatus": 1},
			fields=["glopenid"],
			limit=1,
		)
		if not submitted:
			self.skipTest("No submitted Accounts Opening — run seed_v4_demo")
		doc_key = str(submitted[0].glopenid)
		rows = frappe.db.sql(
			"""
			SELECT SUM(vd.debit) AS dr, SUM(vd.credit) AS cr
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = 'Accounts Opening' AND mv.documentid = %s
			""",
			doc_key,
			as_dict=True,
		)[0]
		self.assertAlmostEqual(flt(rows.dr), flt(rows.cr), places=2)
