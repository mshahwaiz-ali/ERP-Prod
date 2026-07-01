// Copyright (c) 2026, Millitrix and contributors
// Transaction Category — Oracle Transaction_Category.fmb (control account level 5).

frappe.ui.form.on("Transaction Category", {
	refresh(frm) {
		frm.set_query("accid", () => ({ filters: { chartlevel: 5, transflag: "Yes" } }));
	},
});
