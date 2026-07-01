// Copyright (c) 2026, Millitrix and contributors
frappe.ui.form.on("Advance Adjustment", {
	refresh(frm) {
		millitrix.knockoff.add_load_button(frm, {
			child_field: "invoice_lines",
			date_field: "adjdate",
			map_row: millitrix.knockoff.ADJUSTMENT_INVOICE_MAP,
			after_load(frm) {
				millitrix.knockoff.recalc_child_total(frm, "invoice_lines", "amount");
			},
		});
		millitrix.knockoff.add_load_advance_pnr_button(frm, {
			child_field: "pnr_lines",
			date_field: "adjdate",
			map_row: millitrix.knockoff.ADVANCE_PNR_MAP,
			after_load(frm) {
				millitrix.knockoff.recalc_child_total(frm, "pnr_lines", "amount");
			},
		});
	},
	invoice_lines_remove(frm) {
		millitrix.knockoff.recalc_child_total(frm, "invoice_lines", "amount");
	},
	pnr_lines_remove(frm) {
		millitrix.knockoff.recalc_child_total(frm, "pnr_lines", "amount");
	},
});

frappe.ui.form.on("Adjustment Invoice", {
	amount(frm) {
		millitrix.knockoff.recalc_child_total(frm, "invoice_lines", "amount");
	},
});

frappe.ui.form.on("Adjustment PNR", {
	amount(frm) {
		millitrix.knockoff.recalc_child_total(frm, "pnr_lines", "amount");
	},
});
