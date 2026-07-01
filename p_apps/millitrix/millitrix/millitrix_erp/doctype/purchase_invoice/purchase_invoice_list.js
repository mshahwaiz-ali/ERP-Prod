// Purchase Invoice — premium list: Item first, not PI-xxx ID.
frappe.provide("millitrix.purchase_invoice_list");

millitrix.purchase_invoice_list.apply_default_filters = (listview) => {
	if (listview._millitrix_pi_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const supplier = frappe.route_options?.millitrix_supplierid;
	if (supplier) {
		pending.push(["Purchase Invoice", "supplierid", "=", supplier, false]);
		delete frappe.route_options.millitrix_supplierid;
	}
	const item = frappe.route_options?.millitrix_itemcode;
	if (item) {
		pending.push(["Purchase Invoice", "itemcode", "=", item, false]);
		delete frappe.route_options.millitrix_itemcode;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["Purchase Invoice", "invdate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_pi_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["Purchase Invoice"] = {
	hide_name_filter: true,
	add_fields: [
		"purchinvno",
		"invdate",
		"itemcode",
		"supplierid",
		"brokerid",
		"kantatype",
		"amount",
		"payable",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter("Purchase Invoice", "itemcode", "purchinvno");
		}
		millitrix.purchase_invoice_list.apply_default_filters(listview).then((applied) => {
			if (
				!applied &&
				!listview.filter_area?.filter_list?.length &&
				millitrix.list_view?.apply_month_date_filter
			) {
				millitrix.list_view.apply_month_date_filter(listview, "invdate");
			}
		});
	},
};
