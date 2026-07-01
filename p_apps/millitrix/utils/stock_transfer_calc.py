# Copyright (c) 2026, Millitrix and contributors
# Stock Transfer Note line recalc — mirrors millitrix_stock_forms.js

from __future__ import annotations

from frappe.utils import flt

from millitrix.utils.invoice_calc import calc_net_weight, display_total_weight
from millitrix.utils.invoice_fields import normalize_kantatype


def recalc_transfer_line(line, header) -> None:
	kantatype = normalize_kantatype(getattr(header, "kantatype", None) or "Delivery Kanta")
	total_weight = display_total_weight(line, kantatype, header=header)
	net = max(flt(calc_net_weight(line, kantatype, is_purchase=False, header=header)), 0)
	bag_amnt = flt(line.bagqty) * flt(line.bagrate)
	line.total_weight = flt(total_weight, 2)
	line.netweight = flt(net, 2)
	line.totalamnt = flt(net * flt(line.rate) + bag_amnt, 2)


def recalc_transfer_document(doc) -> None:
	for line in doc.details or []:
		recalc_transfer_line(line, doc)
