// Copyright (c) 2026, Millitrix and contributors

frappe.ui.form.on("Payment and Receipt Instrument", {
	pnrmode(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const mode = (row.pnrmode || "").toLowerCase();
		if (mode === "cash") {
			frappe.model.set_value(cdt, cdn, "bankaccid", null);
		}
	},
});
