// Copyright (c) 2026, Millitrix and contributors
// Employee Category — Oracle Pay_EmpCategory.fmb

frappe.ui.form.on("Employee Category", {
	refresh(frm) {
		frm.set_query("accid", () => ({
			filters: { chartlevel: 5, transflag: "Yes" },
		}));
	},
});
