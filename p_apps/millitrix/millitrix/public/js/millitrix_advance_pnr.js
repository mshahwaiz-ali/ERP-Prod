// Copyright (c) 2026, Millitrix and contributors
// Oracle PNRAdvance.fmb — unified Advance PNR (Payment / Receipt flows).

frappe.provide("millitrix.advance_pnr");

millitrix.advance_pnr.FLOW_PARTY_CATEGORIES = {
	payment: ["12"],
	receipt: ["13"],
};

millitrix.advance_pnr.FLOW_LABELS = {
	payment: {
		title: __("Advance Payment"),
		party: __("Party"),
		mode: __("Payment Mode"),
		print_format: "Advance Payment Voucher",
	},
	receipt: {
		title: __("Advance Receipt"),
		party: __("Customer"),
		mode: __("Receipt Mode"),
		print_format: "Advance Receipt Voucher",
	},
};

millitrix.advance_pnr.FIELD_ORDERS = {
	payment: [
		"pnrno",
		"advance_flow",
		"pnrdate",
		"referno",
		"referdate",
		"partyid",
		"party_name",
		"bankaccid",
		"bank_name",
		"pnrmode",
		"amount",
		"narration",
	],
	receipt: [
		"pnrno",
		"advance_flow",
		"pnrdate",
		"partyid",
		"party_name",
		"bankaccid",
		"bank_name",
		"narration",
		"referno",
		"referdate",
		"pnrmode",
		"amount",
	],
};

millitrix.advance_pnr.apply_field_order = function (frm) {
	if (frm.doctype !== "Advance PNR") {
		return;
	}
	const flow = millitrix.advance_pnr.flow_key(frm) || "payment";
	const order = millitrix.advance_pnr.FIELD_ORDERS[flow];
	if (!order?.length) {
		return;
	}
	const container = frm.layout?.wrapper?.find(".form-column").first();
	if (!container?.length) {
		return;
	}
	order.forEach((fieldname) => {
		const field = frm.fields_dict[fieldname];
		if (field?.$wrapper) {
			field.$wrapper.detach().appendTo(container);
		}
	});
};

millitrix.advance_pnr.open_new = function (flow) {
	frappe.route_options = { millitrix_advance_flow: flow };
	frappe.set_route("Form", "Advance PNR", "new");
};

millitrix.advance_pnr.flow_key = function (frm) {
	const flow = frm.doc.advance_flow || frm._millitrix_advance_flow;
	if (flow === "Receipt") {
		return "receipt";
	}
	if (flow === "Payment") {
		return "payment";
	}
	return frm._millitrix_advance_flow || null;
};

millitrix.advance_pnr.apply_form_defaults = function (frm) {
	const opts = frappe.route_options || {};
	const route_flow = opts.millitrix_advance_flow;
	if (route_flow) {
		frm._millitrix_advance_flow = route_flow;
		const label = route_flow === "receipt" ? "Receipt" : "Payment";
		if (!frm.doc.advance_flow) {
			frm.set_value("advance_flow", label);
		}
		frappe.route_options = {};
	}
	if (!frm.doc.advance_flow && frm._millitrix_advance_flow) {
		frm.set_value(
			"advance_flow",
			frm._millitrix_advance_flow === "receipt" ? "Receipt" : "Payment"
		);
	}
	millitrix.advance_pnr.apply_form_labels(frm);
	millitrix.advance_pnr.set_party_query(frm, millitrix.advance_pnr.flow_key(frm));
	millitrix.advance_pnr.apply_field_order(frm);
};

millitrix.advance_pnr.apply_form_labels = function (frm) {
	const flow = millitrix.advance_pnr.flow_key(frm);
	const labels = millitrix.advance_pnr.FLOW_LABELS[flow];
	if (!labels) {
		return;
	}
	if (frm.fields_dict.partyid) {
		frm.set_df_property("partyid", "label", labels.party);
	}
	if (frm.fields_dict.pnrmode) {
		frm.set_df_property("pnrmode", "label", labels.mode);
	}
	if (frm.fields_dict.bankaccid) {
		frm.set_df_property("bankaccid", "label", __("Bank"));
	}
	if (frm.fields_dict.amount) {
		frm.set_df_property("amount", "label", __("Advance"));
	}
	millitrix.advance_pnr.apply_payment_fetch_labels(frm);
	if (frm.doc.docstatus === 0) {
		frm.set_df_property("advance_flow", "read_only", frm._millitrix_advance_flow ? 1 : 0);
	}
	millitrix.advance_pnr.apply_field_order(frm);
};

millitrix.advance_pnr.apply_payment_fetch_labels = function (frm) {
	["party_name", "bank_name"].forEach((field) => {
		if (frm.fields_dict[field]) {
			frm.set_df_property(field, "label", "");
		}
	});
};

millitrix.advance_pnr.set_party_query = function (frm, flow) {
	const categories = millitrix.advance_pnr.FLOW_PARTY_CATEGORIES[flow];
	if (!categories) {
		return;
	}
	frm.set_query("partyid", () => ({
		filters: { pcat_id: ["in", categories] },
	}));
};

millitrix.advance_pnr.print_voucher = function (frm) {
	const flow = millitrix.advance_pnr.flow_key(frm);
	const labels = millitrix.advance_pnr.FLOW_LABELS[flow] || {};
	const print_format = labels.print_format || "Advance Payment Voucher";
	frm.print_doc(undefined, print_format);
};
