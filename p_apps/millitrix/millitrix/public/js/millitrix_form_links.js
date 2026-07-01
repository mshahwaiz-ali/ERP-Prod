// Blueprint link filters — party category, COA level 5, store by location.
// Copyright (c) 2026, Millitrix and contributors

frappe.provide("millitrix.form_links");
frappe.provide("millitrix.api");

millitrix.api.default_error =
	(title) =>
	(r) => {
		frappe.msgprint({
			title: title || __("Request failed"),
			message: r?.message || __("Could not complete the request."),
			indicator: "red",
		});
	};

millitrix.api.call = (opts) =>
	frappe.call({
		...opts,
		error: opts.error || millitrix.api.default_error(opts.error_title),
	});

millitrix.form_links.COA_POSTING = { chartlevel: 5, transflag: "Yes" };

const PCAT = { broker: ["11"], supplier: ["12"], customer: ["13"] };

millitrix.form_links.PARTY_BY_FIELD = {
	brokerid: PCAT.broker,
	supplierid: PCAT.supplier,
	customerid: PCAT.customer,
};

// Client screenshots hide Location on finance forms — default from user session.
// Keep in sync with blueprint_form_rules.LOCATION_UI_HIDDEN_DOCTYPES
millitrix.form_links.LOCATION_UI_HIDDEN = new Set([
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
	"Employee Payment Voucher",
	"Employee Receipt Voucher",
	"Paid Advance Adjustment",
	"Received Advance Adjustment",
	"Payment By Hawala",
	"Party Gross Margin",
	"Accounts Opening",
	"Opening Stock",
	"Closing Stock",
	"Crashing Refine",
	"Closing and Adjustment Entries",
	"Voucher Transaction",
	"Un-Submit Documents",
	"PaySlip",
	"Payment and Receipt Voucher",
	"Cash and Bank Voucher",
	"Advance Adjustment",
	"PO Cancellation",
	"SO Cancellation",
	"Purchase Invoice",
	"Sales Invoice",
	"Purchase Order",
	"Sales Order",
	"Purchase Return",
	"Sales Return",
	"Purchase Other Bill",
	"Purchase Return Other Bill",
	"Sales Other Bill",
	"Sales Return Other Bill",
	"Stock Adjustment",
	"Stock Transfer Note",
	"In Out Gate Pass",
	"Item Price List",
]);

millitrix.form_links.apply_default_location = function (frm) {
	if (frm.doc.location_id || !frm.fields_dict.location_id) {
		return;
	}
	if (frm.doctype === "Crashing Refine" && frm.doc.mill_id) {
		frm.set_value("location_id", frm.doc.mill_id);
		return;
	}
	frappe.call({
		method: "millitrix.api.user_context.get_user_scope",
		callback(r) {
			const loc = r.message?.location_id;
			if (loc && !frm.doc.location_id) {
				frm.set_value("location_id", loc);
			}
		},
		error: millitrix.api.default_error(__("Could not load user location")),
	});
};

millitrix.form_links.apply_common_queries = function (frm) {
	const loc = frm.doc.location_id;

	Object.entries(millitrix.form_links.PARTY_BY_FIELD).forEach(([field, cats]) => {
		if (!frm.fields_dict[field]) return;
		frm.set_query(field, () => ({ filters: { pcat_id: ["in", cats] } }));
	});

	["partyid", "sub_partyid"].forEach((field) => {
		if (!frm.fields_dict[field]) return;
		frm.set_query(field, () => {
			const filters = {};
			if (frm.doctype === "Advance PNR") {
				const flow = frm.doc.advance_flow === "Receipt" ? PCAT.customer : PCAT.supplier;
				filters.pcat_id = ["in", flow];
			}
			if (frm.doctype === "Advance Payment") filters.pcat_id = ["in", PCAT.supplier];
			if (frm.doctype === "Advance Receipt") filters.pcat_id = ["in", PCAT.customer];
			if (frm.doctype === "Purchase Invoice Payment") filters.pcat_id = ["in", PCAT.supplier];
			if (frm.doctype === "Sales Invoice Receipt") filters.pcat_id = ["in", PCAT.customer];
			if (frm.doctype === "Broker Invoice Payment") filters.pcat_id = ["in", PCAT.broker];
			if (frm.doctype === "Payable Discount Note") filters.pcat_id = ["in", PCAT.supplier];
			if (frm.doctype === "Receivable Discount Note") filters.pcat_id = ["in", PCAT.customer];
			if (frm.doctype === "Paid Advance Adjustment") filters.pcat_id = ["in", PCAT.supplier];
			if (frm.doctype === "Received Advance Adjustment") filters.pcat_id = ["in", PCAT.customer];
			if (frm.doctype === "PO Cancellation") filters.pcat_id = ["in", PCAT.supplier];
			if (frm.doctype === "SO Cancellation") filters.pcat_id = ["in", PCAT.customer];
			if (frm.doctype === "In Out Gate Pass") {
				filters.pcat_id = ["in", [...PCAT.supplier, ...PCAT.customer]];
			}
			if (frm.doctype === "Party Payment Voucher") {
				filters.pcat_id = ["in", PCAT.supplier];
			}
			if (frm.doctype === "Party Receipt Voucher") {
				filters.pcat_id = ["in", PCAT.customer];
			}
			return { filters };
		});
	});

	["bankaccid", "accid"].forEach((field) => {
		if (!frm.fields_dict[field]) return;
		const df = frappe.meta.get_docfield(frm.doctype, field);
		if (field === "bankaccid" && df?.options === "Bank Account") {
			frm.set_query(field, () => ({}));
			return;
		}
		frm.set_query(field, () => ({ filters: millitrix.form_links.COA_POSTING }));
	});

	["storeid", "fromstoreid", "tostoreid"].forEach((field) => {
		if (!frm.fields_dict[field]) return;
		frm.set_query(field, () => {
			const filters = {};
			if (loc) filters.location_id = loc;
			return { filters };
		});
	});

	if (frm.fields_dict.itemcode) {
		frm.set_query("itemcode", () => ({ filters: { stockable: "Yes" } }));
	}

	if (frm.fields_dict.empno) {
		frm.set_query("empno", () => {
			const filters = {};
			if (loc) filters.location_id = loc;
			return { filters };
		});
	}
};

const TRANSACTION_DOCTYPES = [
	"Purchase Order", "Sales Order", "Purchase Invoice", "Sales Invoice",
	"Purchase Return", "Sales Return", "Purchase Other Bill", "Sales Other Bill",
	"Purchase Return Other Bill", "Sales Return Other Bill",
	"Opening Stock", "Closing Stock", "Stock Adjustment", "Stock Transfer Note",
	"In Out Gate Pass", "Item Setup", "Item Price List", "Crashing Refine",
	"Advance PNR", "Advance Payment", "Advance Receipt",
	"Purchase Invoice Payment", "Sales Invoice Receipt", "Broker Invoice Payment",
	"Payable Discount Note", "Receivable Discount Note",
	"Payment Voucher", "Receipt Voucher", "Expense Voucher",
	"Party Payment Voucher", "Party Receipt Voucher",
	"Paid Advance Adjustment", "Received Advance Adjustment",
	"Payment and Receipt Voucher", "Cash and Bank Voucher",
	"Employee Payment Voucher", "Employee Receipt Voucher",
	"Advance Adjustment", "Accounts Opening", "Voucher Transaction",
	"Party Gross Margin", "Payment By Hawala", "Closing and Adjustment Entries",
	"PaySlip", "PO Cancellation", "SO Cancellation", "Un-Submit Documents",
];

TRANSACTION_DOCTYPES.forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		onload(frm) {
			millitrix.form_links.apply_default_location(frm);
		},
		refresh(frm) {
			millitrix.form_links.apply_common_queries(frm);
		},
	});
});

frappe.ui.form.on("Party", {
	refresh(frm) {
		frm.set_query("pcat_id", () => ({ filters: {} }));
		frm.set_query("cityid", () => ({ filters: {} }));
	},
});

frappe.ui.form.on("Store Setup", {
	refresh(frm) {
		if (frm.fields_dict.location_id) {
			frm.set_query("storetypeid", () => ({ filters: {} }));
		}
	},
});

frappe.ui.form.on("Bank Account", {
	refresh(frm) {
		frm.set_query("accid", () => ({ filters: millitrix.form_links.COA_POSTING }));
	},
});

frappe.ui.form.on("Party Item", {
	refresh(frm) {
		frm.set_query("itemcode", () => ({ filters: { stockable: "Yes" } }));
	},
});
