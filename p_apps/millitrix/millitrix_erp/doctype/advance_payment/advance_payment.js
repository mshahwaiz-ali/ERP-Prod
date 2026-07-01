// Copyright (c) 2026, Millitrix and contributors
frappe.ui.form.on("Advance Payment", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "Advance Payment");
		}
	},

	refresh(frm) {
		frm.set_query("partyid", () => ({
			filters: { pcat_id: ["in", ["12"]] },
		}));
		frm.set_query("bankaccid", () => ({}));
		millitrix.advance_pnr.apply_payment_fetch_labels(frm);
		millitrix.knockoff.add_accounting_button(frm, {
			document_id_field: "pnrno",
			method: "millitrix.api.knockoff.get_advance_accounting_lines",
			flow: "payment",
		});
	},

	amount(frm) {
		if (frm.doc.__islocal && frm.doc.amount) {
			frm.set_value("balance", frm.doc.amount);
		}
	},
});
