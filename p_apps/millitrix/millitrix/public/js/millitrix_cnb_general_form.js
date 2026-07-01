// Copyright (c) 2026, Millitrix and contributors
// Payment / Receipt — A/c Id grid (Cash and Bank Voucher Detail).
// Expense — Trans Id grid (Expense Voucher Detail).

frappe.provide("millitrix.cnb_general");

millitrix.cnb_general.EXPENSE_DOCTYPE = "Expense Voucher";
millitrix.cnb_general.PAYMENT_DOCTYPES = ["Payment Voucher", "Receipt Voucher"];

millitrix.cnb_general.update_total = function (frm) {
	const rows = frm.doc.details || [];
	const line_total = rows.reduce((sum, row) => sum + flt(row.amount), 0);
	if (frm.doc.docstatus === 0 && !frm.is_new()) {
		frm.set_value("amount", line_total);
	}
	const show_total = rows.length >= 1 || frm.doc.docstatus === 1;
	frm.toggle_display("amount", show_total);
};

millitrix.cnb_general.setup_expense = function (frm) {
	if (!frm.doc.doctypeid) {
		frm.set_value("doctypeid", frm.doctype);
	}
	if (frm.fields_dict.bank_name) {
		frm.set_df_property("bank_name", "label", "");
	}
	if (frm.fields_dict.bankaccid) {
		frm.set_df_property("bankaccid", "label", __("Bank"));
	}
	frm.set_query("trans_id", "details", () => ({ filters: {} }));
	this.update_total(frm);
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, {
			document_id_field: "cnbvno",
			method: "millitrix.api.knockoff.get_cnb_accounting_lines",
		});
	}
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
};

millitrix.cnb_general.setup_payment = function (frm) {
	if (!frm.doc.doctypeid) {
		frm.set_value("doctypeid", frm.doctype);
	}
	if (frm.fields_dict.bank_name) {
		frm.set_df_property("bank_name", "label", "");
	}
	if (frm.fields_dict.bankaccid) {
		frm.set_df_property("bankaccid", "label", __("Bank"));
	}
	frm.set_query("accid", "details", () => ({ filters: millitrix.form_links.COA_POSTING }));
	this.update_total(frm);
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, {
			document_id_field: "cnbvno",
			method: "millitrix.api.knockoff.get_cnb_accounting_lines",
		});
	}
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
};

frappe.ui.form.on("Expense Voucher", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "Expense Voucher");
		}
		millitrix.cnb_general.setup_expense(frm);
	},

	refresh(frm) {
		millitrix.cnb_general.setup_expense(frm);
	},

	details_add(frm) {
		setTimeout(() => millitrix.cnb_general.setup_expense(frm), 100);
	},

	details_remove(frm) {
		millitrix.cnb_general.update_total(frm);
	},
});

millitrix.cnb_general.PAYMENT_DOCTYPES.forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		onload(frm) {
			if (!frm.doc.doctypeid) {
				frm.set_value("doctypeid", doctype);
			}
			millitrix.cnb_general.setup_payment(frm);
		},

		refresh(frm) {
			millitrix.cnb_general.setup_payment(frm);
		},

		details_add(frm) {
			setTimeout(() => millitrix.cnb_general.setup_payment(frm), 100);
		},

		details_remove(frm) {
			millitrix.cnb_general.update_total(frm);
		},
	});
});

frappe.ui.form.on("Cash and Bank Voucher Detail", {
	amount(frm) {
		if (millitrix.cnb_general.PAYMENT_DOCTYPES.includes(frm.doctype)) {
			millitrix.cnb_general.update_total(frm);
		}
	},
});

frappe.ui.form.on("Expense Voucher Detail", {
	amount(frm) {
		if (frm.doctype === millitrix.cnb_general.EXPENSE_DOCTYPE) {
			millitrix.cnb_general.update_total(frm);
		}
	},
});
