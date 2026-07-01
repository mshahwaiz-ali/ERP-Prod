// Copyright (c) 2026, Millitrix and contributors
// Party Category — Oracle Party_Category.fmb (control account level 4).

frappe.ui.form.on("Party Category", {
	refresh(frm) {
		frm.set_query("accid", () => ({ filters: { chartlevel: 4, transflag: "Yes" } }));
	},
});
