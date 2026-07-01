// Copyright (c) 2026, Millitrix and contributors
// Employee Setup — Oracle Employee.fmx (Mill, Employee, Dept, Designation, Category, Salary…)

frappe.provide("millitrix.employee_setup");

millitrix.employee_setup.apply_scope = function (frm) {
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
};

frappe.ui.form.on("Employee Setup", {
	onload(frm) {
		millitrix.employee_setup.apply_scope(frm);
	},

	refresh(frm) {
		millitrix.employee_setup.apply_scope(frm);
	},
});
