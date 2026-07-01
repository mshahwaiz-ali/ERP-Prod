# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from frappe import _
from millitrix.utils.finance_reports import get_coa_report_rows

def execute(filters=None):
	return get_columns(), get_coa_report_rows(filters)

def get_columns():
	return [
		{"label": _("Account"), "fieldname": "name", "fieldtype": "Link", "options": "Chart of Accounting", "width": 120},
		{"label": _("Acc ID"), "fieldname": "accid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 120},
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 220},
		{"label": _("Nature"), "fieldname": "nature", "fieldtype": "Data", "width": 80},
		{"label": _("Level"), "fieldname": "chartlevel", "fieldtype": "Int", "width": 70},
		{"label": _("L1 Acc"), "fieldname": "l1_accid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 100},
		{"label": _("L1 Desc"), "fieldname": "l1_acc_desc", "fieldtype": "Data", "width": 160},
		{"label": _("L2 Acc"), "fieldname": "l2_accid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 100},
		{"label": _("L2 Desc"), "fieldname": "l2_acc_desc", "fieldtype": "Data", "width": 160},
		{"label": _("L3 Acc"), "fieldname": "l3_accid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 100},
		{"label": _("L3 Desc"), "fieldname": "l3_acc_desc", "fieldtype": "Data", "width": 160},
		{"label": _("L4 Acc"), "fieldname": "l4_accid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 100},
		{"label": _("L4 Desc"), "fieldname": "l4_acc_desc", "fieldtype": "Data", "width": 160},
		{"label": _("L5 Acc"), "fieldname": "l5_accid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 100},
		{"label": _("L5 Desc"), "fieldname": "l5_acc_desc", "fieldtype": "Data", "width": 160},
		{"label": _("Parent"), "fieldname": "parentid", "fieldtype": "Link", "options": "Chart of Accounting", "width": 120},
		{"label": _("Trans Flag"), "fieldname": "transflag", "fieldtype": "Data", "width": 90},
	]
