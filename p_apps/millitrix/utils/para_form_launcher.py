# Copyright (c) 2026, Millitrix and contributors
# Oracle PurchParaForm / SalesParaForm / … — report launcher pages.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import frappe
from frappe import _

from millitrix.utils.client_doctype_map import report_display_name
from millitrix.utils.erpnext_compat import get_session_location
from millitrix.utils.report_filters import (
	get_saved_report_parameters,
	normalize_report_dates,
	save_report_parameters,
)
from millitrix.utils.report_registry import resolve_report_name
from millitrix.utils.user_permissions import get_mill_user

_PURCHASE_REPORTS = (
	"POPending",
	"PORegister",
	"POSummary",
	"POInvDetail",
	"PInvRegister",
	"PIOutstanding",
	"PISummary",
	"PurchInvoice",
	"PurchInvSummary",
	"PurchItemSummary",
	"PurchInvPayment",
	"PurchInvPayDetl",
	"PurchInvPayDetl_Consider",
	"DailyItemPurch",
	"MonthlyItemPurch",
	"SupplierLedgerSummary",
	"SuppOrdInvDetl",
	"SuppPayAndInv",
	"BrokerInvPayment",
	"BrokerInvPayDetl",
	"BrokerLedgerSummary",
	"Party_Info",
)

_SALES_REPORTS = (
	"SOPending",
	"SORegister",
	"SOSummary",
	"SOInvDetail",
	"SInvRegister",
	"SIOutstanding",
	"SISummary",
	"SalesInvoice",
	"SalesInvSummary",
	"SalesItemSummary",
	"SalesInvReceipt",
	"SalesInvRcptDetl",
	"SalesInvRcptDetl_Consider",
	"SIPOutstanding",
	"DailyItemSales",
	"MonthlyItemSales",
	"CustLedgerSummary",
	"CustAging",
	"CustOrdInvDetl",
	"SuppInvAndPay",
	"Party_Info",
)

_STOCK_REPORTS = (
	"Item_Stock",
	"ItemLedger",
	"ItemWiseStock",
	"ItemBinCard",
	"ItemDailyStock",
	"StkRece_Summary",
	"TStk_Summary",
	"UnSubmit_Stock",
	"PartyBardana",
	"PartyBardanaBincard",
)

_FINANCIAL_REPORTS = (
	"Trial_Balance",
	"Trial_Balance_1",
	"AccLedger",
	"IncomeStatement",
	"BalanceSheet",
	"PNL",
	"CashFlow",
	"CashFlowDetail",
	"CashBook",
	"BankBook",
	"BankStatus",
	"BankFinanceStatus",
	"PartyBalance",
	"Party_Bal_Paid",
	"Account_Balance",
	"COA",
	"GJ",
	"VoucherRegister",
)

_PAYABLE_REPORTS = (
	"Payment_Register",
	"PartyPRegister",
	"PayableDRegister",
	"AdvancePRegister",
	"AdvPAdjustReg",
	"PIOutstanding",
	"PurchInvPayment",
	"PurchInvPayDetl",
	"PurchInvPayDetl_Consider",
	"SuppPayAndInv",
	"BrokerInvPayment",
	"BrokerInvPayDetl",
	"Party_Bal_Paid",
)

_RECEIVABLE_REPORTS = (
	"Receipt_Register",
	"PartyRRegister",
	"ReceivableDRegister",
	"AdvanceRRegister",
	"AdvRAdjustReg",
	"SIOutstanding",
	"SIPOutstanding",
	"SalesInvReceipt",
	"SalesInvRcptDetl",
	"SalesInvRcptDetl_Consider",
	"SuppInvAndPay",
	"CustAging",
	"Party_Bal_Paid",
)

CONDITION_FIELD_META: dict[str, dict[str, Any]] = {
	"supplierid": {"label": "Supplier", "fieldtype": "Link", "options": "Party", "pcat_id": ["12"]},
	"customerid": {"label": "Customer", "fieldtype": "Link", "options": "Party", "pcat_id": ["13"]},
	"partyid": {"label": "Party", "fieldtype": "Link", "options": "Party"},
	"brokerid": {"label": "Broker", "fieldtype": "Link", "options": "Party", "pcat_id": ["11"]},
	"itemcode": {"label": "Item", "fieldtype": "Link", "options": "Item Setup"},
	"iclassid": {"label": "Item Class", "fieldtype": "Link", "options": "Item Class"},
	"storeid": {"label": "Store", "fieldtype": "Link", "options": "Store Setup"},
	"from_storeid": {"label": "From Store", "fieldtype": "Link", "options": "Store Setup"},
	"to_storeid": {"label": "To Store", "fieldtype": "Link", "options": "Store Setup"},
	"accid": {"label": "Account", "fieldtype": "Link", "options": "Chart of Accounting"},
	"coa_level": {"label": "Chart of Accounts Level", "fieldtype": "Int"},
	"from_svouch": {"label": "From Submit Voucher No", "fieldtype": "Int"},
	"to_svouch": {"label": "To Submit Voucher No", "fieldtype": "Int"},
	"from_purchinvno": {"label": "From Purchase Invoice No", "fieldtype": "Int"},
	"to_purchinvno": {"label": "To Purchase Invoice No", "fieldtype": "Int"},
	"from_ponumber": {"label": "From PO Number", "fieldtype": "Int"},
	"to_ponumber": {"label": "To PO Number", "fieldtype": "Int"},
	"from_salesinvno": {"label": "From Sales Invoice No", "fieldtype": "Int"},
	"to_salesinvno": {"label": "To Sales Invoice No", "fieldtype": "Int"},
	"from_sonumber": {"label": "From SO Number", "fieldtype": "Int"},
	"to_sonumber": {"label": "To SO Number", "fieldtype": "Int"},
	"posted_filter": {
		"label": "Posted",
		"fieldtype": "Select",
		"options": "Submitted\nDraft\nAll",
		"default": "Submitted",
	},
	"report_by": {
		"label": "Report By",
		"fieldtype": "Select",
		"options": "Date\nInvoice No\nPO No",
		"default": "Date",
	},
	"truckno": {"label": "Truck No", "fieldtype": "Data"},
	"p_days": {"label": "Outstanding Days", "fieldtype": "Int"},
	"order_status": {
		"label": "Order Status",
		"fieldtype": "Select",
		"options": "\nInitial\nIn Progress\nCompleted\nCancelled",
	},
}


@dataclass(frozen=True)
class ParaFormSpec:
	key: str
	runtime: str
	module_name: str
	title: str
	report_legacy_ids: tuple[str, ...]
	condition_fields: tuple[str, ...] = ()
	report_requires: dict[str, tuple[str, ...]] = field(default_factory=dict)


PARA_FORM_SPECS: dict[str, ParaFormSpec] = {
	"purchase": ParaFormSpec(
		key="purchase",
		runtime="PurchParaForm",
		module_name="Purchase Parameter Form",
		title="Purchase Parameter Form",
		report_legacy_ids=_PURCHASE_REPORTS,
		condition_fields=(
			"report_by",
			"supplierid",
			"brokerid",
			"itemcode",
			"iclassid",
			"storeid",
			"order_status",
			"from_purchinvno",
			"to_purchinvno",
			"from_ponumber",
			"to_ponumber",
			"truckno",
			"p_days",
			"posted_filter",
		),
		report_requires={"AccLedger": ("accid",), "Trial_Balance_1": ("location_id",)},
	),
	"sales": ParaFormSpec(
		key="sales",
		runtime="SalesParaForm",
		module_name="Sales Parameter Form",
		title="Sales Parameter Form",
		report_legacy_ids=_SALES_REPORTS,
		condition_fields=(
			"report_by",
			"customerid",
			"brokerid",
			"itemcode",
			"iclassid",
			"storeid",
			"order_status",
			"from_salesinvno",
			"to_salesinvno",
			"from_sonumber",
			"to_sonumber",
			"truckno",
			"p_days",
			"posted_filter",
		),
	),
	"stock": ParaFormSpec(
		key="stock",
		runtime="StockParaForm",
		module_name="Stock Parameter Form",
		title="Stock Parameter Form",
		report_legacy_ids=_STOCK_REPORTS,
		condition_fields=("itemcode", "iclassid", "storeid", "from_storeid", "to_storeid"),
	),
	"financial": ParaFormSpec(
		key="financial",
		runtime="FinancialParaForm",
		module_name="Financial Parameter Form",
		title="Financial Parameter Form",
		report_legacy_ids=_FINANCIAL_REPORTS,
		condition_fields=("partyid", "accid", "coa_level", "report_by", "from_svouch", "to_svouch"),
		report_requires={"AccLedger": ("accid",), "Trial_Balance_1": ("location_id",)},
	),
	"payable": ParaFormSpec(
		key="payable",
		runtime="PayableParaForm",
		module_name="Payable Parameter Form",
		title="Payable Parameter Form",
		report_legacy_ids=_PAYABLE_REPORTS,
		condition_fields=(
			"report_by",
			"supplierid",
			"brokerid",
			"itemcode",
			"from_purchinvno",
			"to_purchinvno",
			"truckno",
			"p_days",
			"posted_filter",
		),
	),
	"receivable": ParaFormSpec(
		key="receivable",
		runtime="ReceivableParaForm",
		module_name="Receivable Parameter Form",
		title="Receivable Parameter Form",
		report_legacy_ids=_RECEIVABLE_REPORTS,
		condition_fields=(
			"report_by",
			"customerid",
			"brokerid",
			"itemcode",
			"from_salesinvno",
			"to_salesinvno",
			"truckno",
			"p_days",
			"posted_filter",
		),
	),
}


def get_para_form_spec(form_key: str) -> ParaFormSpec:
	spec = PARA_FORM_SPECS.get(form_key)
	if not spec:
		frappe.throw(_("Unknown parameter form: {0}").format(form_key))
	return spec


def resolve_para_form_key_for_report(report_name: str) -> str | None:
	"""Map canonical Frappe report name to para-form key (purchase, sales, …)."""
	target = (report_name or "").strip()
	if not target:
		return None
	for key, spec in PARA_FORM_SPECS.items():
		for legacy_id in spec.report_legacy_ids:
			if resolve_report_name(legacy_id) == target:
				return key
	return None


def get_saved_filters_for_report(report_name: str) -> dict:
	"""Load Oracle-style saved filters for direct report open."""
	form_key = resolve_para_form_key_for_report(report_name)
	if not form_key:
		return {}
	userid = _resolve_userid(required=False)
	if not userid:
		return {}
	location_id = get_session_location() or ""
	spec = get_para_form_spec(form_key)
	moduleid = get_para_module_id(spec)
	saved = get_saved_report_parameters(location_id, userid, moduleid)
	extra = _parse_parameter_string(saved.pop("parameter_string", None))
	for key, value in extra.items():
		if value is not None and not saved.get(key):
			saved[key] = value
	return normalize_report_dates(saved)


def get_para_module_id(spec: ParaFormSpec) -> str:
	module_id = frappe.db.get_value("Module", {"runtimefile": spec.runtime}, "name")
	if module_id:
		return module_id
	module_id = frappe.db.get_value("Module", {"module": spec.module_name}, "name")
	if module_id:
		return module_id
	doc = frappe.get_doc(
		{
			"doctype": "Module",
			"nature": "Assets",
			"module": spec.module_name,
			"moduletype": "F",
			"runtimefile": spec.runtime,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _resolve_userid(*, required: bool = True) -> str:
	mill_user = get_mill_user()
	if mill_user:
		return mill_user.name
	if frappe.session.user == "Administrator":
		row = frappe.db.get_value("User Rights", {}, "name")
		if row:
			return row
	if not required:
		return ""
	frappe.throw(_("User Rights record is required to run reports."))


def _parse_parameter_string(raw: str | None) -> dict:
	if not raw:
		return {}
	try:
		data = json.loads(raw)
	except (TypeError, json.JSONDecodeError):
		return {}
	return data if isinstance(data, dict) else {}


def _serialize_parameter_string(extra: dict) -> str:
	return json.dumps({k: v for k, v in extra.items() if v not in (None, "")})


def list_para_reports(spec: ParaFormSpec) -> list[dict]:
	out: list[dict] = []
	for legacy in spec.report_legacy_ids:
		report_name = resolve_report_name(legacy)
		if not report_name:
			continue
		out.append(
			{
				"legacy": legacy,
				"label": report_display_name(legacy),
				"report_name": report_name,
				"requires": list(spec.report_requires.get(legacy, ())),
			}
		)
	return out


def get_condition_field_defs(spec: ParaFormSpec) -> list[dict]:
	defs: list[dict] = []
	for fieldname in spec.condition_fields:
		meta = CONDITION_FIELD_META.get(fieldname)
		if not meta:
			continue
		field_def = {"fieldname": fieldname, **meta}
		if fieldname == "report_by":
			if spec.key == "sales":
				field_def["options"] = "Date\nInvoice No\nSO No"
			elif spec.key == "purchase":
				field_def["options"] = "Date\nInvoice No\nPO No"
			elif spec.key == "financial":
				field_def["options"] = "Date\nSubmit Voucher No"
			elif spec.key in ("payable", "receivable"):
				field_def["options"] = "Date\nInvoice No"
		if spec.key == "financial" and fieldname == "partyid":
			field_def["pcat_id"] = ["12", "13"]
		defs.append(field_def)
	return defs


def get_para_defaults(form_key: str) -> dict:
	spec = get_para_form_spec(form_key)
	location_id = get_session_location()
	userid = _resolve_userid(required=False)
	moduleid = get_para_module_id(spec)
	saved = get_saved_report_parameters(location_id or "", userid, moduleid) if userid else {}
	extra = _parse_parameter_string(saved.get("parameter_string"))
	defaults = normalize_report_dates({})
	result = {
		"form_key": spec.key,
		"title": spec.title,
		"reports": list_para_reports(spec),
		"condition_fields": get_condition_field_defs(spec),
		"location_id": location_id,
		"from_date": saved.get("from_date") or defaults.get("from_date"),
		"to_date": saved.get("to_date") or defaults.get("to_date"),
		"output_mode": extra.get("output_mode") or "preview",
		"selected_report": extra.get("selected_report"),
	}
	for fieldname in spec.condition_fields:
		if fieldname in extra:
			result[fieldname] = extra[fieldname]
	return result


def build_para_report_filters(form_key: str, payload: dict) -> dict:
	spec = get_para_form_spec(form_key)
	payload = frappe.parse_json(payload) if isinstance(payload, str) else dict(payload or {})
	location_id = payload.get("location_id") or get_session_location()
	filters = normalize_report_dates(
		{
			"from_date": payload.get("from_date"),
			"to_date": payload.get("to_date"),
			"location_id": location_id,
		}
	)

	for key in spec.condition_fields:
		value = payload.get(key)
		if value in (None, ""):
			continue
		if key == "posted_filter":
			posted = str(value).strip().lower()
			if posted == "draft":
				filters["docstatus"] = 0
			elif posted == "all":
				filters["include_consider"] = 1
			continue
		filters[key] = value

	if payload.get("supplierid"):
		filters.setdefault("partyid", payload["supplierid"])
	if payload.get("customerid"):
		filters.setdefault("partyid", payload["customerid"])

	report_by = str(payload.get("report_by") or "Date").strip().lower()
	if spec.key == "financial":
		if report_by.startswith("submit") or report_by.startswith("sv"):
			filters["report_by"] = "SVCH"
			if payload.get("from_svouch") not in (None, ""):
				filters["from_svouch"] = int(payload["from_svouch"])
			if payload.get("to_svouch") not in (None, ""):
				filters["to_svouch"] = int(payload["to_svouch"])
		else:
			filters["report_by"] = "D"
	elif report_by.startswith("inv"):
		filters["report_by"] = "Inv"
	elif report_by.startswith("po") or report_by.startswith("so"):
		filters["report_by"] = "PO"
	else:
		filters["report_by"] = "D"

	if payload.get("order_status"):
		filters["order_status"] = payload["order_status"]
	if payload.get("p_days") not in (None, ""):
		filters["p_days"] = int(payload["p_days"])

	coa_level = payload.get("coa_level")
	if coa_level not in (None, ""):
		filters["coa_level"] = int(coa_level)
		filters["chartlevel"] = int(coa_level)

	return filters


def _report_meta(spec: ParaFormSpec, legacy_or_name: str) -> dict | None:
	for row in list_para_reports(spec):
		if row["legacy"] == legacy_or_name:
			return row
	report_name = resolve_report_name(legacy_or_name)
	if not report_name:
		return None
	return {
		"legacy": legacy_or_name,
		"label": report_display_name(legacy_or_name),
		"report_name": report_name,
		"requires": list(spec.report_requires.get(legacy_or_name, ())),
	}


def validate_para_execute(form_key: str, payload: dict) -> dict:
	spec = get_para_form_spec(form_key)
	payload = frappe.parse_json(payload) if isinstance(payload, str) else dict(payload or {})
	selected = payload.get("selected_report")
	if not selected:
		frappe.throw(_("Select a report format."))

	meta = _report_meta(spec, selected)
	if not meta:
		frappe.throw(_("Report is not available: {0}").format(selected))

	filters = build_para_report_filters(form_key, payload)
	for field in meta.get("requires") or ():
		if field == "location_id":
			if not filters.get("location_id"):
				frappe.throw(_("Location is required for this report."))
			continue
		if not filters.get(field):
			label = CONDITION_FIELD_META.get(field, {}).get("label") or field
			frappe.throw(_("Set {0} in Condition before Execute.").format(_(label)))

	from millitrix.utils.user_permissions import assert_report_access

	assert_report_access(meta["report_name"])
	return {"report_name": meta["report_name"], "legacy": meta["legacy"], "filters": filters}


def save_para_parameters(form_key: str, payload: dict) -> str:
	spec = get_para_form_spec(form_key)
	payload = frappe.parse_json(payload) if isinstance(payload, str) else dict(payload or {})
	location_id = payload.get("location_id") or get_session_location()
	if not location_id:
		frappe.throw(_("Location is required."))

	userid = _resolve_userid()
	moduleid = get_para_module_id(spec)
	extra = {
		"output_mode": payload.get("output_mode") or "preview",
		"selected_report": payload.get("selected_report"),
	}
	for fieldname in spec.condition_fields:
		if payload.get(fieldname) not in (None, ""):
			extra[fieldname] = payload[fieldname]

	cache_filters = {
		"from_date": payload.get("from_date"),
		"to_date": payload.get("to_date"),
		"parameter_string": _serialize_parameter_string(extra),
	}
	return save_report_parameters(location_id, userid, moduleid, cache_filters)


def execute_para_report(form_key: str, payload: dict) -> dict:
	payload = frappe.parse_json(payload) if isinstance(payload, str) else dict(payload or {})
	result = validate_para_execute(form_key, payload)
	save_para_parameters(form_key, payload)
	output_mode = payload.get("output_mode") or "preview"
	return {**result, "output_mode": output_mode}
