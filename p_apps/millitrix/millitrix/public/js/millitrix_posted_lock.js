// Copyright (c) 2026, Millitrix and contributors
// Lock submitted / legacy-posted transaction forms (Oracle POSTED=Y).

frappe.provide("millitrix.posted_lock");

millitrix.posted_lock.LOCK_DOCTYPES = new Set([
	"Purchase Order",
	"Sales Order",
	"Purchase Invoice",
	"Sales Invoice",
	"Purchase Return",
	"Sales Return",
	"Purchase Other Bill",
	"Sales Other Bill",
	"Purchase Return Other Bill",
	"Sales Return Other Bill",
	"In Out Gate Pass",
	"Stock Adjustment",
	"Stock Transfer Note",
	"Opening Stock",
	"Closing Stock",
	"Crashing Refine",
	"PO Cancellation",
	"SO Cancellation",
	"Voucher Transaction",
	"Purchase Invoice Payment",
	"Sales Invoice Receipt",
	"Broker Invoice Payment",
	"Advance Payment",
	"Advance Receipt",
	"Advance PNR",
	"Payable Discount Note",
	"Receivable Discount Note",
	"Payment Voucher",
	"Receipt Voucher",
	"Expense Voucher",
	"Party Payment Voucher",
	"Party Receipt Voucher",
	"Employee Payment Voucher",
	"Employee Receipt Voucher",
	"Paid Advance Adjustment",
	"Received Advance Adjustment",
	"Payment By Hawala",
	"Party Gross Margin",
	"Closing and Adjustment Entries",
	"Accounts Opening",
	"PaySlip",
	"Payment and Receipt Voucher",
	"Cash and Bank Voucher",
	"Advance Adjustment",
]);

millitrix.posted_lock.apply = (frm) => {
	if (!millitrix.posted_lock.LOCK_DOCTYPES.has(frm.doctype)) {
		return;
	}
	const legacy_posted =
		String(frm.doc.posted || "").trim().toUpperCase() in { Y: 1, YES: 1, SUBMITTED: 1 };
	if (frm.doc.docstatus === 1 || legacy_posted) {
		frm.disable_form();
	}
};

for (const doctype of millitrix.posted_lock.LOCK_DOCTYPES) {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			millitrix.posted_lock.apply(frm);
		},
	});
}
