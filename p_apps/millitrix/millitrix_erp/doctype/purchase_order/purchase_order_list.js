// Purchase Order — premium list: Item first, not PO-xxx ID.
frappe.provide("millitrix.purchase_order_list");

millitrix.purchase_order_list.apply_default_filters = (listview) => {
	if (listview._millitrix_po_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const supplier = frappe.route_options?.millitrix_supplierid;
	if (supplier) {
		pending.push(["Purchase Order", "supplierid", "=", supplier, false]);
		delete frappe.route_options.millitrix_supplierid;
	}
	const item = frappe.route_options?.millitrix_itemcode;
	if (item) {
		pending.push(["Purchase Order", "itemcode", "=", item, false]);
		delete frappe.route_options.millitrix_itemcode;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["Purchase Order", "podate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_po_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["Purchase Order"] = {
	hide_name_filter: true,
	add_fields: [
		"ponumber",
		"podate",
		"potype",
		"itemcode",
		"supplierid",
		"brokerid",
		"rate",
		"amount",
		"status",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter("Purchase Order", "itemcode", "ponumber");
		}
		millitrix.purchase_order_list.apply_default_filters(listview).then((applied) => {
			if (
				!applied &&
				!listview.filter_area?.filter_list?.length &&
				millitrix.list_view?.apply_month_date_filter
			) {
				millitrix.list_view.apply_month_date_filter(listview, "podate");
			}
		});
	},
};
