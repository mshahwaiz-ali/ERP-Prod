frappe.pages["sales-parameter-form"].on_page_load = function (wrapper) {
	millitrix.para_form.boot(wrapper, "sales");
};

frappe.pages["sales-parameter-form"].on_page_show = function (wrapper) {
	millitrix.para_form.on_page_show(wrapper, "sales");
};
