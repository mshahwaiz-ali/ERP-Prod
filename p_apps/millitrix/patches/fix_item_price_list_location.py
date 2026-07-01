from __future__ import annotations
# Copyright (c) 2026, Millitrix and contributors
# Backfill empty location_id on forms that hide Location in the UI.

import frappe
from millitrix.utils.blueprint_form_rules import LOCATION_UI_HIDDEN_DOCTYPES
from millitrix.utils.erpnext_compat import get_session_location


def execute() -> None:
    default_location = get_session_location()

    if not default_location:
        locations = frappe.get_all("Location", pluck="name", limit=1, order_by="name asc")
        default_location = locations[0] if locations else None

    if not default_location:
        print("fix_item_price_list_location: no Location found, skipped")
        return

    total = 0

    for doctype in sorted(LOCATION_UI_HIDDEN_DOCTYPES):
        if not frappe.get_meta(doctype).has_field("location_id"):
            continue

        names = frappe.get_all(
            doctype,
            filters={"location_id": ("in", ("", None))},
            pluck="name",
        )

        for name in names:
            frappe.db.set_value(
                doctype,
                name,
                "location_id",
                default_location,
                update_modified=False,
            )

        if names:
            print(f"  {doctype}: {len(names)}")
            total += len(names)

    if total:
        pass  # safe mode

    print(f"fix_item_price_list_location: updated {total} rows -> {default_location}")
