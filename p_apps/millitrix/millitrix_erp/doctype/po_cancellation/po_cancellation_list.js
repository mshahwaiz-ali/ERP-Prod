// PO Cancellation — premium list: Party first, not POC-xxx ID.
frappe.provide("millitrix.po_cancellation_list");

millitrix.po_cancellation_list.apply_default_filters = (listview) => {
	if (listview._millitrix_poc_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const party = frappe.route_options?.millitrix_partyid;
	if (party) {
		pending.push(["PO Cancellation", "partyid", "=", party, false]);
		delete frappe.route_options.millitrix_partyid;
	}
	const item = frappe.route_options?.millitrix_primary_item;
	if (item) {
		pending.push(["PO Cancellation", "primary_item", "=", item, false]);
		delete frappe.route_options.millitrix_primary_item;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["PO Cancellation", "candate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_poc_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["PO Cancellation"] = {
	hide_name_filter: true,
	add_fields: [
		"pocid",
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
			millitrix.list_view.patch_subject_formatter("PO Cancellation", "partyid", "pocid");
		}
		millitrix.po_cancellation_list.apply_default_filters(listview).then((applied) => {
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
