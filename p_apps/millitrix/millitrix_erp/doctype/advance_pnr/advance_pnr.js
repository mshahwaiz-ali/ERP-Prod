// Copyright (c) 2026, Millitrix and contributors
frappe.ui.form.on("Advance PNR", {
	onload(frm) {
		millitrix.advance_pnr.apply_form_defaults(frm);
		if (!frm.doc.doctypeid) {
			const flow = millitrix.advance_pnr.flow_key(frm);
			frm.set_value(
				"doctypeid",
				flow === "receipt" ? "Advance Receipt" : "Advance Payment"
			);
		}
	},
	refresh(frm) {
		millitrix.advance_pnr.apply_form_labels(frm);
		frm.set_query("bankaccid", () => ({}));
		const flow = millitrix.advance_pnr.flow_key(frm);
		millitrix.advance_pnr.apply_field_order(frm);
		millitrix.knockoff.add_accounting_button(frm, {
			document_id_field: "pnrno",
			method: "millitrix.api.knockoff.get_advance_accounting_lines",
			flow,
		});
	},
	advance_flow(frm) {
		millitrix.advance_pnr.apply_form_labels(frm);
		millitrix.advance_pnr.set_party_query(frm, millitrix.advance_pnr.flow_key(frm));
		millitrix.advance_pnr.apply_field_order(frm);
		if (frm.doc.partyid) {
			frm.set_value("partyid", "");
		}
		const flow = millitrix.advance_pnr.flow_key(frm);
		frm.set_value(
			"doctypeid",
			flow === "receipt" ? "Advance Receipt" : "Advance Payment"
		);
	},
	amount(frm) {
		if (frm.doc.__islocal && frm.doc.amount) {
			frm.set_value("balance", frm.doc.amount);
		}
	},
});
