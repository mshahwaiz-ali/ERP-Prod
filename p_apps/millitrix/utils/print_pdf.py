# Copyright (c) 2026, Millitrix and contributors
# Surface PDF errors instead of returning blank files when wkhtmltopdf is missing.

from __future__ import annotations

from pathlib import Path

import frappe
from frappe import _
from frappe.utils.print_format import download_multi_pdf as _frappe_download_multi_pdf

from millitrix.utils.pdf_setup import is_wkhtmltopdf_ready, wkhtmltopdf_status


def _wkhtmltopdf_install_command() -> str:
	script = Path(frappe.get_app_path("millitrix")) / "scripts" / "install_wkhtmltopdf.sh"
	return f"bash {script}"


@frappe.whitelist(allow_guest=False)
def download_multi_pdf(
	doctype: str,
	name: str,
	format: str | None = None,
	no_letterhead: int | None = None,
	letterhead: str | None = None,
	options: str | None = None,
	task_id: str | None = None,
):
	if not is_wkhtmltopdf_ready():
		status = wkhtmltopdf_status()
		script = _wkhtmltopdf_install_command()
		frappe.throw(
			_("Print PDF is unavailable: wkhtmltopdf is not installed. Run in terminal:<br><code>{0}</code><br>{1}").format(
				script, status.get("install_hint") or status.get("error") or ""
			),
			title=_("PDF Engine Missing"),
		)
	if task_id:
		from frappe.utils.print_format import download_multi_pdf_async

		return download_multi_pdf_async(
			doctype, name, format, bool(no_letterhead), letterhead, options
		)
	return _frappe_download_multi_pdf(
		doctype, name, format, bool(no_letterhead), letterhead, options
	)


@frappe.whitelist(allow_guest=False)
def download_pdf(
	doctype: str,
	name: str,
	format: str | None = None,
	doc: str | None = None,
	no_letterhead: int | None = None,
	language: str | None = None,
	letterhead: str | None = None,
	pdf_generator: str | None = None,
):
	if not is_wkhtmltopdf_ready():
		status = wkhtmltopdf_status()
		script = _wkhtmltopdf_install_command()
		frappe.throw(
			_("Print PDF is unavailable: wkhtmltopdf is not installed. Run in terminal:<br><code>{0}</code><br>{1}").format(
				script, status.get("install_hint") or status.get("error") or ""
			),
			title=_("PDF Engine Missing"),
		)
	from frappe.utils.print_format import download_pdf as _frappe_download_pdf

	return _frappe_download_pdf(
		doctype, name, format, doc, no_letterhead, language, letterhead, pdf_generator
	)


@frappe.whitelist(allow_guest=False)
def download_multi_pdf_async(
	doctype: str,
	name: str,
	format: str | None = None,
	no_letterhead: bool = False,
	letterhead: str | None = None,
	options: str | None = None,
):
	if not is_wkhtmltopdf_ready():
		status = wkhtmltopdf_status()
		script = _wkhtmltopdf_install_command()
		frappe.throw(
			_("Print PDF is unavailable: wkhtmltopdf is not installed. Run in terminal:<br><code>{0}</code><br>{1}").format(
				script, status.get("install_hint") or status.get("error") or ""
			),
			title=_("PDF Engine Missing"),
		)
	from frappe.utils.print_format import download_multi_pdf_async as _frappe_async

	return _frappe_async(doctype, name, format, no_letterhead, letterhead, options)
