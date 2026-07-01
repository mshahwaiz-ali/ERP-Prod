// Copyright (c) 2026, Millitrix and contributors
// Payment By Hawala — Oracle: Debit section + Credit section (not a child-table grid)

frappe.provide("millitrix.hawala");

millitrix.hawala.HAWALA_INVOICE_MAP = (row) => ({
	doctypeid: row.doctypeid,
	documentid: row.documentid,
	docbalamnt: row.docbalamnt,
	amount: row.docbalamnt,
	suspense: 0,
});

millitrix.hawala.apply_credit_queries = function (frm) {
	if (frm.fields_dict.b_partyid) {
		frm.set_query("b_partyid", () => ({ filters: {} }));
	}
	if (frm.fields_dict.b_accid) {
		frm.set_query("b_accid", () => ({ filters: millitrix.form_links.COA_POSTING }));
	}
	if (frm.fields_dict.b_itemcode) {
		frm.set_query("b_itemcode", () => ({ filters: { stockable: "Yes" } }));
	}
};

millitrix.hawala.sync_credit_amount = function (frm) {
	if (frm.doc.b_amount && !frm.doc.amount) {
		frm.set_value("amount", frm.doc.b_amount);
	} else if (frm.doc.amount && !frm.doc.b_amount) {
		frm.set_value("b_amount", frm.doc.amount);
	}
};

millitrix.hawala.setup = function (frm) {
	if (!frm.doc.doctypeid) {
		frm.set_value("doctypeid", "Payment By Hawala");
	}
	millitrix.form_links.apply_default_location(frm);
	millitrix.form_links.apply_common_queries(frm);
	this.apply_credit_queries(frm);
	this.sync_credit_amount(frm);
	if (frm.is_new()) {
		if (millitrix.child_table) {
			millitrix.child_table.setup(frm);
		}
		return;
	}
	millitrix.knockoff.add_accounting_button(frm, {
		document_id_field: "gmid",
		method: "millitrix.api.knockoff.get_hawala_accounting_lines",
	});
	if (!frm.is_new() && frm.attachments?.new_attachment) {
		frm.add_custom_button(__("Documents"), () => frm.attachments.new_attachment());
	}
	if (frm.doc.docstatus === 0 && frm.doc.partyid) {
		millitrix.knockoff.add_load_button(frm, {
			child_field: "invoices",
			date_field: "gmdate",
			party_field: "partyid",
			flow: "payment",
			replace_flow: "payment",
			map_row: millitrix.hawala.HAWALA_INVOICE_MAP,
			button_label: __("Get Documents"),
		});
	}
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
};

frappe.ui.form.on("Payment By Hawala", {
	onload(frm) {
		millitrix.hawala.setup(frm);
	},

	refresh(frm) {
		millitrix.hawala.setup(frm);
	},

	amount(frm) {
		if (frm.doc.amount && frm.doc.b_amount !== frm.doc.amount) {
			frm.set_value("b_amount", frm.doc.amount);
		}
	},

	b_amount(frm) {
		if (frm.doc.b_amount && frm.doc.amount !== frm.doc.b_amount) {
			frm.set_value("amount", frm.doc.b_amount);
		}
	},
});
