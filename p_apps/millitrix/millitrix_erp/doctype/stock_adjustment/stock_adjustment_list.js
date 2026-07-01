// Stock Adjustment — premium list: Item first, not STKADJ-xxx ID.
frappe.provide("millitrix.stock_adjustment_list");

millitrix.stock_adjustment_list.apply_default_filters = (listview) => {
	if (listview._millitrix_sa_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const item = frappe.route_options?.millitrix_primary_item;
	if (item) {
		pending.push(["Stock Adjustment", "primary_item", "=", item, false]);
		delete frappe.route_options.millitrix_primary_item;
	}
	const store = frappe.route_options?.millitrix_primary_store;
	if (store) {
		pending.push(["Stock Adjustment", "primary_store", "=", store, false]);
		delete frappe.route_options.millitrix_primary_store;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["Stock Adjustment", "sadate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_sa_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["Stock Adjustment"] = {
	hide_name_filter: true,
	add_fields: [
		"stkadjid",
		"sadate",
		"primary_item",
		"primary_store",
		"line_count",
		"total_amount",
		"remarks",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter(
				"Stock Adjustment",
				"primary_item",
				"stkadjid"
			);
		}
		millitrix.stock_adjustment_list.apply_default_filters(listview).then((applied) => {
			if (
				!applied &&
				!listview.filter_area?.filter_list?.length &&
				millitrix.list_view?.apply_month_date_filter
			) {
				millitrix.list_view.apply_month_date_filter(listview, "sadate");
			}
		});
	},
};
