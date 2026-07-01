# Copyright (c) 2026, Millitrix and contributors
# Oracle PurchInvPayment.RDF

from __future__ import annotations

from millitrix.utils.extended_reports import get_purch_inv_payment_register_rows
from millitrix.utils.report_columns import purch_inv_payment_register_columns
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return purch_inv_payment_register_columns(), get_purch_inv_payment_register_rows(normalize_report_dates(filters))
