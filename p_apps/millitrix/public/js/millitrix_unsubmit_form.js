// Unsubmit & Edit on submittable doctypes + Un-Submit Documents form (Oracle UnSubmit.fmb).
// Copyright (c) 2026, Millitrix and contributors

frappe.provide("millitrix.unsubmit");

const UNSUBMIT_DOCTYPES = [
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
	"Sales Order",
	"SO Cancellation",
	"Sales Invoice",
	"Sales Return",
	"Sales Other Bill",
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
	"Crashing Refine",
	"PaySlip",
	"Pay Salary Increment",
	"Advance Adjustment",
	"Payment By Hawala",
	"Party Gross Margin",
	"Purchase Return Other Bill",
	"Sales Return Other Bill",
];

millitrix.unsubmit.add_button = (frm) => {
	if (frm.is_new() || frm.doc.docstatus !== 1) {
		return;
	}
	frm.add_custom_button(__("Unsubmit & Edit"), () => {
		frappe.confirm(__("Unsubmit this document for editing?"), () => {
			frappe.call({
				method: "millitrix.api.unsubmit_form.unsubmit_for_edit",
				args: { doctype: frm.doctype, name: frm.doc.name },
				freeze: true,
				error: millitrix.api.default_error(__("Unsubmit failed")),
				callback() {
					frappe.show_alert({ message: __("Document is editable"), indicator: "green" });
					frm.reload_doc();
				},
			});
		});
	}, __("Actions"));
};

millitrix.unsubmit.sync_target_doctype = async (frm) => {
	const val = frm.doc.usdoctype;
	if (!val) {
		frm.set_value("target_doctype", "");
		return;
	}
	const doctype = await frappe.db.get_value("DocType", val, "name");
	if (doctype?.name) {
		frm.set_value("target_doctype", val);
		return;
	}
	const row = await frappe.db.get_value("Module", val, "doctypeid");
	frm.set_value("target_doctype", row?.doctypeid || "");
};

millitrix.unsubmit.sync_doc_description = async (frm) => {
	if (!frm.doc.target_doctype || !frm.doc.documentid) {
		frm.set_value("doc_description", "");
		return;
	}
	const r = await frappe.call({
		method: "millitrix.api.unsubmit_form.get_document_description",
		args: {
			usdoctype: frm.doc.usdoctype,
			documentid: frm.doc.documentid,
			target_doctype: frm.doc.target_doctype,
		},
	});
	frm.set_value("doc_description", r.message || "");
};

millitrix.unsubmit.configure_unsubmit_form = (frm) => {
	frm.set_query("usdoctype", () => ({
		query: "millitrix.api.unsubmit_form.module_link_query",
	}));
	frm.set_query("documentid", () => {
		if (!frm.doc.target_doctype) {
			return { filters: { name: ["=", ""] } };
		}
		return { filters: { docstatus: 1 } };
	});
};

UNSUBMIT_DOCTYPES.forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			millitrix.unsubmit.add_button(frm);
		},
	});
});

frappe.ui.form.on("Un-Submit Documents", {
	setup(frm) {
		millitrix.unsubmit.configure_unsubmit_form(frm);
	},
	async onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "Un-Submit Documents");
		}
		await millitrix.unsubmit.sync_target_doctype(frm);
		await millitrix.unsubmit.sync_doc_description(frm);
	},
	async usdoctype(frm) {
		await millitrix.unsubmit.sync_target_doctype(frm);
		frm.set_value("documentid", "");
		frm.set_value("doc_description", "");
	},
	async documentid(frm) {
		await millitrix.unsubmit.sync_doc_description(frm);
	},
});
