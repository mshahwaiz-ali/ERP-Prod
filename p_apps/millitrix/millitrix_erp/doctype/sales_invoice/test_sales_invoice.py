# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt


class TestMillitrixSalesInvoice(IntegrationTestCase):
	def test_submitted_si_has_balanced_gl(self):
		if not frappe.db.exists("Sales Invoice", {"salesinvno": 10001, "docstatus": 1}):
			self.skipTest("Demo SI 10001 not seeded")
		rows = frappe.db.sql(
			"""
			SELECT SUM(vd.debit) AS dr, SUM(vd.credit) AS cr
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = 'Sales Invoice' AND mv.documentid = 10001
			""",
			as_dict=True,
		)[0]
		self.assertAlmostEqual(flt(rows.dr), flt(rows.cr), places=2)

	def test_bardana_brokery_si_gl(self):
		if not frappe.db.exists("Sales Invoice", {"salesinvno": 10003, "docstatus": 1}):
			self.skipTest("Audit SI 10003 not seeded — run audit_proofs")
		rows = frappe.db.sql(
			"""
			SELECT vd.debit, vd.credit, vd.detail
			FROM `tabVoucher Transaction` mv
			INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
			WHERE mv.docstatus = 1 AND mv.doctypeid = 'Sales Invoice' AND mv.documentid = 10003
			""",
			as_dict=True,
		)
		total_dr = sum(flt(r.debit) for r in rows)
		total_cr = sum(flt(r.credit) for r in rows)
		self.assertAlmostEqual(total_dr, total_cr, places=2)
		self.assertTrue(any("Bardana" in (r.detail or "") for r in rows))
