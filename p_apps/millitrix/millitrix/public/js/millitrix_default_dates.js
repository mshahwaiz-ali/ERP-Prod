// Copyright (c) 2026, Millitrix and contributors
// Oracle $$Date$$ = SYSDATE on new transaction forms (editable default = today).

frappe.provide("millitrix.default_dates");

millitrix.default_dates.TRANSACTION_DOCTYPES = {
	"Purchase Order": "podate",
	"Sales Order": "sodate",
	"Purchase Invoice": "invdate",
	"Sales Invoice": "invdate",
	"Purchase Return": "retdate",
	"Sales Return": "retdate",
	"Purchase Other Bill": "billdate",
	"Sales Other Bill": "billdate",
	"Purchase Return Other Bill": "brdate",
	"Sales Return Other Bill": "brdate",
	"In Out Gate Pass": "gpdate",
	"Stock Adjustment": "sadate",
	"Stock Transfer Note": "tdate",
	"Opening Stock": "opendate",
	"Closing Stock": "opendate",
	"Crashing Refine": "crdate",
	"PO Cancellation": "candate",
	"SO Cancellation": "candate",
	"Un-Submit Documents": "usdate",
	"Accounts Opening": "opening_date",
	"Voucher Transaction": "vouchdate",
	"Closing and Adjustment Entries": "vouchdate",
	"Advance Payment": "pnrdate",
	"Advance Receipt": "pnrdate",
	"Advance PNR": "pnrdate",
	"Purchase Invoice Payment": "pnrdate",
	"Sales Invoice Receipt": "pnrdate",
	"Broker Invoice Payment": "pnrdate",
	"Payable Discount Note": "pnrdate",
	"Receivable Discount Note": "pnrdate",
	"Paid Advance Adjustment": "adjdate",
	"Received Advance Adjustment": "adjdate",
	"Payment Voucher": "vouchdate",
	"Receipt Voucher": "vouchdate",
	"Expense Voucher": "vouchdate",
	"Party Payment Voucher": "vouchdate",
	"Party Receipt Voucher": "vouchdate",
	"Employee Payment Voucher": "vouchdate",
	"Employee Receipt Voucher": "vouchdate",
	"Party Gross Margin": "pgdate",
	"Payment By Hawala": "gmdate",
	"PaySlip": "pdate",
	"Item Price List": "ipdate",
	"Pay Salary Increment": "indate",
	"Cash and Bank Voucher": "vouchdate",
	"Payment and Receipt Voucher": "pnrdate",
};

millitrix.default_dates.apply = function (frm) {
	const date_field = millitrix.default_dates.TRANSACTION_DOCTYPES[frm.doctype];
	if (!date_field || !frm.is_new() || frm.doc[date_field]) {
		return;
	}
	if (!frm.fields_dict[date_field]) {
		return;
	}
	frm.set_value(date_field, frappe.datetime.get_today());
};

Object.keys(millitrix.default_dates.TRANSACTION_DOCTYPES).forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		onload(frm) {
			millitrix.default_dates.apply(frm);
		},
		refresh(frm) {
			millitrix.default_dates.apply(frm);
		},
	});
});
