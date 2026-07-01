// Chart of Accounting — open tabbed setup (Oracle ChartOfAccount.fmb).
frappe.listview_settings["Chart of Accounting"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Chart Setup"), () => {
			frappe.set_route("chart-of-accounting-setup");
		});
	},
};
