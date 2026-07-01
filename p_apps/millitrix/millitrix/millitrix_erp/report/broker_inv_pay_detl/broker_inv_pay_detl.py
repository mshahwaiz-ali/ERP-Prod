# Copyright (c) 2026, Millitrix and contributors
# Oracle BrokerInvPayDetl.rdf

from __future__ import annotations

from frappe import _

from millitrix.utils.final_reports import get_broker_inv_pay_detl_rows
from millitrix.utils.report_filters import normalize_report_dates


def execute(filters=None):
	return get_columns(), get_broker_inv_pay_detl_rows(normalize_report_dates(filters))


def get_columns():
	return [
		{"label": _("Type"), "fieldname": "inv_type", "fieldtype": "Data", "width": 80},
		{"label": _("Invoice No"), "fieldname": "invno", "fieldtype": "Data", "width": 110},
		{"label": _("Date"), "fieldname": "invdate", "fieldtype": "Date", "width": 110},
		{"label": _("Location"), "fieldname": "location_id", "fieldtype": "Link", "options": "Location", "width": 120},
		{"label": _("Broker"), "fieldname": "brokerid", "fieldtype": "Link", "options": "Party", "width": 130},
		{"label": _("Broker Name"), "fieldname": "broker_name", "fieldtype": "Data", "width": 160},
		{"label": _("Party"), "fieldname": "partyid", "fieldtype": "Link", "options": "Party", "width": 130},
		{"label": _("Party Name"), "fieldname": "party_name", "fieldtype": "Data", "width": 160},
		{"label": _("Item"), "fieldname": "itemcode", "fieldtype": "Link", "options": "Item Setup", "width": 120},
		{"label": _("Truck"), "fieldname": "truckno", "fieldtype": "Data", "width": 90},
		{"label": _("Bags"), "fieldname": "bagqty", "fieldtype": "Float", "width": 80},
		{"label": _("Net Weight"), "fieldname": "netweight", "fieldtype": "Float", "width": 100},
		{"label": _("Line Brokery"), "fieldname": "brokeramnt", "fieldtype": "Currency", "width": 110},
		{"label": _("Less Brokery"), "fieldname": "less_brokery", "fieldtype": "Currency", "width": 110},
		{"label": _("Less Cartage"), "fieldname": "less_cartage", "fieldtype": "Currency", "width": 110},
		{"label": _("Brokery Payable"), "fieldname": "brokerypayable", "fieldtype": "Currency", "width": 120},
		{"label": _("Brokery Status"), "fieldname": "brokery", "fieldtype": "Data", "width": 100},
	]
