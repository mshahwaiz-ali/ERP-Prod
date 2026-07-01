// Copyright (c) 2026, Millitrix and contributors
// Store Setup — Oracle IN_Stores.fmx

frappe.provide("millitrix.store_setup");

millitrix.store_setup.apply_scope = function (frm) {
	frappe.call({
		method: "millitrix.api.user_context.get_user_scope",
		callback(r) {
			const scope = r.message || {};
			const locations = scope.bypass ? [] : scope.allowed_locations || [];
			frm.set_query("location_id", () => {
				if (locations.length) {
					return { filters: { name: ["in", locations] } };
				}
				return {};
			});
			if (frm.is_new() && !frm.doc.location_id && scope.location_id) {
				frm.set_value("location_id", scope.location_id);
			}
		},
	});

	if (frm.fields_dict.parentid) {
		frm.set_query("parentid", () => {
			const filters = {};
			if (frm.doc.location_id) {
				filters.location_id = frm.doc.location_id;
			}
			if (!frm.is_new()) {
				filters.name = ["!=", frm.doc.name];
			}
			return { filters };
		});
	}
};

frappe.ui.form.on("Store Setup", {
	onload(frm) {
		millitrix.store_setup.apply_scope(frm);
	},

	refresh(frm) {
		millitrix.store_setup.apply_scope(frm);
	},
});
