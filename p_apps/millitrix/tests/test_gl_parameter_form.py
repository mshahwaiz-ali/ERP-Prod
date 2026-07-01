# Copyright (c) 2026, Millitrix and contributors

import unittest

from millitrix.utils.gl_parameter_form import (
	build_report_filters,
	list_gl_para_reports,
	validate_gl_para_execute,
)


class TestGLParameterForm(unittest.TestCase):
	def test_gl_para_reports_resolve(self):
		reports = list_gl_para_reports()
		self.assertGreater(len(reports), 8)
		legacy = {row["legacy"] for row in reports}
		self.assertIn("AccLedger", legacy)
		self.assertIn("Trial_Balance", legacy)
		self.assertIn("PartyBalance", legacy)

	def test_voucher_filter_mode(self):
		filters = build_report_filters(
			{
				"location_id": "LOC-1",
				"filter_mode": "voucherno",
				"from_voucherno": "100",
				"to_voucherno": "200",
			}
		)
		self.assertEqual(filters.get("from_voucherno"), "100")
		self.assertEqual(filters.get("to_voucherno"), "200")

	def test_accledger_requires_account(self):
		with self.assertRaises(Exception):
			validate_gl_para_execute(
				{
					"location_id": "LOC-1",
					"filter_mode": "date",
					"from_date": "2026-01-01",
					"to_date": "2026-06-01",
					"selected_report": "AccLedger",
				}
			)
