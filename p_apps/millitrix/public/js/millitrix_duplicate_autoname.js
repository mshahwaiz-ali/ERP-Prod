// Copyright (c) 2026, Millitrix and contributors
// Duplicate: clear read-only autoname fields so UI matches New (number assigned on save).

frappe.provide("millitrix.duplicate_autoname");

millitrix.duplicate_autoname.clear_if_needed = (frm) => {
	if (!frm?.is_new() || frm.doc.amended_from || frm.doc.__mill_autoname_cleared) {
		return;
	}
	const meta = frappe.get_meta(frm.doctype);
	const autoname = meta.autoname || "";
	if (!autoname.startsWith("field:")) {
		return;
	}
	const fieldname = autoname.slice(6);
	const df = frappe.meta.get_docfield(frm.doctype, fieldname);
	if (!df?.read_only || frm.doc[fieldname] == null || frm.doc[fieldname] === "") {
		return;
	}
	frm.doc[fieldname] = null;
	frm.doc.__mill_autoname_cleared = 1;
	frm.refresh_field(fieldname);
};

frappe.ui.form.on("*", {
	refresh(frm) {
		millitrix.duplicate_autoname.clear_if_needed(frm);
	},
});
