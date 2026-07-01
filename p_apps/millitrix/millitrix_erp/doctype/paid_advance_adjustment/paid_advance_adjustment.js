// Copyright (c) 2026, Millitrix and contributors
// Oracle AdvanceAdjustment.fmb — supplier advance vs purchase invoices.

frappe.ui.form.on("Paid Advance Adjustment", {
	refresh(frm) {
		millitrix.knockoff.setup_advance_adjustment_form(frm, "payment");
	},

	invoice_lines_remove(frm) {
		millitrix.knockoff.recalc_child_total(frm, "invoice_lines", "amount");
	},

	pnr_lines_remove(frm) {
		millitrix.knockoff.recalc_child_total(frm, "pnr_lines", "amount");
	},
});
