// Sales Return — premium list: Item first, not SRET-xxx ID.
frappe.provide("millitrix.sales_return_list");

millitrix.sales_return_list.apply_default_filters = (listview) => {
	if (listview._millitrix_sr_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const customer = frappe.route_options?.millitrix_customerid;
	if (customer) {
		pending.push(["Sales Return", "customerid", "=", customer, false]);
		delete frappe.route_options.millitrix_customerid;
	}
	const item = frappe.route_options?.millitrix_itemcode;
	if (item) {
		pending.push(["Sales Return", "itemcode", "=", item, false]);
		delete frappe.route_options.millitrix_itemcode;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["Sales Return", "retdate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_sr_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["Sales Return"] = {
	hide_name_filter: true,
	add_fields: [
		"salesretno",
		"retdate",
		"itemcode",
		"customerid",
		"brokerid",
		"salesinvno",
		"amount",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter("Sales Return", "itemcode", "salesretno");
		}
		millitrix.sales_return_list.apply_default_filters(listview).then((applied) => {
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
