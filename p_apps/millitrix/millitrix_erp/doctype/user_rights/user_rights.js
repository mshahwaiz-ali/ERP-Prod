// Copyright (c) 2026, Millitrix and contributors

const PERM_FIELDS = [
	"canview",
	"canadd",
	"canedit",
	"candelete",
	"cansubmit",
	"canassign",
	"canunsubmit",
];

function _set_all_permissions(frm, value) {
	(frm.doc.module_permissions || []).forEach((row) => {
		PERM_FIELDS.forEach((field) => {
			frappe.model.set_value(row.doctype, row.name, field, value);
		});
	});
	frm.refresh_field("module_permissions");
}

function _fetch_module_name(moduleid) {
	if (!moduleid) {
		return Promise.resolve("");
	}
	return frappe.db.get_value("Module", String(moduleid), "module").then((r) => r.message?.module || "");
}

frappe.ui.form.on("User Rights", {
	refresh(frm) {
		frm.set_df_property("user_locations", "hidden", 1);

		frm.add_custom_button(
			__("Select All"),
			() => _set_all_permissions(frm, 1),
			__("Permissions")
		);
		frm.add_custom_button(
			__("Clear All"),
			() => _set_all_permissions(frm, 0),
			__("Permissions")
		);
	},

	get_all_modules(frm) {
		if (!frm.doc.get_all_modules) {
			return;
		}
		frappe.call({
			method: "millitrix.millitrix_erp.doctype.user_rights.user_rights.load_all_modules",
			callback(r) {
				const existing = new Set(
					(frm.doc.module_permissions || []).map((row) => String(row.moduleid))
				);
				(r.message || []).forEach((mod) => {
					if (existing.has(String(mod.moduleid))) {
						return;
					}
					const row = frm.add_child("module_permissions");
					row.moduleid = mod.moduleid;
					row.module_name = mod.module;
					row.user_level = row.user_level || "Level 1";
				});
				frm.refresh_field("module_permissions");
				frm.set_value("get_all_modules", 0);
			},
		});
	},
});

frappe.ui.form.on("Module Permission", {
	moduleid(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		_fetch_module_name(row.moduleid).then((name) => {
			frappe.model.set_value(cdt, cdn, "module_name", name);
		});
	},
});
