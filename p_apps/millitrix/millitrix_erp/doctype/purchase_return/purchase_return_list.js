// Purchase Return — premium list: Item first, not PRET-xxx ID.
frappe.provide("millitrix.purchase_return_list");

millitrix.purchase_return_list.apply_default_filters = (listview) => {
	if (listview._millitrix_pr_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const supplier = frappe.route_options?.millitrix_supplierid;
	if (supplier) {
		pending.push(["Purchase Return", "supplierid", "=", supplier, false]);
		delete frappe.route_options.millitrix_supplierid;
	}
	const item = frappe.route_options?.millitrix_itemcode;
	if (item) {
		pending.push(["Purchase Return", "itemcode", "=", item, false]);
		delete frappe.route_options.millitrix_itemcode;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["Purchase Return", "retdate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_pr_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["Purchase Return"] = {
	hide_name_filter: true,
	add_fields: [
		"purchretno",
		"retdate",
		"itemcode",
		"supplierid",
		"brokerid",
		"purchinvno",
		"amount",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter("Purchase Return", "itemcode", "purchretno");
		}
		millitrix.purchase_return_list.apply_default_filters(listview).then((applied) => {
			if (
				!applied &&
				!listview.filter_area?.filter_list?.length &&
				millitrix.list_view?.apply_month_date_filter
			) {
				millitrix.list_view.apply_month_date_filter(listview, "retdate");
			}
		});
	},
};
