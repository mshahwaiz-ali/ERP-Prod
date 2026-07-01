# Copyright (c) 2026, Millitrix and contributors
# Client login — Frappe default desk; access limited via roles + block_modules only.

from __future__ import annotations

import frappe

CLIENT_USERNAME = "client"
CLIENT_ROLE = "Millitrix Client"
MILLITRIX_MODULE = "Millitrix ERP"

FRAPPE_MODULES_TO_BLOCK = (
	"Automation",
	"Contacts",
	"Core",
	"Custom",
	"Desk",
	"Email",
	"Geo",
	"Integrations",
	"Printing",
	"Social",
	"Website",
	"Workflow",
)

ADMIN_SETUP_DOCTYPES_NO_DELETE = (
	"DocType",
	"DocType Layout",
	"Customize Form",
	"Custom Field",
	"Property Setter",
	"Role",
	"Role Profile",
	"Module Def",
	"Workspace",
	"Page",
	"Report",
	"Print Format",
	"System Settings",
	"Navbar Settings",
	"Global Search Settings",
	"User",
	"User Rights",
	"Module",
	"Menu",
	"Document Follow",
	"Notification Settings",
	"Access Log",
	"Error Log",
	"Scheduled Job Type",
	"Server Script",
	"Client Script",
)

# Millitrix setup screens — client may open lists but must not change definitions.
MILLITRIX_SETUP_READONLY = (
	"User Rights",
	"Module",
	"Menu",
	"Document Type",
)

CLIENT_DENIED_WRITE_DOCTYPES = frozenset(MILLITRIX_SETUP_READONLY + ADMIN_SETUP_DOCTYPES_NO_DELETE)
_WRITE_PTYPES = frozenset(
	{"write", "create", "delete", "submit", "cancel", "amend", "share", "import", "set_user_permissions"}
)
# When Millitrix Client Custom DocPerm exists, Frappe ignores standard DocPerm for that DocType.
# Administrator often has Millitrix Client role — admin desk roles need matching Custom DocPerm rows.
ADMIN_DESK_ROLES = ("System Manager", "Millitrix ERP Manager", "Millitrix ERP User")
ADMINISTRATOR_KEEP_ROLES = frozenset({"System Manager", "Millitrix ERP Manager"})


def is_restricted_desk_user(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user in ("Guest", "Administrator"):
		return False
	return CLIENT_ROLE in frappe.get_roles(user)


def sanitize_administrator_user() -> None:
	"""Keep Frappe built-in Administrator as full desk superuser — not Millitrix Client.

	There is no separate admin user to delete: User.name is always ``Administrator``.
	The username field (often ``admin``) is only the login alias.
	"""
	if not frappe.db.exists("User", "Administrator"):
		return

	for row in frappe.get_all(
		"Has Role",
		filters={"parent": "Administrator", "parenttype": "User"},
		fields=["name", "role"],
	):
		if row.role not in ADMINISTRATOR_KEEP_ROLES:
			frappe.db.delete("Has Role", row.name)

	for role in ADMINISTRATOR_KEEP_ROLES:
		if frappe.db.exists(
			"Has Role",
			{"parent": "Administrator", "parenttype": "User", "role": role},
		):
			continue
		frappe.get_doc(
			{
				"doctype": "Has Role",
				"parent": "Administrator",
				"parenttype": "User",
				"parentfield": "roles",
				"role": role,
			}
		).insert(ignore_permissions=True)

	frappe.db.set_value(
		"User",
		"Administrator",
		{
			"enabled": 1,
			"default_app": "",
			"search_bar": 1,
			"view_switcher": 1,
			"bulk_actions": 1,
		},
		update_modified=False,
	)
	frappe.db.delete("Block Module", {"parent": "Administrator", "parenttype": "User"})
	frappe.cache.hdel("roles", "Administrator")
	frappe.cache.hdel("user_doc", "Administrator")


def cleanup_extra_users() -> list[str]:
	"""Keep only Administrator + Millitrix client user."""
	keep = {"Guest", "Administrator"}
	client_name = frappe.db.get_value("User", {"username": CLIENT_USERNAME}, "name")
	if client_name:
		keep.add(client_name)

	removed: list[str] = []
	for name in frappe.get_all("User", pluck="name"):
		if name in keep:
			continue
		frappe.delete_doc("User", name, force=1, ignore_permissions=True)
		removed.append(name)

	if removed:
		frappe.db.commit()
	return removed


def ensure_client_role() -> str:
	if not frappe.db.exists("Role", CLIENT_ROLE):
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": CLIENT_ROLE,
				"desk_access": 1,
				"disabled": 0,
			}
		).insert(ignore_permissions=True)
	return CLIENT_ROLE


def _apply_blocked_modules(user) -> None:
	user.set("block_modules", [])
	for module in FRAPPE_MODULES_TO_BLOCK:
		user.append("block_modules", {"module": module})


def _grant_millitrix_user_role(user_name: str) -> None:
	role = "Millitrix ERP User"
	if not frappe.db.exists("Role", role):
		return
	user = frappe.get_doc("User", user_name)
	if any(r.role == role for r in user.roles):
		return
	user.append("roles", {"role": role})
	user.save(ignore_permissions=True)


def _ensure_seed_employee(location: str) -> str | None:
	employee = frappe.db.get_value("Employee Setup", {}, "name", order_by="name asc")
	if employee:
		return employee

	dept = frappe.db.get_value("Departments", {}, "name", order_by="name asc")
	desig = frappe.db.get_value("Designation", {}, "name", order_by="name asc")
	ecat = frappe.db.get_value("Employee Category", {}, "name", order_by="name asc")
	if not all((dept, desig, ecat)):
		return None

	from frappe.utils import today

	doc = frappe.get_doc(
		{
			"doctype": "Employee Setup",
			"location_id": location,
			"ename": "Millitrix Client",
			"deptid": dept,
			"desigid": desig,
			"ecatid": ecat,
			"salary": 0,
			"hiredate": today(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_seed_master() -> tuple[str | None, str | None]:
	location = frappe.db.get_value("Location", {}, "name", order_by="name asc")
	if not location:
		return None, None
	employee = _ensure_seed_employee(location)
	return location, employee


def _grant_client_module_permissions(user_rights_name: str) -> None:
	"""Oracle USERSPRIVILEGES — full Millitrix use, no delete / restricted reports."""
	from millitrix.utils.field_normalizers import is_yes

	doc = frappe.get_doc("User Rights", user_rights_name)
	by_module = {int(row.moduleid): row for row in (doc.module_permissions or []) if row.moduleid}
	changed = False

	for mod in frappe.get_all("Module", fields=["moduleid", "module"], order_by="moduleid asc"):
		moduleid = int(mod.moduleid)
		row = by_module.get(moduleid)
		if not row:
			row = doc.append("module_permissions", {})
			row.moduleid = moduleid
			row.module_name = mod.module
			row.user_level = "Level 1"
			by_module[moduleid] = row
			changed = True

		for field in ("canview", "canadd", "canedit", "cansubmit", "canassign", "canunsubmit"):
			if not is_yes(getattr(row, field, None)):
				row.set(field, "Y")
				changed = True
		if is_yes(row.candelete):
			row.candelete = "N"
			changed = True
		if is_yes(row.resaccess):
			row.resaccess = "N"
			changed = True

	if changed:
		doc.save(ignore_permissions=True)


def _clear_mill_user_cache(user_name: str) -> None:
	from millitrix.utils.user_permissions import clear_mill_user_cache

	clear_mill_user_cache(frappe._dict(erp_user=user_name))


def _ensure_user_rights(user_name: str) -> str | None:
	location, employee = _ensure_seed_master()
	if not location or not employee:
		frappe.log_error(
			title="Millitrix client user",
			message="Skipped User Rights — create Location + HR masters (Department, Designation, Category) first.",
		)
		return None

	user_doc = frappe.get_doc("User", user_name)
	existing = frappe.db.get_value("User Rights", {"erp_user": user_name}, "name")
	if existing:
		doc = frappe.get_doc("User Rights", existing)
		updated = False
		if not doc.location_id:
			doc.location_id = location
			updated = True
		if not doc.empno:
			doc.empno = employee
			updated = True
		if doc.activestatus not in ("Active", "Y"):
			doc.activestatus = "Active"
			updated = True
		if updated:
			doc.save(ignore_permissions=True)
		user_rights_name = doc.name
	else:
		doc = frappe.get_doc(
			{
				"doctype": "User Rights",
				"userid": user_doc.get("full_name") or CLIENT_USERNAME,
				"erp_user": user_name,
				"location_id": location,
				"empno": employee,
				"activestatus": "Active",
			}
		)
		doc.insert(ignore_permissions=True)
		user_rights_name = doc.name

	_grant_client_module_permissions(user_rights_name)
	_clear_mill_user_cache(user_name)
	return user_rights_name


def client_doctype_permission(doc, ptype="read", user=None, debug=False):
	"""Block client users from Frappe / Millitrix setup writes."""
	if not is_restricted_desk_user(user):
		return None
	doctype = doc if isinstance(doc, str) else getattr(doc, "doctype", None)
	if doctype in CLIENT_DENIED_WRITE_DOCTYPES and ptype in _WRITE_PTYPES:
		return False
	return None


def guard_user_rights_permission(doc, ptype="read", user=None, debug=False):
	result = client_doctype_permission(doc, ptype, user, debug)
	if result is False:
		return False
	from millitrix.utils.user_permissions import has_permission

	return has_permission(doc, ptype, user, debug)


def _remove_client_admin_custom_docperms() -> None:
	"""Drop Custom DocPerm rows that block Frappe admin doctypes for all users.

	When any Custom DocPerm exists on a DocType, Frappe ignores standard DocPerm for
	that DocType — a read=0 row for Millitrix Client therefore breaks Administrator
	routing to /app/doctype/* (Edit DocType / form builder).
	Client access is already enforced via block_modules on the client user.
	"""
	for doctype in ADMIN_SETUP_DOCTYPES_NO_DELETE:
		frappe.db.delete("Custom DocPerm", {"parent": doctype, "role": CLIENT_ROLE})


def _remove_custom_docperm(doctype: str, role: str) -> None:
	frappe.db.delete("Custom DocPerm", {"parent": doctype, "role": role})


def _remove_client_custom_docperm(doctype: str) -> None:
	_remove_custom_docperm(doctype, CLIENT_ROLE)


def _submittable_perm_flags(doctype: str) -> dict[str, int]:
	if frappe.get_meta(doctype).is_submittable:
		return {"submit": 1, "cancel": 1}
	return {"submit": 0, "cancel": 0}


def _upsert_custom_docperm(
	doctype: str,
	role: str,
	source: dict,
	*,
	overrides: dict | None = None,
) -> None:
	_remove_custom_docperm(doctype, role)
	values = {
		"doctype": "Custom DocPerm",
		"parent": doctype,
		"parenttype": "DocType",
		"parentfield": "permissions",
		"role": role,
		"permlevel": source.get("permlevel") or 0,
		"read": source.get("read") or 0,
		"write": source.get("write") or 0,
		"create": source.get("create") or 0,
		"delete": source.get("delete") or 0,
		"submit": source.get("submit") or 0,
		"cancel": source.get("cancel") or 0,
		"amend": source.get("amend") or 0,
		"report": source.get("report") or 0,
		"export": source.get("export") or 0,
		"import": source.get("import") or 0,
		"share": source.get("share") or 0,
		"print": source.get("print") or 0,
		"email": source.get("email") or 0,
		"select": source.get("select") or 0,
		"if_owner": source.get("if_owner") or 0,
	}
	if overrides:
		values.update(overrides)
	frappe.get_doc(values).insert(ignore_permissions=True)


def _upsert_client_custom_docperm(doctype: str, source: dict) -> None:
	overrides = {"delete": 0, **_submittable_perm_flags(doctype)}
	if doctype in MILLITRIX_SETUP_READONLY:
		overrides.update({"write": 0, "create": 0, "delete": 0})
	_upsert_custom_docperm(doctype, CLIENT_ROLE, source, overrides=overrides)


def _sync_admin_custom_docperms() -> None:
	"""Mirror standard DocPerm into Custom DocPerm for admin desk roles.

	Frappe drops standard DocPerm whenever any Custom DocPerm row exists on a DocType.
	Administrator inherits Millitrix Client, so without admin-role Custom DocPerm rows the
	desk hides Delete / Submit / Cancel even though server-side Administrator checks pass.
	"""
	doctypes = frappe.get_all(
		"Custom DocPerm",
		filters={"role": CLIENT_ROLE},
		pluck="parent",
		distinct=True,
	)
	delete_by_role = {
		"System Manager": 1,
		"Millitrix ERP Manager": 1,
		"Millitrix ERP User": 0,
	}
	for doctype in doctypes:
		sub_flags = _submittable_perm_flags(doctype)
		for role in ADMIN_DESK_ROLES:
			source_rows = frappe.get_all(
				"DocPerm",
				filters={"parent": doctype, "role": role},
				fields=["*"],
				limit=1,
			)
			if not source_rows:
				continue
			overrides = {**sub_flags, "delete": delete_by_role.get(role, source_rows[0].get("delete") or 0)}
			_upsert_custom_docperm(doctype, role, source_rows[0], overrides=overrides)


def _ensure_has_role(parent: str, parenttype: str, role: str, parentfield: str = "roles") -> None:
	if frappe.db.exists(
		"Has Role",
		{"parent": parent, "parenttype": parenttype, "role": role},
	):
		return
	frappe.get_doc(
		{
			"doctype": "Has Role",
			"parent": parent,
			"parenttype": parenttype,
			"parentfield": parentfield,
			"role": role,
		}
	).insert(ignore_permissions=True)


def _sync_client_millitrix_permissions() -> None:
	"""Millitrix Client gets ERP User desk access without Frappe admin or setup writes."""
	_remove_client_admin_custom_docperms()

	mill_doctypes = set(
		frappe.get_all("DocType", filters={"module": MILLITRIX_MODULE}, pluck="name")
	)
	mill_doctypes.update(MILLITRIX_SETUP_READONLY)

	for doctype in sorted(mill_doctypes):
		source_rows = frappe.get_all(
			"DocPerm",
			filters={"parent": doctype, "role": "Millitrix ERP User"},
			fields=["*"],
			limit=1,
		)
		if not source_rows:
			continue
		_upsert_client_custom_docperm(doctype, source_rows[0])

	for report in frappe.get_all("Report", filters={"module": MILLITRIX_MODULE}, pluck="name"):
		_ensure_has_role(report, "Report", CLIENT_ROLE)

	for page in frappe.get_all("Page", filters={"module": MILLITRIX_MODULE}, pluck="name"):
		_ensure_has_role(page, "Page", CLIENT_ROLE)

	_sync_admin_custom_docperms()


def _strip_extra_roles(user_name: str) -> None:
	"""Client login uses only Millitrix Client (+ Frappe automatic roles)."""
	user = frappe.get_doc("User", user_name)
	allowed = {CLIENT_ROLE, "All", "Guest", "Desk User"}
	roles = [row.role for row in user.roles]
	if set(roles) <= allowed and CLIENT_ROLE in roles:
		return
	user.roles = []
	for role in allowed:
		if role in roles or role == CLIENT_ROLE:
			user.append("roles", {"role": role})
	user.save(ignore_permissions=True)


def _lock_down_client_role_permissions() -> None:
	_remove_client_admin_custom_docperms()
	_sync_client_millitrix_permissions()


def ensure_client_user(password: str = "client@123") -> str:
	ensure_client_role()

	if frappe.db.exists("User", CLIENT_USERNAME):
		user = frappe.get_doc("User", CLIENT_USERNAME)
	elif frappe.db.exists("User", {"username": CLIENT_USERNAME}):
		user = frappe.get_doc("User", frappe.db.get_value("User", {"username": CLIENT_USERNAME}, "name"))
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"{CLIENT_USERNAME}@millitrix.local",
				"username": CLIENT_USERNAME,
				"first_name": "Millitrix",
				"last_name": "Client",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
		frappe.db.commit()
		user = frappe.get_doc("User", user.name)

	_ensure_user_rights(user.name)

	user.enabled = 1
	user.default_app = "millitrix"
	user.desk_theme = "Light"
	user.search_bar = 1
	user.view_switcher = 0
	user.bulk_actions = 0
	user.document_follow = 0
	_apply_blocked_modules(user)
	user.roles = []
	user.append("roles", {"role": CLIENT_ROLE})
	user.save(ignore_permissions=True)
	_strip_extra_roles(user.name)

	from frappe.utils.password import update_password

	update_password(user.name, password, logout_all_sessions=0)

	_lock_down_client_role_permissions()
	frappe.db.commit()
	return user.name


def _millitrix_search_doctypes() -> set[str]:
	return set(frappe.get_all("DocType", filters={"module": MILLITRIX_MODULE}, pluck="name"))


def _filter_client_boot_search(bootinfo) -> None:
	"""Awesome Bar — only Millitrix ERP doctypes/reports/workspaces (no Frappe admin)."""
	mill_dts = _millitrix_search_doctypes()
	user = bootinfo.get("user") or {}

	for key in (
		"can_read",
		"can_create",
		"can_search",
		"can_write",
		"can_get_report",
		"all_read",
		"can_submit",
		"can_cancel",
		"can_delete",
		"can_export",
		"can_print",
		"can_email",
	):
		if user.get(key):
			user[key] = sorted(dt for dt in user[key] if dt in mill_dts)

	reports = user.get("all_reports") or {}
	user["all_reports"] = {
		name: rpt for name, rpt in reports.items() if rpt.get("ref_doctype") in mill_dts
	}

	mill_workspaces = set(
		frappe.get_all("Workspace", filters={"module": MILLITRIX_MODULE}, pluck="name")
	)
	if bootinfo.get("allowed_workspaces"):
		bootinfo["allowed_workspaces"] = [
			ws
			for ws in bootinfo["allowed_workspaces"]
			if ws.get("name") in mill_workspaces or ws.get("title") in mill_workspaces
		]

	if bootinfo.get("page_info"):
		bootinfo["page_info"] = {
			name: page
			for name, page in bootinfo["page_info"].items()
			if "millitrix" in (page.get("route") or name).lower()
		}

	if bootinfo.get("dashboards") is not None:
		bootinfo["dashboards"] = [
			d for d in bootinfo["dashboards"] if d.get("module") == MILLITRIX_MODULE
		]

	bootinfo["millitrix_client_search"] = True


def extend_bootinfo_for_client(bootinfo):
	if is_restricted_desk_user():
		_filter_client_boot_search(bootinfo)


def boot_session(bootinfo):
	user = frappe.session.user
	if not is_restricted_desk_user(user):
		return
	# Standard Frappe boot flags only — no custom desk UI.
	bootinfo["hide_app_switcher"] = True
	bootinfo["disable_system_info"] = True
	_filter_client_boot_search(bootinfo)
