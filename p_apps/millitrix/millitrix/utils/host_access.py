# Copyright (c) 2026, Millitrix and contributors
# Restrict desk access to millitrix.local + configured LAN IP on port 8000 only.

from __future__ import annotations

import frappe

from millitrix.api.lan import get_local_host

_LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


def _allowed_hosts() -> set[str]:
	cfg = frappe.get_site_config()
	hosts: set[str] = set()
	local_host = (get_local_host() or "millitrix.local").strip().lower()
	if local_host:
		hosts.add(local_host)
	for domain in cfg.get("domains") or []:
		name = (domain or "").strip().lower()
		if name:
			hosts.add(name.split(":")[0])
	host_name = (cfg.get("host_name") or "").strip().lower()
	if host_name:
		hosts.add(host_name.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0])
	hosts.update(_LOOPBACK)
	return hosts


def validate_request_host() -> None:
	"""before_request — reject unknown Host headers (e.g. local.millitrix)."""
	if frappe.flags.in_import or frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if not getattr(frappe.local, "request", None):
		return

	host = (frappe.get_request_header("Host") or "").split(":")[0].strip().lower()
	if not host or host in _allowed_hosts():
		return

	allowed = sorted(h for h in _allowed_hosts() if h not in _LOOPBACK)
	frappe.respond_as_web_page(
		"Access Denied",
		f"Use <b>http://{get_local_host()}:8000</b>"
		+ (f" or <b>http://&lt;LAN-IP&gt;:8000</b>" if allowed else "")
		+ f".<br><small>Blocked host: {host}</small>",
		http_status_code=403,
	)
	raise frappe.PermissionError("Invalid host")
