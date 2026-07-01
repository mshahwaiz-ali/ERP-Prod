# Copyright (c) 2026, Millitrix and contributors
# Restrict desk access to local.mill + configured LAN IP on port 8000 only.

from __future__ import annotations

import frappe
from frappe import _

from millitrix.api.lan import DEFAULT_LOCAL_HOST, get_local_host, get_local_host_aliases

_LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


def _allowed_hosts() -> set[str]:
	cfg = frappe.get_site_config()
	hosts: set[str] = set()
	for local_host in get_local_host_aliases():
		if local_host:
			hosts.add(local_host)
	for alias in cfg.get("millitrix_local_aliases") or []:
		name = (alias or "").strip().lower()
		if name:
			hosts.add(name.split(":")[0])
	for domain in cfg.get("domains") or []:
		name = (domain or "").strip().lower()
		if name:
			hosts.add(name.split(":")[0])
	host_name = (cfg.get("host_name") or "").strip().lower()
	if host_name:
		hosts.add(host_name.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0])
	hosts.update(_LOOPBACK)
	return hosts


def _primary_host() -> str:
	return (get_local_host() or DEFAULT_LOCAL_HOST).strip().lower()


def validate_request_host() -> None:
	"""before_request — reject unknown Host headers while allowing local aliases."""
	if frappe.flags.in_import or frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if not getattr(frappe.local, "request", None):
		return

	host = (frappe.get_request_header("Host") or "").split(":")[0].strip().lower()
	if not host or host in _allowed_hosts():
		return

	allowed = sorted(h for h in _allowed_hosts() if h not in _LOOPBACK)
	frappe.respond_as_web_page(
		_("Millitrix Host Not Allowed"),
		_("Use <b>http://{0}:8000</b>. Allowed local aliases: {1}.<br><small>Blocked host: {2}</small>").format(
			_primary_host(),
			", ".join(allowed) or _primary_host(),
			host,
		),
		http_status_code=403,
	)
	raise frappe.PermissionError("Invalid host")
