// Copyright (c) 2026, Millitrix and contributors
frappe.ui.form.on("Menu", {
	refresh(frm) {
		if (frm.is_new() && !frm.doc.sortby) {
			frm.set_value("sortby", 1);
		}
	},
});
