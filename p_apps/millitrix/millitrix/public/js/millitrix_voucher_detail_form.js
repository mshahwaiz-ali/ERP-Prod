// Copyright (c) 2026, Millitrix and contributors
// Voucher Transaction Detail — Manual Journal shows Employee/Transaction/Bank Cash GL; Closing does not.

frappe.provide("millitrix.voucher_detail");

millitrix.voucher_detail.MANUAL_JOURNAL_ONLY = ["empno", "trans_id", "bnkcash_gl"];

millitrix.voucher_detail.MANUAL_GRID_HIDDEN = [
	"partyid",
	"party_name",
	"itemcode",
	"item_name",
	"account_name",
];

millitrix.voucher_detail.MANUAL_GRID_VISIBLE = ["accid", "debit", "credit", "detail"];

millitrix.voucher_detail.set_optional_fields = function (frm, show) {
	const grid = frm.fields_dict.details?.grid;
	if (!grid) {
		return;
	}
	millitrix.voucher_detail.MANUAL_JOURNAL_ONLY.forEach((fieldname) => {
		grid.update_docfield_property(fieldname, "hidden", show ? 0 : 1);
	});
	grid.refresh();
};

millitrix.voucher_detail.set_manual_grid = function (frm) {
	const grid = frm.fields_dict.details?.grid;
	if (!grid?.update_docfields_property) {
		return;
	}
	millitrix.voucher_detail.MANUAL_GRID_HIDDEN.forEach((fieldname) => {
		grid.update_docfields_property(fieldname, "hidden", 1);
	});
	millitrix.voucher_detail.MANUAL_GRID_VISIBLE.forEach((fieldname) => {
		grid.update_docfields_property(fieldname, "hidden", 0);
	});
	frm.refresh_field("details");
};

frappe.ui.form.on("Closing and Adjustment Entries", {
	refresh(frm) {
		millitrix.voucher_detail.set_optional_fields(frm, false);
	},
});

frappe.ui.form.on("Voucher Transaction", {
	refresh(frm) {
		millitrix.voucher_detail.set_optional_fields(frm, true);
		millitrix.voucher_detail.set_manual_grid(frm);
	},
});
