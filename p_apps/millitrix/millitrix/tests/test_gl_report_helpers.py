# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import unittest

from millitrix.utils.gl_reports import format_balance_side, split_balance


class TestGlReportHelpers(unittest.TestCase):
	def test_split_balance_positive(self):
		self.assertEqual(split_balance(100), (100.0, 0.0))

	def test_split_balance_negative(self):
		self.assertEqual(split_balance(-50), (0.0, 50.0))

	def test_format_balance_side_asset(self):
		self.assertEqual(format_balance_side(100, "Assets"), "Dr")
		self.assertEqual(format_balance_side(-100, "Assets"), "Cr")

	def test_format_balance_side_liability(self):
		self.assertEqual(format_balance_side(100, "Liabilities"), "Cr")
		self.assertEqual(format_balance_side(-100, "Liabilities"), "Dr")

	def test_format_balance_side_zero(self):
		self.assertEqual(format_balance_side(0, "Assets"), "")
