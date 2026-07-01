# Copyright (c) 2026, Millitrix and contributors
# Blueprint 4.11 — Mill Settings as Single DocType with Link fields.

from __future__ import annotations

import frappe
from frappe import _

SETTING_FIELDS: dict[str, str] = {
	"Trade Purchase": "trade_purchase",
	"Trade Sales": "trade_sales",
	"Cash": "cash",
	"Bardana": "bardana",
	"Bardana Store": "bardana_store",
	"Party Brokery": "party_brokery",
	"Brokery Exp": "brokery_exp",
	"Receivable Discount": "receivable_discount",
	"Payable Discount": "payable_discount",
	"Purchase Cartage Exp": "purchase_cartage_exp",
	"Purchase OtherBill": "purchase_other_bill",
	"Purchases OtherBill": "purchases_other_bill",
	"Sales OtherBill": "sales_other_bill",
	"Suspense": "suspense",
	"Labour Payable": "labour_payable",
	"Labour Receivable": "labour_receivable",
	"Stock Movement Cartage": "stock_movement_cartage",
	"Item Stock GL": "item_stock_gl",
	"Item Opening GL": "item_opening_gl",
	"Item Closing GL": "item_closing_gl",
	"Closing Item GL": "closing_item_gl",
	"Dust Item": "dust_item",
	"Salary Exp": "salary_exp",
	"Capital": "capital",
	"Income Summary": "income_summary",
	"Employee": "employee_account",
	"Custom UI URL": "custom_ui_url",
}

_ACCOUNT_SETTINGS = frozenset(SETTING_FIELDS) - {"Bardana Store", "Dust Item", "Custom UI URL", "Financial Year"}


class _SettingView:
	"""Compatibility shim for legacy row-based Mill Setting access."""

	def __init__(self, *, paracode=None, fromdate=None, todate=None):
		self.paracode = paracode
		self.fromdate = fromdate
		self.todate = todate


def _settings_doc():
	return frappe.get_single("GL Parameter")


def get_setting(description: str) -> _SettingView:
	if description == "Financial Year":
		doc = _settings_doc()
		return _SettingView(fromdate=doc.financial_year_from, todate=doc.financial_year_to)

	fieldname = SETTING_FIELDS.get(description)
	if not fieldname:
		frappe.throw(_("Unknown GL Parameter key: {0}").format(description))

	doc = _settings_doc()
	return _SettingView(paracode=doc.get(fieldname))


def get_setting_value(description: str) -> str | None:
	if description == "Financial Year":
		doc = _settings_doc()
		if doc.financial_year_from and doc.financial_year_to:
			return f"{doc.financial_year_from}|{doc.financial_year_to}"
		return None

	view = get_setting(description)
	value = view.paracode
	if value in (None, "", "-"):
		return None
	return str(value)


def get_setting_account(description: str) -> str:
	if description not in _ACCOUNT_SETTINGS:
		frappe.throw(_("Setting '{0}' is not a Chart of Accounts link").format(description))

	accid = get_setting_value(description)
	if not accid:
		frappe.throw(
			_("GL Parameter '{0}' has no GL account configured.").format(description)
		)
	return accid


def get_discount_account(flow: str) -> str:
	"""GL account for PNR discount notes; falls back to brokery accounts."""
	primary = "Receivable Discount" if flow == "receipt" else "Payable Discount"
	fallback = "Party Brokery" if flow == "receipt" else "Brokery Exp"
	accid = get_setting_value(primary) or get_setting_value(fallback)
	if not accid:
		frappe.throw(
			_("Configure {0} or {1} in GL Parameter").format(primary, fallback)
		)
	return accid


def get_fiscal_year() -> tuple[str, str]:
	doc = _settings_doc()
	if not doc.financial_year_from or not doc.financial_year_to:
		frappe.throw(_("Financial Year dates not configured in GL Parameter"))
	return str(doc.financial_year_from), str(doc.financial_year_to)
