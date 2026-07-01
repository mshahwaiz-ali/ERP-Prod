// In Out Gate Pass — premium list: Item first, not GP number.
frappe.provide("millitrix.gate_pass_list");

millitrix.gate_pass_list.apply_default_filters = (listview) => {
	if (listview._millitrix_gp_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const gptype = frappe.route_options?.millitrix_gptype;
	if (gptype) {
		pending.push(["In Out Gate Pass", "gptype", "=", gptype, false]);
		delete frappe.route_options.millitrix_gptype;
	}
	const party = frappe.route_options?.millitrix_partyid;
	if (party) {
		pending.push(["In Out Gate Pass", "partyid", "=", party, false]);
		delete frappe.route_options.millitrix_partyid;
	}
	const item = frappe.route_options?.millitrix_itemcode;
	if (item) {
		pending.push(["In Out Gate Pass", "itemcode", "=", item, false]);
		delete frappe.route_options.millitrix_itemcode;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["In Out Gate Pass", "gpdate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_gp_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["In Out Gate Pass"] = {
	hide_name_filter: true,
	add_fields: ["gatepassno", "gpdate", "gptype", "partyid", "itemcode", "docstatus"],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter("In Out Gate Pass", "itemcode", "gatepassno");
		}
		millitrix.gate_pass_list.apply_default_filters(listview).then((applied) => {
			if (
				!applied &&
				!listview.filter_area?.filter_list?.length &&
				millitrix.list_view?.apply_month_date_filter
			) {
				millitrix.list_view.apply_month_date_filter(listview, "gpdate");
			}
		});
	},
};
