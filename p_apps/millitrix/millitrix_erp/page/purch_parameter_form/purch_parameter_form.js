frappe.pages["purch-parameter-form"].on_page_load = function (wrapper) {
	millitrix.para_form.boot(wrapper, "purchase");
};

frappe.pages["purch-parameter-form"].on_page_show = function (wrapper) {
	millitrix.para_form.on_page_show(wrapper, "purchase");
};
