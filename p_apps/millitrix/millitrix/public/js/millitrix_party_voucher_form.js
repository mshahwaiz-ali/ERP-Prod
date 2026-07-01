// Copyright (c) 2026, Millitrix and contributors
// Party Payment / Receipt Voucher — Oracle CNBPartyVoucher.fmx

frappe.provide("millitrix.party_voucher");

millitrix.party_voucher.DOCTYPES = {
	"Party Payment Voucher": {
		flow: "payment",
		balance_label: "Payable",
		amount_label: "Paid",
	},
	"Party Receipt Voucher": {
		flow: "receipt",
		balance_label: "Receivable",
		amount_label: "Received",
	},
};

millitrix.party_voucher.DOCUMENT_GRID = [
	"partyid",
	"party_name",
	"documentid",
	"docbalamnt",
	"amount",
	"balance",
];

millitrix.party_voucher.update_total = function (frm) {
	if (!this.DOCTYPES[frm.doctype]) {
		return;
	}
	const rows = frm.doc.documents || [];
	const line_total = rows.reduce((sum, row) => sum + flt(row.amount), 0);
	if (frm.doc.docstatus === 0 && !frm.is_new()) {
		frm.set_value("amount", line_total);
	}
	const show_total = rows.length >= 1 || frm.doc.docstatus === 1;
	frm.toggle_display("amount", show_total);
};

millitrix.party_voucher.setup = function (frm) {
	const cfg = this.DOCTYPES[frm.doctype];
	if (!cfg) {
		return;
	}
	if (!frm.doc.doctypeid) {
		frm.set_value("doctypeid", frm.doctype);
	}
	if (frm.fields_dict.bank_name) {
		frm.set_df_property("bank_name", "label", "");
	}
	if (frm.fields_dict.party_name) {
		frm.set_df_property("party_name", "label", "");
	}
	millitrix.knockoff.apply_cnb_document_grid(frm, "documents", this.DOCUMENT_GRID);
	const grid = frm.fields_dict.documents?.grid;
	if (grid && cfg.balance_label) {
		millitrix.knockoff.set_grid_field(grid, "docbalamnt", {
			label: __(cfg.balance_label),
		});
		millitrix.knockoff.set_grid_field(grid, "amount", {
			label: __(cfg.amount_label),
		});
		grid.refresh();
	}
	this.update_total(frm);
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, {
			document_id_field: "cnbvno",
			method: "millitrix.api.knockoff.get_cnb_accounting_lines",
		});
	}
	if (!frm.is_new() && frm.doc.docstatus === 0) {
		millitrix.knockoff.add_load_button(frm, {
			child_field: "documents",
			date_field: "vouchdate",
			party_field: "partyid",
			flow: cfg.flow,
			map_row: (row, partyid) => millitrix.knockoff.CNB_DOCUMENT_MAP(row, partyid),
			after_load(f) {
				millitrix.party_voucher.update_total(f);
			},
		});
	}
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
};

Object.keys(millitrix.party_voucher.DOCTYPES).forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			millitrix.party_voucher.setup(frm);
		},

		documents_add(frm) {
			setTimeout(() => millitrix.party_voucher.setup(frm), 100);
		},

		documents_remove(frm) {
			millitrix.party_voucher.update_total(frm);
		},
	});
});

frappe.ui.form.on("Cash and Bank Voucher Document", {
	amount(frm, cdt, cdn) {
		if (!millitrix.party_voucher.DOCTYPES[frm.doctype]) {
			return;
		}
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
		millitrix.knockoff.recalc_cnb_document_balance(cdt, cdn);
		millitrix.party_voucher.update_total(frm);
	},
	partyid(frm, cdt, cdn) {
		if (!millitrix.party_voucher.DOCTYPES[frm.doctype]) {
			return;
		}
		millitrix.knockoff.recalc_cnb_document_balance(cdt, cdn);
	},
	form_render(frm, cdt, cdn) {
		if (!millitrix.party_voucher.DOCTYPES[frm.doctype]) {
			return;
		}
		millitrix.knockoff.recalc_cnb_document_balance(cdt, cdn);
	},
});
