// Copyright (c) 2026, Millitrix and contributors
frappe.ui.form.on("Cash and Bank Voucher", {
	refresh(frm) {
		millitrix.knockoff.apply_cnb_document_grid(
			frm,
			"documents",
			millitrix.knockoff.CNB_DOCUMENT_PARTY_GRID
		);
		millitrix.knockoff.add_load_button(frm, {
			child_field: "documents",
			date_field: "vouchdate",
			prompt_party: true,
			resolve_flow(frm) {
				return millitrix.knockoff.vouchmode_flow(frm.doc.vouchmode);
			},
			map_row: millitrix.knockoff.CNB_DOCUMENT_MAP,
			after_load(frm) {
				millitrix.knockoff.recalc_child_total(frm, "documents", "amount");
			},
		});
	},
});

frappe.ui.form.on("Cash and Bank Voucher Document", {
	amount(frm, cdt, cdn) {
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
	},
});
