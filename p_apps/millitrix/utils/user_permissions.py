# Copyright (c) 2026, Millitrix and contributors
# Blueprint Section 10 — Oracle USERSPRIVILEGES enforcement

from __future__ import annotations

import frappe
from frappe import _

from millitrix.utils.doctype_ids import UNSUBMIT_DOCUMENT

BYPASS_ROLES = ("Administrator", "System Manager", "Millitrix ERP Manager")

PTYPE_FIELD_MAP = {
	"read": "canview",
	"select": "canview",
	"print": "canview",
	"email": "canview",
	"report": "canview",
	"export": "canview",
	"share": "canview",
	"create": "canadd",
	"write": "canedit",
	"delete": "candelete",
	"submit": "cansubmit",
	"cancel": "canunsubmit",
	"amend": "canedit",
}

SUBMITTABLE_DOCTYPES = [
	"In Out Gate Pass",
	"Opening Stock",
	"Closing Stock",
	"Stock Adjustment",
	"Stock Transfer Note",
	"Purchase Order",
	"PO Cancellation",
	"Purchase Invoice",
	"Purchase Return",
	"Purchase Other Bill",
	"Purchase Return Other Bill",
	"Sales Order",
	"SO Cancellation",
	"Sales Invoice",
	"Sales Return",
	"Sales Other Bill",
	"Sales Return Other Bill",
	"Voucher Transaction",
	"Advance PNR",
	"Advance Payment",
	"Advance Receipt",
	"Purchase Invoice Payment",
	"Sales Invoice Receipt",
	"Broker Invoice Payment",
	"Payable Discount Note",
	"Receivable Discount Note",
	"Payment Voucher",
	"Receipt Voucher",
	"Expense Voucher",
	"Party Payment Voucher",
	"Party Receipt Voucher",
	"Paid Advance Adjustment",
	"Received Advance Adjustment",
	"Payment and Receipt Voucher",
	"Cash and Bank Voucher",
	"Employee Payment Voucher",
	"Employee Receipt Voucher",
	"Closing and Adjustment Entries",
	"Accounts Opening",
	"Un-Submit Documents",
	"Crashing Refine",
	"PaySlip",
	"Advance Adjustment",
	"Payment By Hawala",
	"Party Gross Margin",
	"Pay Salary Increment",
]

PERMISSION_DOCTYPES = sorted(
	set(
		SUBMITTABLE_DOCTYPES
		+ [
			"User Rights",
			"Module",
			"Menu",
			"Party",
			"Item Setup",
			"Chart of Accounting",
			"Employee Setup",
			"Store Setup",
			"Report Parameter",
			"Stock In Hand",
		]
	)
)

STORE_SCOPE_FIELDS = ("storeid", "fromstoreid", "tostoreid")


def _is_yes(value) -> bool:
	from millitrix.utils.field_normalizers import is_yes

	return is_yes(value)


def admin_only_mode_enabled() -> bool:
	return _is_yes(frappe.conf.get("millitrix_admin_only", 1))


def is_admin_user(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(set(frappe.get_roles(user)) & set(BYPASS_ROLES))


def admin_only_blocks_user(user: str | None = None) -> bool:
	user = user or frappe.session.user
	return user != "Guest" and admin_only_mode_enabled() and not is_admin_user(user)


def bypasses_mill_permissions(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Guest":
		return True
	if is_admin_user(user):
		return True
	return False


def get_mill_user(user: str | None = None) -> frappe._dict | None:
	user = user or frappe.session.user
	if admin_only_blocks_user(user):
		return None
	if user in ("Guest", "Administrator"):
		return None
	cache_key = f"mill_user::{user}"
	cached = frappe.cache.hget("millitrix_user_permissions", cache_key)
	if cached:
		return frappe.get_doc("User Rights", cached)
	if cached == "":
		return None

	row = frappe.db.get_value(
		"User Rights",
		{"erp_user": user, "activestatus": ["in", ["Y", "Active"]]},
		["name", "userid", "location_id"],
		as_dict=True,
	)
	if not row:
		frappe.cache.hset("millitrix_user_permissions", cache_key, "")
		return None

	doc = frappe.get_doc("User Rights", row.name)
	frappe.cache.hset("millitrix_user_permissions", cache_key, doc.name)
	return doc


def _missing_user_rights_message(user: str | None = None) -> str:
        user = user or frappe.session.user
        if admin_only_mode_enabled():
                return _("Millitrix is configured for admin-only access. Login as Administrator or a System Manager.")
        return _("User Rights are not configured for ERP user {0}").format(user)


def _deny_missing_user_rights(user: str | None = None):
        frappe.throw(_missing_user_rights_message(user), frappe.PermissionError)


def _is_protected_doctype(doctype: str | None) -> bool:
        return bool(doctype and doctype in PERMISSION_DOCTYPES)


def require_mill_user_for_doctype(doctype: str | None, user: str | None = None):
        """Fail closed for protected Millitrix DocTypes when User Rights are missing."""
        if bypasses_mill_permissions(user):
                return None

        mill_user = get_mill_user(user)
        if mill_user:
                return mill_user

        if _is_protected_doctype(doctype):
                _deny_missing_user_rights(user)

        return None


def get_user_locations(mill_user) -> list[str]:
	if not mill_user:
		return []
	locations = [row.location_id for row in (mill_user.user_locations or []) if row.location_id]
	if not locations and mill_user.location_id:
		locations = [mill_user.location_id]
	return locations


def clear_mill_user_cache(doc, method=None):
	"""Drop cached User Rights after privilege / store changes."""
	if getattr(doc, "erp_user", None):
		frappe.cache.hdel("millitrix_user_permissions", f"mill_user::{doc.erp_user}")


def resolve_store_name(storeid_value) -> str | None:
	"""Map Oracle USER_STORES.storeid (int Data) to Store Setup.name."""
	if storeid_value in (None, ""):
		return None
	raw = str(storeid_value).strip()
	if frappe.db.exists("Store Setup", raw):
		return raw
	try:
		return frappe.db.get_value("Store Setup", {"storeid": int(raw)}, "name")
	except (TypeError, ValueError):
		return None


def get_user_stores(mill_user) -> list[str]:
	"""Allowed stores when USER_STORES rows exist (Oracle data scope)."""
	if not mill_user or not mill_user.user_stores:
		return []
	stores: list[str] = []
	for row in mill_user.user_stores:
		name = resolve_store_name(row.storeid)
		if name and name not in stores:
			stores.append(name)
	return stores


def get_default_store(mill_user) -> str | None:
	if not mill_user:
		return None
	for row in mill_user.user_stores or []:
		if _is_yes(row.default_store):
			return resolve_store_name(row.storeid)
	stores = get_user_stores(mill_user)
	return stores[0] if len(stores) == 1 else None


def collect_stores_from_doc(doc) -> set[str]:
	stores: set[str] = set()
	meta = frappe.get_meta(doc.doctype)
	for field in STORE_SCOPE_FIELDS:
		if meta.has_field(field):
			value = getattr(doc, field, None)
			if value:
				stores.add(str(value))
	for table in meta.get_table_fields():
		for row in doc.get(table.fieldname) or []:
			for field in STORE_SCOPE_FIELDS:
				value = getattr(row, field, None)
				if value:
					stores.add(str(value))
	return stores


def get_module_id_for_doctype(doctype: str) -> int | None:
	moduleid = frappe.db.get_value("Module", {"doctypeid": doctype, "moduletype": "F"}, "moduleid")
	if moduleid:
		return int(moduleid)
	if doctype == UNSUBMIT_DOCUMENT:
		moduleid = frappe.db.get_value(
			"Module",
			{"runtimefile": ["like", "%UnSubmit%"], "moduletype": "F"},
			"moduleid",
		)
		if moduleid:
			return int(moduleid)
	return None


def get_module_permission(mill_user, moduleid: int) -> frappe._dict | None:
	for row in mill_user.module_permissions or []:
		if int(row.moduleid) == int(moduleid):
			return row
	return None


def _permission_field_for(ptype: str) -> str | None:
	return PTYPE_FIELD_MAP.get(ptype)


def has_module_access(mill_user, doctype: str, ptype: str = "read") -> bool | None:
	"""Return True/False when Mill permissions apply; None if module is not mapped."""
	if _is_yes(getattr(mill_user, "get_all_modules", None)):
		return True

	moduleid = get_module_id_for_doctype(doctype)
	if not moduleid:
		return None

	perm = get_module_permission(mill_user, moduleid)
	if not perm:
		return False

	field = _permission_field_for(ptype)
	if not field:
		return None
	return _is_yes(getattr(perm, field, None))


def has_permission(doc, ptype="read", user=None, debug=False):
	"""Deny access when Oracle-style module permissions block the action."""
	if bypasses_mill_permissions(user):
		return None
	if admin_only_blocks_user(user):
		return False

	mill_user = get_mill_user(user)
	if not mill_user:
	        if _is_protected_doctype(doc.doctype):
	                return False
	        return None

	result = has_module_access(mill_user, doc.doctype, ptype)
	if result is False:
		return False

	if ptype == "report" and result is not False:
		moduleid = get_module_id_for_doctype(doc.doctype)
		if moduleid:
			perm = get_module_permission(mill_user, moduleid)
			if perm and _is_yes(perm.resaccess):
				return False

	return None


def get_permission_query_conditions(user, doctype=None):
	if bypasses_mill_permissions(user):
		return ""
	if admin_only_blocks_user(user):
		return "1=0" if doctype and _is_protected_doctype(doctype) else ""

	mill_user = get_mill_user(user)
	if not doctype:
	        return ""
	if not mill_user:
	        if _is_protected_doctype(doctype):
	                return "1=0"
	        return ""

	meta = frappe.get_meta(doctype)
	conditions: list[str] = []

	if meta.has_field("location_id"):
		locations = get_user_locations(mill_user)
		if locations:
			escaped = ", ".join(frappe.db.escape(loc) for loc in locations)
			conditions.append(f"`tab{doctype}`.location_id in ({escaped})")

	if meta.has_field("storeid"):
		stores = get_user_stores(mill_user)
		if stores:
			escaped = ", ".join(frappe.db.escape(store) for store in stores)
			conditions.append(f"`tab{doctype}`.storeid in ({escaped})")

	return " and ".join(conditions)


def validate_location_access(doc, user=None):
	if bypasses_mill_permissions(user):
		return

	mill_user = get_mill_user(user)
	if not mill_user:
	        _deny_missing_user_rights(user)
	        return

	location = getattr(doc, "location_id", None)
	if not location:
		return

	allowed = get_user_locations(mill_user)
	if allowed and location not in allowed:
		frappe.throw(
			_("You do not have access to location {0}").format(location),
			frappe.PermissionError,
		)


def validate_store_access(doc, user=None):
	if bypasses_mill_permissions(user):
		return

	mill_user = get_mill_user(user)
	if not mill_user:
	        _deny_missing_user_rights(user)
	        return

	allowed = get_user_stores(mill_user)
	if not allowed:
		return

	for store in collect_stores_from_doc(doc):
		if store not in allowed:
			frappe.throw(
				_("You do not have access to store {0}").format(store),
				frappe.PermissionError,
			)


def _report_name_variants(report_name: str) -> set[str]:
	variants = {report_name}
	if report_name:
		variants.add(report_name.replace("_", " "))
		variants.add(report_name.replace("_", ""))
	return {value for value in variants if value}


def find_report_module(report_name: str) -> frappe._dict | None:
	for field in ("rep_allies", "runtimefile", "module"):
		for value in _report_name_variants(report_name):
			row = frappe.db.get_value(
				"Module",
				{"moduletype": "R", field: value},
				["name", "moduleid", "parentid", "module", "rep_allies"],
				as_dict=True,
			)
			if row:
				return row
	return None


def has_mill_report_access(mill_user, report_name: str) -> bool | None:
	"""Return True/False when Mill report rules apply; None if unmapped."""
	if _is_yes(getattr(mill_user, "get_all_modules", None)):
		return True

	report_module = find_report_module(report_name)
	if report_module:
		moduleid = report_module.get("moduleid") or report_module.get("name")
		perm = get_module_permission(mill_user, int(moduleid))
		if not perm or not _is_yes(perm.canview):
			return False
		if _is_yes(perm.resaccess):
			return False
		return True

	allied_forms = frappe.get_all(
		"Module",
		filters={"moduletype": "F", "rep_allies": report_name},
		fields=["moduleid"],
	)
	if not allied_forms:
		return None

	allowed = False
	for form_module in allied_forms:
		perm = get_module_permission(mill_user, form_module.moduleid)
		if not perm:
			continue
		if _is_yes(perm.resaccess):
			return False
		if _is_yes(perm.canview):
			allowed = True

	return allowed if allowed else False


def has_report_permission(doc, ptype="read", user=None, debug=False):
	if bypasses_mill_permissions(user):
		return None
	if admin_only_blocks_user(user):
		return False

	mill_user = get_mill_user(user)
	if not mill_user:
		return None

	if getattr(doc, "doctype", None) != "Report":
		return None

	result = has_mill_report_access(mill_user, doc.name)
	if result is False:
		return False
	return None


def assert_report_access(report_name: str, user=None):
	"""Guard script report execute() when Report DocType permission is bypassed."""
	if bypasses_mill_permissions(user):
		return
	if admin_only_blocks_user(user):
	        frappe.throw(_missing_user_rights_message(user), frappe.PermissionError)
	        return

	mill_user = get_mill_user(user)
	if not mill_user:
	        _deny_missing_user_rights(user)
	        return

	result = has_mill_report_access(mill_user, report_name)
	if result is False:
		frappe.throw(
			_("You do not have permission to run report {0}").format(report_name),
			frappe.PermissionError,
		)


def apply_user_store_filters(filters: dict | None, user=None) -> dict:
	"""Scope stock-style report filters to USER_STORES."""
	filters = dict(filters or {})
	if bypasses_mill_permissions(user):
		return filters
	if admin_only_blocks_user(user):
		frappe.throw(_missing_user_rights_message(user), frappe.PermissionError)

	mill_user = get_mill_user(user)
	allowed = get_user_stores(mill_user)
	if not allowed:
		return filters

	selected = filters.get("storeid")
	if selected and selected not in allowed:
		frappe.throw(
			_("You do not have access to store {0}").format(selected),
			frappe.PermissionError,
		)
	if not selected:
		if len(allowed) == 1:
			filters["storeid"] = allowed[0]
		else:
			filters["_allowed_stores"] = allowed
	return filters


def check_submit_permission(doc, method=None):
	if bypasses_mill_permissions():
		return

	mill_user = get_mill_user()
	if not mill_user:
	        _deny_missing_user_rights()
	        return

	validate_location_access(doc)
	validate_store_access(doc)
	result = has_module_access(mill_user, doc.doctype, "submit")
	if result is False:
		frappe.throw(
			_("You do not have permission to submit {0}").format(doc.doctype),
			frappe.PermissionError,
		)


def check_cancel_permission(doc, method=None):
	if bypasses_mill_permissions():
		return

	mill_user = get_mill_user()
	if not mill_user:
	        _deny_missing_user_rights()
	        return

	result = has_module_access(mill_user, doc.doctype, "cancel")
	if result is False:
		frappe.throw(
			_("You do not have permission to cancel {0}").format(doc.doctype),
			frappe.PermissionError,
		)


def check_unsubmit_permission(user=None):
	if bypasses_mill_permissions(user):
		return

	mill_user = get_mill_user(user)
	if not mill_user:
	        _deny_missing_user_rights(user)
	        return

	moduleid = get_module_id_for_doctype(UNSUBMIT_DOCUMENT)
	if not moduleid:
		return

	perm = get_module_permission(mill_user, moduleid)
	if perm and not _is_yes(perm.canunsubmit):
		frappe.throw(_("You do not have permission to unsubmit documents"), frappe.PermissionError)


def validate_doc_access(doc, method=None):
	"""Validate write/create against module permissions and location scope."""
	if bypasses_mill_permissions():
		return

	mill_user = get_mill_user()
	if not mill_user:
	        _deny_missing_user_rights()
	        return

	validate_location_access(doc)
	validate_store_access(doc)

	if doc.is_new():
		ptype = "create"
	elif doc.docstatus == 0:
		ptype = "write"
	else:
		return

	result = has_module_access(mill_user, doc.doctype, ptype)
	if result is False:
		frappe.throw(
			_("You do not have permission to {0} {1}").format(ptype, doc.doctype),
			frappe.PermissionError,
		)
