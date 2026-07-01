# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt


class TestMillitrixPurchaseInvoice(IntegrationTestCase):
	def test_submitted_pi_has_balanced_gl(self):
		if not frappe.db.exists("Purchase Invoice", {"purchinvno": 10001, "docstatus": 1}):
			self.skipTest("Demo PI 10001 not seeded")
		rows = frappe.db.sql(
			"""
			SELECT SUM(vd.debit) AS dr, SUM(vd.credit) AS cr
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = 'Purchase Invoice' AND mv.documentid = 10001
			""",
			as_dict=True,
		)[0]
		self.assertAlmostEqual(flt(rows.dr), flt(rows.cr), places=2)

	def test_brokery_dr_supplier_pi_balanced(self):
		if not frappe.db.exists("Purchase Invoice", {"purchinvno": 10007, "docstatus": 1}):
			self.skipTest("Audit PI 10007 not seeded — run audit_proofs")
		rows = frappe.db.sql(
			"""
			SELECT SUM(vd.debit) AS dr, SUM(vd.credit) AS cr
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = 'Purchase Invoice' AND mv.documentid = 10007
			""",
			as_dict=True,
		)[0]
		self.assertAlmostEqual(flt(rows.dr), flt(rows.cr), places=2)
