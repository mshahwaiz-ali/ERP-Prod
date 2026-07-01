# Copyright (c) 2026, Millitrix and contributors
# Oracle formula parity — invoice_calc + production_calc

import unittest

from frappe.utils import flt

from millitrix.utils.invoice_calc import calc_bagamnt, calc_line_totals, recalc_invoice_header
from millitrix.utils.production_calc import (
	input_total_weight,
	prod_1_qty,
	prod_2_qty,
	recalc_input_line,
	ref_bags_qty,
	ref_weight_qty,
)


class _Line:
	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)

	def __getattr__(self, name):
		return 0


class _Header:
	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)


class TestInvoiceCalcOracleParity(unittest.TestCase):
	def test_mund_line_total_excludes_broker_and_labour(self):
		header = _Header(
			doctype="Sales Invoice",
			kantatype="Total Weight",
			amntby="Mund",
			mundtype="N",
			brokery="Unpaid",
			borrow="Delivery",
		)
		line = _Line(
			truckqty=1000,
			delikanta=1000,
			lessweight=0,
			bagqty=10,
			bagrate=50,
			bags_are="SA",
			rate=5000,
			discount=100,
			labouramnt=200,
			brokeramnt=999,
		)
		calc = calc_line_totals(line, header, is_purchase=False)
		# mund = 1000/40 = 25; base = 25*5000 = 125000; bagamnt = 500; total = 125400
		self.assertEqual(calc["totalamnt"], 125400.0)
		self.assertNotIn(999, (calc["totalamnt"],))

	def test_bag_line_total(self):
		header = _Header(
			doctype="Purchase Invoice",
			kantatype="Total Weight",
			amntby="Bag",
			mundtype="N",
		)
		line = _Line(
			truckqty=800,
			delikanta=800,
			lessweight=0,
			bagqty=20,
			bagrate=30,
			bags_are="PU",
			rate=100,
			discount=0,
			dust=0,
		)
		calc = calc_line_totals(line, header, is_purchase=True)
		self.assertEqual(calc["bagamnt"], 600.0)
		self.assertEqual(calc["totalamnt"], 2600.0)  # 20*100 + 600

	def test_truck_qty_fallback_when_not_bag_or_mund(self):
		header = _Header(
			doctype="Sales Invoice",
			kantatype="Quantity",
			amntby="Truck",
			mundtype="N",
		)
		line = _Line(truckqty=5, rate=1000, lessweight=0, bagqty=0, bagrate=0, discount=50)
		calc = calc_line_totals(line, header, is_purchase=False)
		self.assertEqual(calc["totalamnt"], 4950.0)

	def test_receivable_includes_labour_not_line_total(self):
		header = _Header(
			doctype="Sales Invoice",
			kantatype="Total Weight",
			amntby="Mund",
			mundtype="N",
			brokery="Unpaid",
			borrow="Delivery",
			amount=10000,
		)
		line = _Line(cartage=500, truckadv=0, labouramnt=300, brokeramnt=0)
		header.details = [line]
		recalc_invoice_header(header, is_purchase=False)
		# 10000 + 300 labour - 500 cartage
		self.assertEqual(flt(header.receivable), 9800.0)

	def test_brokery_mund_on_purchase_line(self):
		header = _Header(
			doctype="Purchase Invoice",
			kantatype="Total Weight",
			amntby="Mund",
			mundtype="N",
		)
		line = _Line(
			truckqty=2000,
			delikanta=2000,
			lessweight=0,
			dust=0,
			bagqty=0,
			bagrate=0,
			rate=100,
			discount=0,
		)
		calc_line_totals(line, header, is_purchase=True)
		self.assertEqual(flt(line.brokery_mund), 50.0)


class TestGatePassCalc(unittest.TestCase):
	def test_gate_pass_line_weights(self):
		from millitrix.utils.gate_pass_calc import recalc_gate_pass_line

		header = _Header(kantatype="Delivery Kanta", gptype="Out")
		line = _Line(truckqty=100, delikanta=1000, lessweight=50, bagweight=0)
		recalc_gate_pass_line(line, header)
		self.assertEqual(flt(line.netweight), 950.0)


class TestStockAdjustmentCalc(unittest.TestCase):
	def test_adjustment_amount_from_delta(self):
		from unittest.mock import patch

		from millitrix.utils.stock_adjustment_calc import recalc_adjustment_line

		line = _Line(
			storeid="S1",
			itemcode="WHEAT",
			inc_stock=0,
			dec_stock=40,
			rate=5000,
			current_stock=0,
			adjusted_stock=0,
			amount=0,
		)
		with patch(
			"millitrix.utils.stock_adjustment_calc.get_in_store_item_name",
			return_value=None,
		):
			recalc_adjustment_line(line)
		self.assertEqual(flt(line.adjusted_stock), -40.0)
		self.assertEqual(flt(line.amount), 200000.0)  # 40 kg × 5000 (Oracle -(Inc-Dec)*Rate)


class TestStockTransferCalc(unittest.TestCase):
	def test_transfer_line_total(self):
		from millitrix.utils.stock_transfer_calc import recalc_transfer_line

		header = _Header(kantatype="Delivery Kanta", amntby="Truck")
		line = _Line(truckqty=1000, delikanta=1000, lessweight=50, rate=10, bagqty=5, bagrate=20)
		recalc_transfer_line(line, header)
		self.assertEqual(flt(line.netweight), 950.0)
		self.assertEqual(flt(line.totalamnt), 9600.0)  # 950*10 + 100


class TestProductionCalcOracleParity(unittest.TestCase):
	def test_crash_refine_input_formulas(self):
		line = _Line(bagqty=10, bagweight=50, bagdust=2, dip=3, mundtype="N")
		recalc_input_line(line)
		self.assertEqual(input_total_weight(line), 500)
		self.assertEqual(ref_weight_qty(line), 480)
		self.assertEqual(ref_bags_qty(line), 10)
		self.assertEqual(prod_1_qty(line), 120)  # 40 * 3
		self.assertEqual(prod_2_qty(line), 360)

	def test_bagamnt(self):
		self.assertEqual(calc_bagamnt(_Line(bagqty=5, bagrate=20, bags_are="PU"), is_purchase=True), 100.0)
		self.assertEqual(calc_bagamnt(_Line(bagqty=5, bagrate=20, bags_are="SA"), is_purchase=False), 100.0)
		self.assertEqual(calc_bagamnt(_Line(bagqty=5, bagrate=20), is_purchase=False), 0.0)

	def test_total_weight_uses_bagqty(self):
		from millitrix.utils.invoice_calc import display_total_weight

		line = _Line(bagqty=10, bagweight=80, truckqty=999)
		self.assertEqual(display_total_weight(line, "T"), 800.0)

	def test_purchase_payable_adds_paid_brokery(self):
		header = _Header(
			doctype="Purchase Invoice",
			kantatype="Total Weight",
			amntby="Mund",
			mundtype="N",
			brokery="Paid",
			borrow="Delivery",
			amount=10000,
		)
		line = _Line(cartage=0, truckadv=0, labouramnt=0, brokeramnt=500)
		header.details = [line]
		recalc_invoice_header(header, is_purchase=True)
		self.assertEqual(flt(header.payable), 10500.0)

	def test_purchase_return_receivable_subtracts_paid_brokery(self):
		header = _Header(
			doctype="Purchase Return",
			kantatype="Total Weight",
			amntby="Mund",
			mundtype="N",
			brokery="Paid",
			borrow="Delivery",
			amount=10000,
		)
		line = _Line(cartage=0, truckadv=0, labouramnt=200, brokeramnt=500)
		header.details = [line]
		recalc_invoice_header(header, is_purchase=True)
		self.assertEqual(flt(header.receivable), 9700.0)

	def test_sales_return_payable_adds_paid_brokery(self):
		header = _Header(
			doctype="Sales Return",
			kantatype="Total Weight",
			amntby="Mund",
			mundtype="N",
			brokery="Paid",
			borrow="Delivery",
			amount=10000,
		)
		line = _Line(cartage=0, truckadv=0, labouramnt=500, brokeramnt=500)
		header.details = [line]
		recalc_invoice_header(header, is_purchase=False)
		# Oracle SR: no labour on header — only amount + paid brokery
		self.assertEqual(flt(header.payable), 10500.0)

	def test_purchase_invoice_payable_excludes_labour(self):
		header = _Header(
			doctype="Purchase Invoice",
			kantatype="Total Weight",
			amntby="Mund",
			mundtype="N",
			brokery="Not Paid",
			borrow="Delivery",
			amount=10000,
		)
		line = _Line(cartage=500, truckadv=0, labouramnt=300, brokeramnt=0)
		header.details = [line]
		recalc_invoice_header(header, is_purchase=True)
		self.assertEqual(flt(header.payable), 9500.0)

	def test_net_weight_uses_bag_total_not_delikanta(self):
		header = _Header(doctype="Purchase Invoice", kantatype="Total Weight", amntby="Mund", mundtype="N")
		line = _Line(
			bagqty=10,
			bagweight=80,
			delikanta=500,
			lessweight=0,
			dust=0,
			rate=100,
			discount=0,
		)
		calc = calc_line_totals(line, header, is_purchase=True)
		self.assertEqual(calc["netweight"], 800.0)
		self.assertEqual(calc["mund"], 20.0)
