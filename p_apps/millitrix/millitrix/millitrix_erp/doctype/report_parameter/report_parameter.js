// Copyright (c) 2026, Millitrix and contributors
// Report Parameter — session defaults + readable Link labels (Location name, not id).

frappe.ui.form.on("Report Parameter", {
	async onload(frm) {
		if (!frm.is_new()) {
			return;
		}
		try {
			const defaults = await frappe.xcall(
				"millitrix.api.user_context.get_report_parameter_defaults"
			);
			for (const [fieldname, value] of Object.entries(defaults || {})) {
				if (value != null && value !== "" && !frm.doc[fieldname]) {
					await frm.set_value(fieldname, value);
				}
			}
		} catch (e) {
			// Non-blocking — user can still fill manually.
		}
	},

	setup(frm) {
		frm.set_query("location_id", () => ({
			filters: { description: ["!=", ""] },
		}));
	},
});
