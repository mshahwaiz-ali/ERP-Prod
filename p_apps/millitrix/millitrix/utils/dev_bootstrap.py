# Copyright (c) 2026, Millitrix and contributors
"""Dev/UAT site bootstrap — COA, GL Parameter, Menu, Module, User Rights."""

from __future__ import annotations

import frappe

from millitrix.utils.mill_setting import SETTING_FIELDS
from millitrix.utils.module_registry import MENU_ROWS, all_module_rows
from millitrix.utils.oracle_dump_reader import (
	coa_rows_for_gl_parameter,
	extract_project_para,
	minimum_coa_skeleton,
	resolve_dump_path,
)


def _upsert_doc(doctype: str, key_field: str, key_value, values: dict) -> str:
	name = frappe.db.get_value(doctype, {key_field: key_value}, "name")
	if name:
		frappe.db.set_value(doctype, name, values, update_modified=False)
		return name
	doc = frappe.get_doc({"doctype": doctype, key_field: key_value, **values})
	doc.insert(ignore_permissions=True)
	return doc.name


def seed_coa(*, dump_path: str | None = None, force: bool = False) -> int:
	"""Insert skeleton + GL Parameter posting accounts."""
	existing = frappe.db.count("Chart of Accounting")
	if existing > 20 and not force:
		return existing

	para: dict[str, str] = {}
	try:
		para = extract_project_para(dump_path)
	except FileNotFoundError:
		pass

	rows = minimum_coa_skeleton()
	if para:
		rows.extend(coa_rows_for_gl_parameter(para))
	rows.sort(key=lambda row: (row["chartlevel"], row["accid"]))

	created = 0
	for row in rows:
		accid = int(row["accid"])
		parent = row.get("parentid")
		parent_link = str(int(parent)) if parent not in (None, "") else None
		if parent_link and not frappe.db.exists("Chart of Accounting", parent_link):
			continue
		if frappe.db.exists("Chart of Accounting", str(accid)):
			frappe.db.set_value(
				"Chart of Accounting",
				str(accid),
				{
					"description": row["description"],
					"nature": row["nature"],
					"chartlevel": row["chartlevel"],
					"parentid": parent_link,
					"transflag": row.get("transflag", "Yes"),
				},
				update_modified=False,
			)
		else:
			frappe.get_doc(
				{
					"doctype": "Chart of Accounting",
					"accid": accid,
					"description": row["description"],
					"nature": row["nature"],
					"chartlevel": row["chartlevel"],
					"parentid": parent_link,
					"transflag": row.get("transflag", "Yes"),
				}
			).insert(ignore_permissions=True)
			created += 1
	return frappe.db.count("Chart of Accounting")


_ACCOUNT_PARA = {
	label: fieldname
	for label, fieldname in SETTING_FIELDS.items()
	if fieldname not in ("custom_ui_url", "bardana_store", "dust_item")
}


def seed_gl_parameter(*, dump_path: str | None = None) -> dict[str, str]:
	"""Link GL Parameter Single fields from Oracle PROJECT_PARA."""
	try:
		para = extract_project_para(dump_path)
	except FileNotFoundError:
		para = {}

	doc = frappe.get_single("GL Parameter")
	meta = frappe.get_meta("GL Parameter")
	for field in meta.get_link_fields():
		value = doc.get(field.fieldname)
		if value and not frappe.db.exists(field.options, value):
			doc.set(field.fieldname, None)

	linked: dict[str, str] = {}
	for label, fieldname in _ACCOUNT_PARA.items():
		accid = para.get(label)
		if not accid:
			continue
		acc_name = str(int(accid))
		if frappe.db.exists("Chart of Accounting", acc_name):
			doc.set(fieldname, acc_name)
			linked[fieldname] = acc_name

	if not doc.financial_year_from:
		doc.financial_year_from = "2025-07-01"
	if not doc.financial_year_to:
		doc.financial_year_to = "2026-06-30"
	doc.save(ignore_permissions=True)
	return linked


def seed_transaction_setup() -> None:
	"""Minimal Transaction Category + Transaction List for expense vouchers."""
	expense_acc = frappe.db.get_value(
		"Chart of Accounting", {"chartlevel": 5, "description": ["like", "%Exp%"]}, "name"
	) or frappe.db.get_value("Chart of Accounting", {"chartlevel": 5}, "name")

	if not frappe.db.exists("Transaction Category", "1"):
		frappe.get_doc(
			{
				"doctype": "Transaction Category",
				"tcat_id": 1,
				"description": "General Expense",
				"accid": expense_acc,
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Transaction List", "1"):
		frappe.get_doc(
			{
				"doctype": "Transaction List",
				"trans_id": 1,
				"description": "General Transaction",
				"tcat_id": "1",
			}
		).insert(ignore_permissions=True)


def seed_master_feeding_basics() -> dict:
	"""Oracle MasterFeeding — Company, City, Mill/Location, Department, Designation."""
	out: dict = {}

	if not frappe.db.count("Mill Information"):
		co = frappe.get_doc(
			{
				"doctype": "Mill Information",
				"short_name": "DEMO",
				"description": "Demo Mill Company",
				"address": "Demo Address",
			}
		).insert(ignore_permissions=True)
		out["company"] = co.name
	else:
		out["company"] = frappe.db.get_value("Mill Information", {}, "name")

	if not frappe.db.count("City Setup"):
		city = frappe.get_doc({"doctype": "City Setup", "cityname": "Demo City"}).insert(
			ignore_permissions=True
		)
		out["city"] = city.name
	else:
		out["city"] = frappe.db.get_value("City Setup", {}, "name")

	if not frappe.db.count("Location"):
		loc = frappe.get_doc(
			{
				"doctype": "Location",
				"description": "Demo Mill",
				"short_name": "DM",
				"company_id": out["company"],
				"cityid": out["city"],
				"address": "Demo Mill Address",
			}
		).insert(ignore_permissions=True)
		out["location"] = loc.name
	else:
		out["location"] = frappe.db.get_value("Location", {}, "name")

	if not frappe.db.count("Departments"):
		dept = frappe.get_doc({"doctype": "Departments", "description": "Administration"}).insert(
			ignore_permissions=True
		)
		out["department"] = dept.name
	else:
		out["department"] = frappe.db.get_value("Departments", {}, "name")

	if not frappe.db.count("Designation"):
		desig = frappe.get_doc({"doctype": "Designation", "description": "Staff"}).insert(
			ignore_permissions=True
		)
		out["designation"] = desig.name
	else:
		out["designation"] = frappe.db.get_value("Designation", {}, "name")

	return out


def seed_employee_setup() -> str | None:
	"""One demo employee so User Rights empno link validates."""
	if frappe.db.exists("Employee Setup", {"ename": "Demo Employee"}):
		return frappe.db.get_value("Employee Setup", {"ename": "Demo Employee"}, "name")

	basics = seed_master_feeding_basics()
	location = basics.get("location")
	if not location:
		return None

	dept = basics.get("department")
	desig = basics.get("designation")
	if not frappe.db.count("Employee Category"):
		frappe.get_doc({"doctype": "Employee Category", "description": "General"}).insert(
			ignore_permissions=True
		)
	ecat = frappe.db.get_value("Employee Category", {}, "name")
	doc = frappe.get_doc(
		{
			"doctype": "Employee Setup",
			"ename": "Demo Employee",
			"location_id": location,
			"deptid": dept,
			"desigid": desig,
			"ecatid": ecat,
			"salary": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def seed_menu() -> int:
	count = 0
	for row in MENU_ROWS:
		_upsert_doc("Menu", "menuid", row["menuid"], row)
		count += 1
	return count


def seed_modules() -> int:
	count = 0
	for row in all_module_rows():
		payload = {
			"menuid": row["menuid"],
			"nature": row.get("nature", "Assets"),
			"module": row["module"],
			"moduletype": row.get("moduletype", "F"),
			"runtimefile": row.get("runtimefile", ""),
			"no_of_days": row.get("no_of_days") or 0,
			"doctypeid": row.get("doctypeid") or "",
			"rep_allies": row.get("rep_allies") or "",
		}
		_upsert_doc("Module", "moduleid", row["moduleid"], payload)
		count += 1
	return count


def _default_module_permission_row(module_row: dict) -> dict:
	return {
		"moduleid": module_row["moduleid"],
		"module_name": module_row["module"],
		"user_level": "Level 1",
		"canview": 1,
		"canadd": 1,
		"canedit": 1,
		"candelete": 0,
		"cansubmit": 1,
		"canassign": 0,
		"canunsubmit": 1,
		"resaccess": 0,
	}


def seed_user_rights(*, erp_user: str = "client@millitrix.local") -> str:
	"""User Rights for client with full module access."""
	location = frappe.db.get_value("Location", {}, "name")
	if not location:
		frappe.throw("No Location master — create at least one Location first")

	empno = seed_employee_setup()
	userid = frappe.db.get_value("User", erp_user, "username") or erp_user.split("@")[0]

	if frappe.db.exists("User Rights", userid):
		doc = frappe.get_doc("User Rights", userid)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "User Rights",
				"userid": userid,
				"erp_user": erp_user,
				"location_id": location,
				"empno": empno,
				"username": userid,
				"activestatus": "Active",
				"get_all_modules": 1,
			}
		)

	doc.get_all_modules = 1
	doc.activestatus = "Active"
	if empno:
		doc.empno = empno

	if not doc.get_all_modules:
		existing = {int(row.moduleid) for row in doc.module_permissions or []}
		for module_row in all_module_rows():
			if module_row["moduleid"] in existing:
				continue
			doc.append("module_permissions", _default_module_permission_row(module_row))

	doc.save(ignore_permissions=True)
	frappe.cache.hdel("millitrix_user_permissions", f"mill_user::{erp_user}")
	return doc.name


def seed_demo_transactions() -> dict:
	"""Minimal SI + PNR sample docs for print/list UAT."""
	from frappe.utils import today

	loc = frappe.db.get_value("Location", {}, "name")
	store = frappe.db.get_value("Store Setup", {}, "name")
	item = frappe.db.get_value("Item Setup", {"name": ["like", "100%"]}, "name") or frappe.db.get_value(
		"Item Setup", {}, "name"
	)
	customer = frappe.db.get_value("Party", {"pcat_id": "13"}, "name") or frappe.db.get_value(
		"Party", {"pcat_id": ["!=", "12"]}, "name"
	)
	supplier = frappe.db.get_value("Party", {"pcat_id": "12"}, "name")
	broker = frappe.db.get_value("Party", {"pcat_id": "11"}, "name")
	bank = frappe.db.get_value("Bank Account", {}, "name")
	out: dict = {"skipped": False}

	if not all([loc, store, item, customer, supplier]):
		out["skipped"] = True
		return out

	if not frappe.db.count("Sales Invoice"):
		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"location_id": loc,
				"sodate": today(),
				"sotype": "Main Order",
				"itemcode": item,
				"customerid": customer,
				"brokerid": broker,
				"truckqty": 5,
				"weight": 5000,
				"rate": 5500,
				"status": "Initial",
			}
		)
		so.insert(ignore_permissions=True)
		so.submit()
		si = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"location_id": loc,
				"invdate": today(),
				"itemcode": item,
				"customerid": customer,
				"brokerid": broker,
				"kantatype": "Delivery Kanta",
				"brokery": "Not Paid",
				"borrow": "X Delivery",
				"amntby": "Mund",
				"details": [
					{
						"sonumber": so.name,
						"truckno": "DEMO-SI-1",
						"truckqty": 1,
						"delikanta": 500,
						"storeid": store,
						"rate": 5500,
						"biltyno": "SB1",
					}
				],
			}
		)
		si.insert(ignore_permissions=True)
		si.submit()
		out["sales_invoice"] = si.name
		out["sales_order"] = so.name

	pi = frappe.db.get_value("Purchase Invoice", {}, "name", order_by="creation desc")
	if pi and not frappe.db.count("Purchase Invoice Payment"):
		pip = frappe.get_doc(
			{
				"doctype": "Purchase Invoice Payment",
				"location_id": loc,
				"pnrdate": today(),
				"partyid": supplier,
				"pnrmode": "Cash",
				"amount": 1000,
				"narration": "Demo payment",
				"instruments": [{"pnrmode": "Cash", "amount": 1000}],
				"documents": [{"documentid": frappe.db.get_value("Purchase Invoice", pi, "purchinvno"), "amount": 1000}],
			}
		)
		try:
			pip.insert(ignore_permissions=True)
			pip.submit()
			out["purchase_invoice_payment"] = pip.name
		except Exception as exc:
			out["purchase_invoice_payment_error"] = str(exc)

	if bank and supplier and not frappe.db.count("Payment Voucher"):
		pv = frappe.get_doc(
			{
				"doctype": "Payment Voucher",
				"location_id": loc,
				"vouchdate": today(),
				"vouchmode": "Cash",
				"bankaccid": bank,
				"narration": "Demo CNB payment",
				"details": [{"accid": "1", "amount": 500, "detail": "Demo"}],
			}
		)
		try:
			pv.insert(ignore_permissions=True)
			pv.submit()
			out["payment_voucher"] = pv.name
		except Exception as exc:
			out["payment_voucher_error"] = str(exc)

	return out


def run(*, dump_path: str | None = None, force_coa: bool = False) -> dict:
	"""Main entry — bench execute millitrix.utils.dev_bootstrap.run"""
	if dump_path:
		resolve_dump_path(dump_path)

	frappe.flags.mute_emails = True
	result: dict = {}

	result["coa_count"] = seed_coa(dump_path=dump_path, force=force_coa)
	frappe.db.commit()
	result["gl_parameter"] = seed_gl_parameter(dump_path=dump_path)
	seed_transaction_setup()
	result["menu_count"] = seed_menu()
	result["module_count"] = seed_modules()
	result["master_feeding"] = seed_master_feeding_basics()
	result["user_rights"] = seed_user_rights()
	result["demo_transactions"] = seed_demo_transactions()
	frappe.db.commit()

	from millitrix.utils.client_access import _sync_client_millitrix_permissions

	_sync_client_millitrix_permissions()
	frappe.db.commit()
	result["ok"] = True
	return result
