// Copyright (c) 2026, Millitrix and contributors
frappe.ui.form.on("Module", {
	refresh(frm) {
		if (frm.is_new() && !frm.doc.moduletype) {
			frm.set_value("moduletype", "F");
		}
	},
});
