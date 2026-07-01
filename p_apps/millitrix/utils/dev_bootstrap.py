
from __future__ import annotations
# Copyright (c) 2026, Millitrix and contributors
"""Dev/UAT site bootstrap — COA, GL Parameter, Menu, Module, User Rights."""

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

    doc = frappe.get_doc("GL Parameter")

    meta = frappe.get_meta("GL Parameter")
    for field in meta.get_link_fields():
        value = getattr(doc, field.fieldname, None)
        if value and not frappe.db.exists(field.options, value):
            setattr(doc, field.fieldname, None)

    linked: dict[str, str] = {}
    for label, fieldname in _ACCOUNT_PARA.items():
        accid = para.get(label)
        if not accid:
            continue

        acc_name = str(int(accid))
        if frappe.db.exists("Chart of Accounting", acc_name):
            setattr(doc, fieldname, acc_name)
            linked[fieldname] = acc_name

    if not getattr(doc, "financial_year_from", None):
        doc.financial_year_from = "2025-07-01"
    if not getattr(doc, "financial_year_to", None):
        doc.financial_year_to = "2026-06-30"

    doc.save(ignore_permissions=True)
    return linked
