// Copyright (c) 2026, Millitrix and contributors
// Transaction List — Oracle Transaction_setup.fmb

frappe.ui.form.on("Transaction List", {
	refresh(frm) {
		frm.set_query("tcat_id", () => ({
			filters: {},
		}));
	},
});
