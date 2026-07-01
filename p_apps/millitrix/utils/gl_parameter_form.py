# Copyright (c) 2026, Millitrix and contributors
# Oracle GLParaForm.fmx — GL report launcher (not Mill Settings GL Parameter doctype).

from __future__ import annotations

import json

import frappe
from frappe import _

from millitrix.utils.erpnext_compat import get_session_location
from millitrix.utils.report_filters import (
	get_saved_report_parameters,
	normalize_report_dates,
	save_report_parameters,
)
from millitrix.utils.report_registry import resolve_report_name
from millitrix.utils.user_permissions import get_mill_user

GL_PARA_RUNTIME = "GLParaForm"

GL_PARA_REPORTS: tuple[dict, ...] = (
	{"legacy": "Trial_Balance", "label": "Trial Balance", "requires": ()},
	{"legacy": "Trial_Balance_1", "label": "Trial Balance (Location)", "requires": ("location_id",)},
	{"legacy": "AccLedger", "label": "Account Ledger", "requires": ("accid",)},
	{"legacy": "Account_Balance", "label": "Account Balances", "requires": ()},
	{"legacy": "COA", "label": "Chart Of Accounting", "requires": ()},
	{"legacy": "IncomeStatement", "label": "Income Statement", "requires": ()},
	{"legacy": "BalanceSheet", "label": "Balance Sheet", "requires": ()},
	{"legacy": "PNL", "label": "Profit and Loss", "requires": ()},
	{"legacy": "CashFlow", "label": "Cash Flow", "requires": ()},
	{"legacy": "CashFlowDetail", "label": "Cash Flow Detail", "requires": ()},
	{"legacy": "CashBook", "label": "Cash Book", "requires": ()},
	{"legacy": "BankBook", "label": "Bank Book", "requires": ()},
	{"legacy": "BankStatus", "label": "Bank Status", "requires": ()},
	{"legacy": "BankFinanceStatus", "label": "Bank Finance Status", "requires": ()},
	{"legacy": "PartyBalance", "label": "Party Balance", "requires": ()},
	{"legacy": "Party_Bal_Paid", "label": "Party Balance and Payment", "requires": ()},
	{"legacy": "Expanse_Register", "label": "Expanse Register", "requires": ()},
	{"legacy": "GJ", "label": "General Journal", "requires": ()},
	{"legacy": "Payment_Register", "label": "Payment Register", "requires": ()},
	{"legacy": "Receipt_Register", "label": "Receipt Register", "requires": ()},
	{"legacy": "VoucherRegister", "label": "Voucher", "requires": ()},
)


def get_gl_para_module_id() -> str:
	module_id = frappe.db.get_value("Module", {"runtimefile": GL_PARA_RUNTIME}, "name")
	if module_id:
		return module_id
	module_id = frappe.db.get_value("Module", {"module": ["like", "%GL Parameter%"]}, "name")
	if module_id:
		return module_id
	doc = frappe.get_doc(
		{
			"doctype": "Module",
			"nature": "Assets",
			"module": "GL Parameter Form",
			"moduletype": "F",
			"runtimefile": GL_PARA_RUNTIME,
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
	frappe.throw(_("User Rights record is required to run GL reports."))


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


def list_gl_para_reports() -> list[dict]:
	out: list[dict] = []
	for row in GL_PARA_REPORTS:
		report_name = resolve_report_name(row["legacy"])
		if not report_name:
			continue
		out.append(
			{
				"legacy": row["legacy"],
				"label": row["label"],
				"report_name": report_name,
				"requires": list(row["requires"]),
			}
		)
	return out


def get_gl_para_defaults() -> dict:
	location_id = get_session_location()
	userid = _resolve_userid(required=False)
	moduleid = get_gl_para_module_id()
	saved = get_saved_report_parameters(location_id or "", userid, moduleid) if userid else {}
	extra = _parse_parameter_string(saved.get("parameter_string"))
	defaults = normalize_report_dates({})
	return {
		"reports": list_gl_para_reports(),
		"location_id": location_id,
		"from_date": saved.get("from_date") or defaults.get("from_date"),
		"to_date": saved.get("to_date") or defaults.get("to_date"),
		"coa_level": saved.get("coa_level") or extra.get("coa_level"),
		"partyid": extra.get("partyid"),
		"accid": extra.get("accid"),
		"filter_mode": extra.get("filter_mode") or "date",
		"from_voucherno": extra.get("from_voucherno"),
		"to_voucherno": extra.get("to_voucherno"),
		"output_mode": extra.get("output_mode") or "preview",
		"selected_report": extra.get("selected_report"),
	}


def build_report_filters(payload: dict) -> dict:
	payload = frappe.parse_json(payload) if isinstance(payload, str) else dict(payload or {})
	location_id = payload.get("location_id") or get_session_location()
	filter_mode = payload.get("filter_mode") or "date"
	filters: dict = {"location_id": location_id}

	if filter_mode == "voucherno":
		from_no = payload.get("from_voucherno")
		to_no = payload.get("to_voucherno")
		if from_no in (None, "") or to_no in (None, ""):
			frappe.throw(_("From Voucher No and To Voucher No are required."))
		filters["from_voucherno"] = str(from_no).strip()
		filters["to_voucherno"] = str(to_no).strip()
	else:
		filters = normalize_report_dates(
			{
				"from_date": payload.get("from_date"),
				"to_date": payload.get("to_date"),
				**filters,
			}
		)

	for key in ("partyid", "accid"):
		if payload.get(key):
			filters[key] = payload[key]

	coa_level = payload.get("coa_level")
	if coa_level not in (None, ""):
		filters["coa_level"] = int(coa_level)
		filters["chartlevel"] = int(coa_level)

	return filters


def _report_meta(legacy_or_name: str) -> dict | None:
	for row in GL_PARA_REPORTS:
		if row["legacy"] == legacy_or_name:
			report_name = resolve_report_name(row["legacy"])
			if not report_name:
				return None
			return {**row, "report_name": report_name}
	report_name = resolve_report_name(legacy_or_name)
	if not report_name:
		return None
	return {"legacy": legacy_or_name, "label": report_name, "report_name": report_name, "requires": ()}


def validate_gl_para_execute(payload: dict) -> dict:
	selected = payload.get("selected_report")
	if not selected:
		frappe.throw(_("Select a report format."))

	meta = _report_meta(selected)
	if not meta:
		frappe.throw(_("Report is not available: {0}").format(selected))

	filters = build_report_filters(payload)
	for field in meta.get("requires") or ():
		if field == "location_id":
			if not filters.get("location_id"):
				frappe.throw(_("Location is required for this report."))
			continue
		if not filters.get(field):
			label = _("Client") if field == "partyid" else _("Account") if field == "accid" else field
			frappe.throw(_("Set {0} in Condition before Execute.").format(label))

	from millitrix.utils.user_permissions import assert_report_access

	assert_report_access(meta["report_name"])
	return {"report_name": meta["report_name"], "legacy": meta["legacy"], "filters": filters}


def save_gl_para_parameters(payload: dict) -> str:
	payload = frappe.parse_json(payload) if isinstance(payload, str) else dict(payload or {})
	location_id = payload.get("location_id") or get_session_location()
	if not location_id:
		frappe.throw(_("Location is required."))

	userid = _resolve_userid()
	moduleid = get_gl_para_module_id()
	extra = {
		"filter_mode": payload.get("filter_mode") or "date",
		"from_voucherno": payload.get("from_voucherno"),
		"to_voucherno": payload.get("to_voucherno"),
		"partyid": payload.get("partyid"),
		"accid": payload.get("accid"),
		"coa_level": payload.get("coa_level"),
		"output_mode": payload.get("output_mode") or "preview",
		"selected_report": payload.get("selected_report"),
	}

	cache_filters = {
		"from_date": payload.get("from_date"),
		"to_date": payload.get("to_date"),
		"coa_level": payload.get("coa_level"),
		"parameter_string": _serialize_parameter_string(extra),
	}
	return save_report_parameters(location_id, userid, moduleid, cache_filters)


def execute_gl_para_report(payload: dict) -> dict:
	payload = frappe.parse_json(payload) if isinstance(payload, str) else dict(payload or {})
	result = validate_gl_para_execute(payload)
	save_gl_para_parameters(payload)
	output_mode = payload.get("output_mode") or "preview"
	return {**result, "output_mode": output_mode}
