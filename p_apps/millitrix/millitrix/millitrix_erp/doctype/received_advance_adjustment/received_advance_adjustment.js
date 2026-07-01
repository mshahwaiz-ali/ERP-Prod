// Copyright (c) 2026, Millitrix and contributors
// Oracle AdvanceAdjustment.fmb — customer advance vs sales invoices.

frappe.ui.form.on("Received Advance Adjustment", {
	refresh(frm) {
		millitrix.knockoff.setup_advance_adjustment_form(frm, "receipt");
	},

	invoice_lines_remove(frm) {
		millitrix.knockoff.recalc_child_total(frm, "invoice_lines", "amount");
	},

	pnr_lines_remove(frm) {
		millitrix.knockoff.recalc_child_total(frm, "pnr_lines", "amount");
	},
});
