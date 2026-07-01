// Deprecated — menu opens Party list directly. Old bookmark only.
frappe.pages["supplier-setup"].on_page_load = function () {
	millitrix.party_list.open("12");
};
