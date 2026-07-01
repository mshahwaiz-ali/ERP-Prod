// Deprecated — menu opens Party list directly. Old bookmark only.
frappe.pages["customer-setup"].on_page_load = function () {
	millitrix.party_list.open("13");
};
