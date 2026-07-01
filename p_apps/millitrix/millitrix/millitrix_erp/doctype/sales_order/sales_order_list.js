// Sales Order — premium list: Item first, not SO-xxx ID.
frappe.provide("millitrix.sales_order_list");

millitrix.sales_order_list.apply_default_filters = (listview) => {
	if (listview._millitrix_so_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const customer = frappe.route_options?.millitrix_customerid;
	if (customer) {
		pending.push(["Sales Order", "customerid", "=", customer, false]);
		delete frappe.route_options.millitrix_customerid;
	}
	const item = frappe.route_options?.millitrix_itemcode;
	if (item) {
		pending.push(["Sales Order", "itemcode", "=", item, false]);
		delete frappe.route_options.millitrix_itemcode;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["Sales Order", "sodate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_so_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["Sales Order"] = {
	hide_name_filter: true,
	add_fields: [
		"sonumber",
		"sodate",
		"sotype",
		"itemcode",
		"customerid",
		"brokerid",
		"rate",
		"amount",
		"status",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter("Sales Order", "itemcode", "sonumber");
		}
		millitrix.sales_order_list.apply_default_filters(listview).then((applied) => {
			if (
				!applied &&
				!listview.filter_area?.filter_list?.length &&
				millitrix.list_view?.apply_month_date_filter
			) {
				millitrix.list_view.apply_month_date_filter(listview, "sodate");
			}
		});
	},
};
