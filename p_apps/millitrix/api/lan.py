# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import socket

import frappe
from frappe.installer import update_site_config

DEFAULT_LOCAL_HOST = "millitrix.local"
LOCAL_HOST_ALIASES = ("millitrix.local", "local.mill")
LOGO_PATH = "/assets/millitrix/images/millitrix-logo.svg"


def _local_ipv4() -> str | None:
	"""Current LAN IP (private ranges first — same logic as sample mill-erp.sh)."""
	import re
	import subprocess

	private = re.compile(r"^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)")
	try:
		out = subprocess.check_output(["hostname", "-I"], text=True, stderr=subprocess.DEVNULL).strip()
		for ip in out.split():
			if private.match(ip):
				return ip
		for ip in out.split():
			if not ip.startswith("127."):
				return ip
	except (OSError, subprocess.CalledProcessError):
		pass

	try:
		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			sock.connect(("8.8.8.8", 80))
			ip = sock.getsockname()[0]
			if not ip.startswith("127."):
				return ip
	except OSError:
		pass
	return None


def get_local_host() -> str:
	return (frappe.conf.get("millitrix_local_host") or DEFAULT_LOCAL_HOST).strip()


def get_local_host_aliases() -> list[str]:
	hosts = [get_local_host(), *LOCAL_HOST_ALIASES]
	out: list[str] = []
	for host in hosts:
		host = (host or "").strip().lower()
		if host and host not in out:
			out.append(host)
	return out


def _url(host: str, port: int, path: str = "") -> str:
	path = path if path.startswith("/") else f"/{path}" if path else ""
	return f"http://{host}:{port}{path}"


def ensure_lan_hostnames() -> dict:
	"""Register local.mill + current LAN IP on site (other devices use IP only)."""
	local_host = get_local_host()
	ip = _local_ipv4()
	site_config = frappe.get_site_config()
	domains = set(site_config.get("domains") or [])

	# Drop stale IPs and any legacy LAN hostnames.
	stale = {d for d in domains if d.replace(".", "").isdigit() or d in ("erp.mill", "erp.local")}
	domains -= stale
	domains.update(get_local_host_aliases())
	if ip:
		domains.add(ip)
	domains.discard("")

	update_site_config("domains", sorted(domains), validate=False)
	update_site_config("millitrix_local_host", local_host, validate=False)
	update_site_config("millitrix_local_aliases", get_local_host_aliases(), validate=False)
	update_site_config("millitrix_admin_only", int(frappe.conf.get("millitrix_admin_only", 1)), validate=False)
	port = int(frappe.conf.get("webserver_port") or 8000)
	update_site_config("host_name", f"http://{local_host}:{port}", validate=False)

	# Remove legacy keys from site_config.json
	site_path = frappe.get_site_path("site_config.json")
	try:
		import json
		from pathlib import Path

		cfg_path = Path(site_path)
		if cfg_path.exists():
			cfg = json.loads(cfg_path.read_text())
			for key in ("millitrix_lan_host",):
				cfg.pop(key, None)
			cfg_path.write_text(json.dumps(cfg, indent=1) + "\n")
	except OSError:
		pass

	# frappe.db.commit()  # DISABLED SAFE MODE
	return {"local_host": local_host, "ip": ip, "domains": sorted(domains)}


def _is_trusted_server_request() -> bool:
	"""LAN details are only exposed on the server login host (local.mill / localhost)."""
	host = (frappe.get_request_header("Host") or "").split(":")[0].strip().lower()
	return host in {*get_local_host_aliases(), "localhost", "127.0.0.1"}


@frappe.whitelist(allow_guest=True)
def get_lan_access():
	"""LAN URL for other devices — direct IP only on trusted server login host."""
	if not _is_trusted_server_request():
		return {
			"enabled": False,
			"port": int(frappe.conf.get("webserver_port") or 8000),
			"ip": None,
			"local_host": get_local_host(),
			"local_login_url": None,
			"ip_login_url": None,
			"network_login_url": None,
		}

	port = int(frappe.conf.get("webserver_port") or 8000)
	ip = _local_ipv4()
	local_host = get_local_host()

	return {
		"enabled": bool(frappe.conf.get("lan_access_enabled", 1)),
		"port": port,
		"ip": ip,
		"local_host": local_host,
		"local_login_url": _url(local_host, port, "/login"),
		"ip_login_url": _url(ip, port, "/login") if ip else None,
		"network_login_url": _url(ip, port, "/login") if ip else None,
	}
