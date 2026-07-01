frappe.pages["advance-payment-entry"].on_page_load = function () {
	millitrix.advance_pnr.open_new("payment");
};
