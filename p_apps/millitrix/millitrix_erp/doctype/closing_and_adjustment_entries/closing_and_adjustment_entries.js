// Copyright (c) 2026, Millitrix and contributors
// Closing and Adjustment Entries — grid totals below details (Oracle Closing_Transaction).

frappe.ui.form.on("Closing and Adjustment Entries", {
	refresh(frm) {
		millitrix.closing_entry.update_totals(frm);
		frm.add_custom_button(__("Closing"), () => {
			frappe.set_route("page", "year-end-closing");
		});
	},

	details_add(frm) {
		millitrix.closing_entry.update_totals(frm);
	},

	details_remove(frm) {
		millitrix.closing_entry.update_totals(frm);
	},
});

frappe.ui.form.on("Voucher Transaction Detail", {
	debit(frm) {
		if (frm.doctype === "Closing and Adjustment Entries") {
			millitrix.closing_entry.update_totals(frm);
		}
	},
	credit(frm) {
		if (frm.doctype === "Closing and Adjustment Entries") {
			millitrix.closing_entry.update_totals(frm);
		}
	},
});

frappe.provide("millitrix.closing_entry");

millitrix.closing_entry.update_totals = (frm) => {
	const rows = frm.doc.details || [];
	let total_debit = 0;
	let total_credit = 0;
	rows.forEach((row) => {
		total_debit += flt(row.debit);
		total_credit += flt(row.credit);
	});
	frm.set_value("total_debit", total_debit);
	frm.set_value("total_credit", total_credit);
	// Oracle shows totals row when more than one detail line.
	const show_totals = rows.length > 1;
	frm.toggle_display("total_debit", show_totals);
	frm.toggle_display("total_credit", show_totals);
};
