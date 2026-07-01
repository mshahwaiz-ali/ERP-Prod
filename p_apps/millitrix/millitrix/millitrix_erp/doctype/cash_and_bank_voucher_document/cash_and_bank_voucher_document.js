// Copyright (c) 2026, Millitrix and contributors
frappe.ui.form.on("Cash and Bank Voucher Document", {
	amount(frm, cdt, cdn) {
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
	},
});
