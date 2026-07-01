// Purchase Return Other Bill — premium list: Party first, not PROB-xxx ID.
frappe.provide("millitrix.purchase_return_other_bill_list");

millitrix.purchase_return_other_bill_list.apply_default_filters = (listview) => {
	if (listview._millitrix_prob_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const party = frappe.route_options?.millitrix_partyid;
	if (party) {
		pending.push(["Purchase Return Other Bill", "partyid", "=", party, false]);
		delete frappe.route_options.millitrix_partyid;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["Purchase Return Other Bill", "brdate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_prob_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["Purchase Return Other Bill"] = {
	hide_name_filter: true,
	add_fields: [
		"prbillno",
		"brdate",
		"partyid",
		"pbillno",
		"amount",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter(
				"Purchase Return Other Bill",
				"partyid",
				"prbillno"
			);
		}
		millitrix.purchase_return_other_bill_list.apply_default_filters(listview).then((applied) => {
			if (
				!applied &&
				!listview.filter_area?.filter_list?.length &&
				millitrix.list_view?.apply_month_date_filter
			) {
				millitrix.list_view.apply_month_date_filter(listview, "brdate");
			}
		});
	},
};
