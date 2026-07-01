# Copyright (c) 2026, Millitrix and contributors

import unittest

from millitrix.utils.para_form_launcher import (
	build_para_report_filters,
	get_para_form_spec,
	list_para_reports,
)


class TestParaFormLauncher(unittest.TestCase):
	def test_purchase_reports_resolve(self):
		spec = get_para_form_spec("purchase")
		reports = list_para_reports(spec)
		self.assertGreater(len(reports), 10)
		self.assertTrue(all(row.get("report_name") for row in reports))

	def test_posted_filter_all_sets_include_consider(self):
		filters = build_para_report_filters(
			"purchase",
			{
				"location_id": "LOC-1",
				"from_date": "2026-01-01",
				"to_date": "2026-06-01",
				"posted_filter": "All",
				"supplierid": "SUP-1",
			},
		)
		self.assertEqual(filters.get("include_consider"), 1)
		self.assertEqual(filters.get("partyid"), "SUP-1")

	def test_purchase_condition_fields_include_oracle_extras(self):
		spec = get_para_form_spec("purchase")
		for field in ("iclassid", "truckno", "report_by", "order_status", "p_days"):
			self.assertIn(field, spec.condition_fields)
		legacy = {row["legacy"] for row in list_para_reports(spec)}
		self.assertIn("Party_Info", legacy)

	def test_report_by_and_p_days_pass_through(self):
		filters = build_para_report_filters(
			"purchase",
			{
				"location_id": "LOC-1",
				"from_date": "2026-01-01",
				"to_date": "2026-06-01",
				"report_by": "Invoice No",
				"truckno": "ABC-123",
				"p_days": 30,
				"order_status": "In Progress",
			},
		)
		self.assertEqual(filters.get("report_by"), "Inv")
		self.assertEqual(filters.get("truckno"), "ABC-123")
		self.assertEqual(filters.get("p_days"), 30)
		self.assertEqual(filters.get("order_status"), "In Progress")

	def test_sales_condition_fields_include_oracle_extras(self):
		spec = get_para_form_spec("sales")
		for field in ("iclassid", "truckno", "report_by", "order_status", "p_days"):
			self.assertIn(field, spec.condition_fields)
		legacy = {row["legacy"] for row in list_para_reports(spec)}
		self.assertIn("Party_Info", legacy)

	def test_sales_report_by_so_maps_to_oracle_po(self):
		filters = build_para_report_filters(
			"sales",
			{
				"location_id": "LOC-1",
				"from_date": "2026-01-01",
				"to_date": "2026-06-01",
				"report_by": "SO No",
				"from_sonumber": 100,
				"to_sonumber": 200,
			},
		)
		self.assertEqual(filters.get("report_by"), "PO")
		self.assertEqual(filters.get("from_sonumber"), 100)

	def test_all_six_forms_defined(self):
		for key in ("purchase", "sales", "stock", "financial", "payable", "receivable"):
			spec = get_para_form_spec(key)
			self.assertEqual(spec.key, key)
			self.assertGreater(len(spec.report_legacy_ids), 0)

	def test_financial_condition_fields_include_oracle_extras(self):
		spec = get_para_form_spec("financial")
		for field in ("partyid", "accid", "coa_level", "report_by", "from_svouch", "to_svouch"):
			self.assertIn(field, spec.condition_fields)
		legacy = {row["legacy"] for row in list_para_reports(spec)}
		self.assertIn("AccLedger", legacy)
		self.assertIn("PartyBalance", legacy)

	def test_financial_report_by_svouch_passes_through(self):
		filters = build_para_report_filters(
			"financial",
			{
				"location_id": "LOC-1",
				"from_date": "2026-01-01",
				"to_date": "2026-06-01",
				"report_by": "Submit Voucher No",
				"from_svouch": 100,
				"to_svouch": 200,
				"coa_level": 3,
			},
		)
		self.assertEqual(filters.get("report_by"), "SVCH")
		self.assertEqual(filters.get("from_svouch"), 100)
		self.assertEqual(filters.get("to_svouch"), 200)
		self.assertEqual(filters.get("chartlevel"), 3)

	def test_payable_condition_fields_include_oracle_extras(self):
		spec = get_para_form_spec("payable")
		for field in (
			"report_by",
			"supplierid",
			"brokerid",
			"itemcode",
			"truckno",
			"p_days",
			"from_purchinvno",
			"to_purchinvno",
		):
			self.assertIn(field, spec.condition_fields)
		legacy = {row["legacy"] for row in list_para_reports(spec)}
		self.assertIn("PIOutstanding", legacy)

	def test_payable_report_by_and_supplier_pass_through(self):
		filters = build_para_report_filters(
			"payable",
			{
				"location_id": "LOC-1",
				"from_date": "2026-01-01",
				"to_date": "2026-06-01",
				"report_by": "Invoice No",
				"supplierid": "SUP-1",
				"brokerid": "BRK-1",
				"truckno": "TRK-99",
				"p_days": 15,
				"from_purchinvno": 100,
				"to_purchinvno": 200,
			},
		)
		self.assertEqual(filters.get("report_by"), "Inv")
		self.assertEqual(filters.get("partyid"), "SUP-1")
		self.assertEqual(filters.get("brokerid"), "BRK-1")
		self.assertEqual(filters.get("truckno"), "TRK-99")
		self.assertEqual(filters.get("p_days"), 15)
		self.assertEqual(filters.get("from_purchinvno"), 100)

	def test_receivable_condition_fields_include_oracle_extras(self):
		spec = get_para_form_spec("receivable")
		for field in (
			"report_by",
			"customerid",
			"brokerid",
			"itemcode",
			"truckno",
			"p_days",
			"from_salesinvno",
			"to_salesinvno",
		):
			self.assertIn(field, spec.condition_fields)
		legacy = {row["legacy"] for row in list_para_reports(spec)}
		self.assertIn("SalesInvReceipt", legacy)

	def test_receivable_report_by_and_customer_pass_through(self):
		filters = build_para_report_filters(
			"receivable",
			{
				"location_id": "LOC-1",
				"from_date": "2026-01-01",
				"to_date": "2026-06-01",
				"report_by": "Invoice No",
				"customerid": "CUST-1",
				"brokerid": "BRK-1",
				"truckno": "TRK-99",
				"p_days": 15,
				"from_salesinvno": 100,
				"to_salesinvno": 200,
			},
		)
		self.assertEqual(filters.get("report_by"), "Inv")
		self.assertEqual(filters.get("partyid"), "CUST-1")
		self.assertEqual(filters.get("brokerid"), "BRK-1")
		self.assertEqual(filters.get("truckno"), "TRK-99")
		self.assertEqual(filters.get("p_days"), 15)
		self.assertEqual(filters.get("from_salesinvno"), 100)
