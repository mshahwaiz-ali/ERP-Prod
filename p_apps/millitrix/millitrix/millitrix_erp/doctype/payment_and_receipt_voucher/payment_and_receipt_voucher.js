// Copyright (c) 2026, Millitrix and contributors
frappe.ui.form.on("Payment and Receipt Voucher", {
	onload(frm) {
		millitrix.advance_pnr.apply_form_defaults(frm);
	},
	refresh(frm) {
		const pnr_type = frm.doc.pnr_type || "Invoice";
		const is_advance = pnr_type === "Advance";
		const is_discount = pnr_type === "Discount";

		frm.set_df_property("documents", "hidden", is_advance);
		frm.set_df_property("instruments", "hidden", is_discount);

		if (is_advance) {
			millitrix.knockoff.recalc_child_total(frm, "instruments", "amount");
			return;
		}

		millitrix.knockoff.add_load_button(frm, {
			child_field: "documents",
			date_field: "pnrdate",
			map_row: millitrix.knockoff.PNR_DOCUMENT_MAP,
			after_load(frm) {
				millitrix.knockoff.recalc_child_total(frm, "documents", "amount");
			},
		});

		if (is_discount) {
			millitrix.knockoff.recalc_child_total(frm, "documents", "amount");
		}
	},
	pnr_type(frm) {
		if (frm.doc.pnr_type === "Advance") {
			frm.clear_table("documents");
			frm.refresh_field("documents");
		} else if (frm.doc.pnr_type === "Discount") {
			frm.clear_table("instruments");
			frm.refresh_field("instruments");
		}
		frm.trigger("refresh");
	},
	documents_remove(frm) {
		if (frm.doc.pnr_type !== "Advance") {
			millitrix.knockoff.recalc_child_total(frm, "documents", "amount");
		}
	},
	instruments_remove(frm) {
		if (frm.doc.pnr_type === "Advance") {
			millitrix.knockoff.recalc_child_total(frm, "instruments", "amount");
		}
	},
});

frappe.ui.form.on("Payment and Receipt Document", {
	amount(frm, cdt, cdn) {
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
		if (frm.doc.pnr_type !== "Advance") {
			millitrix.knockoff.recalc_child_total(frm, "documents", "amount");
		}
	},
});

frappe.ui.form.on("Payment and Receipt Instrument", {
	amount(frm) {
		if (frm.doc.pnr_type === "Advance") {
			millitrix.knockoff.recalc_child_total(frm, "instruments", "amount");
		}
	},
});
