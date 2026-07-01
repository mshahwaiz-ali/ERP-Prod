app_name = "millitrix"
app_title = "Millitrix"
app_publisher = "Millitrix"
app_description = "Millitrix custom app"
app_email = "dev@millitrix.local"
app_license = "MIT"

after_install = "millitrix.install.after_install"
after_migrate = [
	"millitrix.patches.migrate_settings.apply",
	"millitrix.patches.set_default_print_formats.execute",
	"millitrix.patches.sync_workspaces.execute",
	"millitrix.patches.setup_client_access.execute",
	"millitrix.patches.setup_branding.execute",
	"millitrix.patches.setup_lan_hostnames.execute",
	"millitrix.patches.configure_parent_list_views.execute",
	"millitrix.patches.ensure_premium_list_view_settings.execute",
	"millitrix.patches.backfill_list_summary_fields.execute",
	"millitrix.utils.pdf_setup.ensure_wkhtmltopdf_or_warn",
]

app_logo_url = "/assets/millitrix/images/millitrix-logo.svg"

extend_bootinfo = [
	"millitrix.utils.branding.extend_bootinfo",
	"millitrix.utils.client_access.extend_bootinfo_for_client",
]

app_include_js = [
	"/assets/millitrix/js/millitrix_number_format.js",
	"/assets/millitrix/js/millitrix_brand.js",
	"/assets/millitrix/js/millitrix_client_desk.js",
	"/assets/millitrix/js/millitrix_child_table.js",
	"/assets/millitrix/js/millitrix_form_links.js",
	"/assets/millitrix/js/millitrix_party_list.js",
	"/assets/millitrix/js/millitrix_list_view.js",
	"/assets/millitrix/js/millitrix_premium_lists.js",
	"/assets/millitrix/js/millitrix_list_filters.js",
	"/assets/millitrix/js/millitrix_stock_forms.js",
	"/assets/millitrix/js/millitrix_invoice_form.js",
	"/assets/millitrix/js/millitrix_form_save.js",
	"/assets/millitrix/js/millitrix_order_form.js",
	"/assets/millitrix/js/millitrix_purchase_return_form.js",
	"/assets/millitrix/js/millitrix_sales_return_form.js",
	"/assets/millitrix/js/millitrix_other_bill_form.js",
	"/assets/millitrix/js/millitrix_knockoff_form.js",
	"/assets/millitrix/js/millitrix_pnr_invoice_form.js",
	"/assets/millitrix/js/millitrix_discount_note_form.js",
	"/assets/millitrix/js/millitrix_advance_pnr.js",
	"/assets/millitrix/js/millitrix_voucher_detail_form.js",
	"/assets/millitrix/js/millitrix_employee_voucher_form.js",
	"/assets/millitrix/js/millitrix_party_voucher_form.js",
	"/assets/millitrix/js/millitrix_cnb_general_form.js",
	"/assets/millitrix/js/millitrix_hawala_form.js",
	"/assets/millitrix/js/millitrix_report_defaults.js",
	"/assets/millitrix/js/millitrix_report_links.js",
	"/assets/millitrix/js/millitrix_default_dates.js",
	"/assets/millitrix/js/millitrix_unsubmit_form.js",
	"/assets/millitrix/js/millitrix_para_form.js",
	"/assets/millitrix/js/millitrix_posted_lock.js",
	"/assets/millitrix/js/millitrix_duplicate_autoname.js",
]

app_include_css = [
	"/assets/millitrix/css/millitrix_brand.css",
	"/assets/millitrix/css/millitrix_child_table.css",
	"/assets/millitrix/css/millitrix_form.css",
	"/assets/millitrix/css/millitrix_list.css",
	"/assets/millitrix/css/millitrix_report.css",
]

web_include_js = [
	"/assets/millitrix/js/millitrix_login_lan.js",
]

web_include_css = [
	"/assets/millitrix/css/millitrix_brand.css",
	"/assets/millitrix/css/millitrix_login_lan.css",
]

boot_session = "millitrix.utils.client_access.boot_session"

before_request = ["millitrix.utils.host_access.validate_request_host"]

override_whitelisted_methods = {
	"frappe.utils.print_format.download_multi_pdf": "millitrix.utils.print_pdf.download_multi_pdf",
	"frappe.utils.print_format.download_multi_pdf_async": "millitrix.utils.print_pdf.download_multi_pdf_async",
	"frappe.utils.print_format.download_pdf": "millitrix.utils.print_pdf.download_pdf",
}

add_to_apps_screen = [
	{
		"name": "millitrix",
		"logo": "/assets/millitrix/images/millitrix-logo.svg",
		"title": "Millitrix",
		"route": "/app/millitrix",
	}
]

_erpnext_compat = "millitrix.utils.erpnext_compat.set_posting_date"

doc_events = {
	"In Out Gate Pass": {
		"validate": [_erpnext_compat, "millitrix.stock.gate_pass.validate"],
		"on_submit": "millitrix.stock.gate_pass.on_submit",
		"on_cancel": "millitrix.stock.gate_pass.on_cancel",
	},
	"Opening Stock": {
		"validate": "millitrix.stock.stock_opening.validate",
		"on_submit": "millitrix.stock.stock_opening.on_submit",
		"on_cancel": "millitrix.stock.stock_opening.on_cancel",
	},
	"Closing Stock": {
		"validate": "millitrix.stock.stock_closing.validate",
		"on_submit": "millitrix.stock.stock_closing.on_submit",
		"on_cancel": "millitrix.stock.stock_closing.on_cancel",
	},
	"Stock Adjustment": {
		"validate": "millitrix.stock.stock_adjustment.validate",
		"on_submit": "millitrix.stock.stock_adjustment.on_submit",
		"on_cancel": "millitrix.stock.stock_adjustment.on_cancel",
	},
	"Stock Transfer Note": {
		"validate": "millitrix.stock.stock_transfer.validate",
		"on_submit": "millitrix.stock.stock_transfer.on_submit",
		"on_cancel": "millitrix.stock.stock_transfer.on_cancel",
	},
	"Purchase Order": {
		"validate": [_erpnext_compat, "millitrix.trading.purchase_order.validate"],
		"on_submit": "millitrix.trading.purchase_order.on_submit",
		"on_cancel": "millitrix.trading.purchase_order.on_cancel",
	},
	"PO Cancellation": {
		"validate": [_erpnext_compat, "millitrix.trading.po_cancellation.validate"],
		"on_submit": "millitrix.trading.po_cancellation.on_submit",
		"on_cancel": "millitrix.trading.po_cancellation.on_cancel",
	},
	"Purchase Invoice": {
		"validate": [_erpnext_compat, "millitrix.trading.purchase_invoice.validate"],
		"on_submit": "millitrix.trading.purchase_invoice.on_submit",
		"on_cancel": "millitrix.trading.purchase_invoice.on_cancel",
	},
	"Purchase Return": {
		"validate": [_erpnext_compat, "millitrix.trading.purchase_return.validate"],
		"on_submit": "millitrix.trading.purchase_return.on_submit",
		"on_cancel": "millitrix.trading.purchase_return.on_cancel",
	},
	"Purchase Other Bill": {
		"validate": [_erpnext_compat, "millitrix.trading.purchase_other_bill.validate"],
		"on_submit": "millitrix.trading.purchase_other_bill.on_submit",
		"on_cancel": "millitrix.trading.purchase_other_bill.on_cancel",
	},
	"Sales Order": {
		"validate": [_erpnext_compat, "millitrix.trading.sales_order.validate"],
		"on_submit": "millitrix.trading.sales_order.on_submit",
		"on_cancel": "millitrix.trading.sales_order.on_cancel",
	},
	"SO Cancellation": {
		"validate": [_erpnext_compat, "millitrix.trading.sales_order_cancellation.validate"],
		"on_submit": "millitrix.trading.sales_order_cancellation.on_submit",
		"on_cancel": "millitrix.trading.sales_order_cancellation.on_cancel",
	},
	"Sales Invoice": {
		"validate": [_erpnext_compat, "millitrix.trading.sales_invoice.validate"],
		"on_submit": "millitrix.trading.sales_invoice.on_submit",
		"on_cancel": "millitrix.trading.sales_invoice.on_cancel",
	},
	"Sales Return": {
		"validate": [_erpnext_compat, "millitrix.trading.sales_return.validate"],
		"on_submit": "millitrix.trading.sales_return.on_submit",
		"on_cancel": "millitrix.trading.sales_return.on_cancel",
	},
	"Sales Other Bill": {
		"validate": [_erpnext_compat, "millitrix.trading.sales_other_bill.validate"],
		"on_submit": "millitrix.trading.sales_other_bill.on_submit",
		"on_cancel": "millitrix.trading.sales_other_bill.on_cancel",
	},
	"Voucher Transaction": {
		"validate": [_erpnext_compat, "millitrix.finance.mill_voucher.validate"],
		"on_submit": "millitrix.finance.mill_voucher.on_submit",
		"on_cancel": "millitrix.finance.mill_voucher.on_cancel",
	},
	"Advance Payment": {
		"validate": _erpnext_compat,
	},
	"Advance Receipt": {
		"validate": _erpnext_compat,
	},
	"Advance PNR": {
		"validate": _erpnext_compat,
	},
	"Purchase Invoice Payment": {
		"validate": _erpnext_compat,
	},
	"Sales Invoice Receipt": {
		"validate": _erpnext_compat,
	},
	"Broker Invoice Payment": {
		"validate": _erpnext_compat,
	},
	"Payable Discount Note": {
		"validate": _erpnext_compat,
	},
	"Receivable Discount Note": {
		"validate": _erpnext_compat,
	},
	"Payment Voucher": {
		"validate": _erpnext_compat,
	},
	"Receipt Voucher": {
		"validate": _erpnext_compat,
	},
	"Expense Voucher": {
		"validate": _erpnext_compat,
	},
	"Party Payment Voucher": {
		"validate": _erpnext_compat,
	},
	"Party Receipt Voucher": {
		"validate": _erpnext_compat,
	},
	"Paid Advance Adjustment": {
		"validate": _erpnext_compat,
	},
	"Received Advance Adjustment": {
		"validate": _erpnext_compat,
	},
	"Payment and Receipt Voucher": {
		"validate": [_erpnext_compat, "millitrix.finance.pnr_voucher.validate"],
		"on_submit": "millitrix.finance.pnr_voucher.on_submit",
		"on_cancel": "millitrix.finance.pnr_voucher.on_cancel",
	},
	"Cash and Bank Voucher": {
		"validate": [_erpnext_compat, "millitrix.finance.cnb_voucher.validate"],
		"on_submit": "millitrix.finance.cnb_voucher.on_submit",
		"on_cancel": "millitrix.finance.cnb_voucher.on_cancel",
	},
	"Employee Payment Voucher": {
		"validate": [_erpnext_compat, "millitrix.finance.employee_payment_voucher.validate"],
		"on_submit": "millitrix.finance.employee_payment_voucher.on_submit",
		"on_cancel": "millitrix.finance.employee_payment_voucher.on_cancel",
	},
	"Employee Receipt Voucher": {
		"validate": [_erpnext_compat, "millitrix.finance.employee_receipt_voucher.validate"],
		"on_submit": "millitrix.finance.employee_receipt_voucher.on_submit",
		"on_cancel": "millitrix.finance.employee_receipt_voucher.on_cancel",
	},
	"Closing and Adjustment Entries": {
		"validate": [_erpnext_compat, "millitrix.finance.closing_adjustment_entry.validate"],
		"on_submit": "millitrix.finance.closing_adjustment_entry.on_submit",
		"on_cancel": "millitrix.finance.closing_adjustment_entry.on_cancel",
	},
	"Accounts Opening": {
		"validate": [_erpnext_compat, "millitrix.finance.gl_opening.validate"],
		"on_submit": "millitrix.finance.gl_opening.on_submit",
		"on_cancel": "millitrix.finance.gl_opening.on_cancel",
	},
	"Un-Submit Documents": {
		"validate": [_erpnext_compat, "millitrix.finance.unsubmit.validate"],
		"on_submit": "millitrix.finance.unsubmit.on_submit",
		"on_cancel": "millitrix.finance.unsubmit.on_cancel",
	},
	"Crashing Refine": {
		"validate": [_erpnext_compat, "millitrix.production.crashing_refine.validate"],
		"on_submit": "millitrix.production.crashing_refine.on_submit",
		"on_cancel": "millitrix.production.crashing_refine.on_cancel",
	},
	"PaySlip": {
		"validate": [_erpnext_compat, "millitrix.hr.employee_payslip.validate"],
		"on_submit": "millitrix.hr.employee_payslip.on_submit",
		"on_cancel": "millitrix.hr.employee_payslip.on_cancel",
	},
	"Advance Adjustment": {
		"validate": [_erpnext_compat, "millitrix.finance.advance_adjustment.validate"],
		"on_submit": "millitrix.finance.advance_adjustment.on_submit",
		"on_cancel": "millitrix.finance.advance_adjustment.on_cancel",
	},
	"Payment By Hawala": {
		"validate": [_erpnext_compat, "millitrix.finance.payment_by_hawala.validate"],
		"on_submit": "millitrix.finance.payment_by_hawala.on_submit",
		"on_cancel": "millitrix.finance.payment_by_hawala.on_cancel",
	},
	"Party Gross Margin": {
		"validate": [_erpnext_compat, "millitrix.finance.party_gross_margin.validate"],
		"on_submit": "millitrix.finance.party_gross_margin.on_submit",
		"on_cancel": "millitrix.finance.party_gross_margin.on_cancel",
	},
	"Purchase Return Other Bill": {
		"validate": [_erpnext_compat, "millitrix.trading.purchase_other_bill_return.validate"],
		"on_submit": "millitrix.trading.purchase_other_bill_return.on_submit",
		"on_cancel": "millitrix.trading.purchase_other_bill_return.on_cancel",
	},
	"Sales Return Other Bill": {
		"validate": [_erpnext_compat, "millitrix.trading.sales_other_bill_return.validate"],
		"on_submit": "millitrix.trading.sales_other_bill_return.on_submit",
		"on_cancel": "millitrix.trading.sales_other_bill_return.on_cancel",
	},
	"Pay Salary Increment": {
		"validate": [_erpnext_compat, "millitrix.hr.pay_salary_increment.validate"],
		"on_submit": "millitrix.hr.pay_salary_increment.on_submit",
		"on_cancel": "millitrix.hr.pay_salary_increment.on_cancel",
	},
	"Party": {},
	"Item Setup": {},
	"Chart of Accounting": {},
	"Employee Setup": {},
	"Store Setup": {},
	"Stock In Hand": {},
	"Report Parameter": {},
	"Item Price List": {},
	"User Rights": {
		"on_update": "millitrix.utils.user_permissions.clear_mill_user_cache",
	},
	"Module": {},
	"Menu": {},
	"Document Type": {},
}

from millitrix.utils.user_permissions import PERMISSION_DOCTYPES

has_permission = {
	dt: "millitrix.utils.user_permissions.has_permission" for dt in PERMISSION_DOCTYPES
}
has_permission["Report"] = "millitrix.utils.user_permissions.has_report_permission"
has_permission["User Rights"] = "millitrix.utils.client_access.guard_user_rights_permission"
for _setup_dt in ("Module", "Menu", "Document Type"):
	has_permission[_setup_dt] = "millitrix.utils.client_access.client_doctype_permission"

permission_query_conditions = {
	dt: "millitrix.utils.user_permissions.get_permission_query_conditions"
	for dt in PERMISSION_DOCTYPES
}

_ACCESS = "millitrix.utils.user_permissions.validate_doc_access"
_LOCATION = "millitrix.utils.erpnext_compat.set_session_location"
_SUBMIT = "millitrix.utils.user_permissions.check_submit_permission"
_CANCEL = "millitrix.utils.user_permissions.check_cancel_permission"
_AUTONAME = "millitrix.utils.naming.prepare_new_document_autoname"
for _dt, _events in doc_events.items():
	_events.setdefault("before_submit", _SUBMIT)
	_events.setdefault("before_cancel", _CANCEL)
	current_insert = _events.get("before_insert")
	if current_insert is None:
		_events["before_insert"] = _AUTONAME
	elif isinstance(current_insert, list):
		if _AUTONAME not in current_insert:
			current_insert.insert(0, _AUTONAME)
	elif current_insert != _AUTONAME:
		_events["before_insert"] = [_AUTONAME, current_insert]
	current = _events.get("validate")
	if current is None:
		_events["validate"] = [_LOCATION, _ACCESS]
	elif isinstance(current, list):
		if _LOCATION not in current:
			current.insert(0, _LOCATION)
		if _ACCESS not in current:
			current.append(_ACCESS)
	elif current == _ACCESS:
		_events["validate"] = [_LOCATION, _ACCESS]
	else:
		_events["validate"] = [_LOCATION, current, _ACCESS]
