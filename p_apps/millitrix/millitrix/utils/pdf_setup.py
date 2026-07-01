# Copyright (c) 2026, Millitrix and contributors
# PDF generation checks — blank PDFs usually mean wkhtmltopdf is missing.

from __future__ import annotations

import subprocess

import frappe


def is_wkhtmltopdf_ready() -> bool:
	try:
		from frappe.utils.pdf import is_wkhtmltopdf_valid

		return bool(is_wkhtmltopdf_valid())
	except Exception:
		return False


def wkhtmltopdf_status() -> dict:
	ok = is_wkhtmltopdf_ready()
	version = ""
	error = ""
	try:
		version = subprocess.check_output(["wkhtmltopdf", "--version"], stderr=subprocess.STDOUT, text=True).strip()
	except (OSError, subprocess.CalledProcessError) as exc:
		error = str(exc) or "wkhtmltopdf not found"
	return {
		"ok": ok,
		"version": version,
		"error": error,
		"install_hint": (
			"Install patched wkhtmltopdf 0.12.6 (must include qt): "
			"https://github.com/wkhtmltopdf/packaging/releases"
		),
	}


def ensure_wkhtmltopdf_or_warn() -> None:
	if is_wkhtmltopdf_ready():
		return
	status = wkhtmltopdf_status()
	frappe.log_error(
		title="Millitrix PDF: wkhtmltopdf missing",
		message=status.get("error") or status.get("install_hint"),
	)
	print("WARNING: wkhtmltopdf missing — print PDF will be blank. See Error Log / millitrix.utils.pdf_setup")


def run() -> dict:
	"""bench execute millitrix.utils.pdf_setup.run"""
	return wkhtmltopdf_status()
