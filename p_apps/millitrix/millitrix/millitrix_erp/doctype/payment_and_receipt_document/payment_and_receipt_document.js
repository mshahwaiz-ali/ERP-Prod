// Copyright (c) 2026, Millitrix and contributors
frappe.ui.form.on("Payment and Receipt Document", {
	amount(frm, cdt, cdn) {
		if (millitrix.pnr_invoice?.DOCTYPES?.has(frm.doctype)) {
			return;
		}
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
	},
});
