# Copyright (c) 2026, Millitrix and contributors
# Oracle Party_Info.RDF

from __future__ import annotations

from frappe import _

from millitrix.utils.extended_reports import get_party_info_rows
from millitrix.utils.report_columns import normalize_columns, party_column


def execute(filters=None):
	return get_columns(), get_party_info_rows(filters)


def get_columns():
	return normalize_columns(
		[
			party_column(width=120),
			{"label": _("Party Name"), "fieldname": "party_name", "fieldtype": "Data", "width": 180},
			{"label": _("Category"), "fieldname": "category_name", "fieldtype": "Data", "width": 120},
			{"label": _("City"), "fieldname": "city_name", "fieldtype": "Data", "width": 120},
			{"label": _("Address"), "fieldname": "address", "fieldtype": "Data", "width": 220},
			{"label": _("Phone"), "fieldname": "phno1", "fieldtype": "Data", "width": 100},
			{"label": _("Phone 2"), "fieldname": "phno2", "fieldtype": "Data", "width": 100},
			{"label": _("Mobile"), "fieldname": "mobileno", "fieldtype": "Data", "width": 100},
			{"label": _("Res. Phone"), "fieldname": "resphno", "fieldtype": "Data", "width": 100},
			{"label": _("Credit Limit"), "fieldname": "creditlimit", "fieldtype": "Currency", "width": 110},
			{"label": _("Credit Days"), "fieldname": "creditdays", "fieldtype": "Int", "width": 90},
		]
	)
