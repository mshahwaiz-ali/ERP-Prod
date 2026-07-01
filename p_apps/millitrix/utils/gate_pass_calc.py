# Copyright (c) 2026, Millitrix and contributors
# Gate Pass line recalc — mirrors in_out_gate_pass.js

from __future__ import annotations

from frappe.utils import flt

from millitrix.utils.invoice_calc import calc_net_weight, display_total_weight
from millitrix.utils.invoice_fields import normalize_kantatype
from millitrix.utils.stock import is_in_gptype


def recalc_gate_pass_line(line, header) -> None:
	kantatype = normalize_kantatype(getattr(header, "kantatype", None) or "Total Weight")
	is_purchase = is_in_gptype(getattr(header, "gptype", None))
	total_weight = display_total_weight(line, kantatype, header=header)
	net = max(flt(calc_net_weight(line, kantatype, is_purchase=is_purchase, header=header)), 0)
	line.total_weight = round(flt(total_weight), 2)
	line.netweight = round(flt(net), 2)


def recalc_gate_pass_document(doc) -> None:
	for line in doc.details or []:
		recalc_gate_pass_line(line, doc)
