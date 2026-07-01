// SO Cancellation — premium list: Party first, not SOC-xxx ID.
frappe.provide("millitrix.so_cancellation_list");

millitrix.so_cancellation_list.apply_default_filters = (listview) => {
	if (listview._millitrix_soc_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const party = frappe.route_options?.millitrix_partyid;
	if (party) {
		pending.push(["SO Cancellation", "partyid", "=", party, false]);
		delete frappe.route_options.millitrix_partyid;
	}
	const item = frappe.route_options?.millitrix_primary_item;
	if (item) {
		pending.push(["SO Cancellation", "primary_item", "=", item, false]);
		delete frappe.route_options.millitrix_primary_item;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["SO Cancellation", "candate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_soc_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["SO Cancellation"] = {
	hide_name_filter: true,
	add_fields: [
		"socid",
		"candate",
		"partyid",
		"primary_item",
		"total_cancel_qty",
		"line_count",
		"remarks",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter("SO Cancellation", "partyid", "socid");
		}
		millitrix.so_cancellation_list.apply_default_filters(listview).then((applied) => {
			if (
				!applied &&
				!listview.filter_area?.filter_list?.length &&
				millitrix.list_view?.apply_month_date_filter
			) {
				millitrix.list_view.apply_month_date_filter(listview, "candate");
			}
		});
	},
};
