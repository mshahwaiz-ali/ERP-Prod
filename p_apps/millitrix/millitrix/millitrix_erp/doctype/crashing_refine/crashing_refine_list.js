// Crashing / Refine — premium list: Item first, not ID.
frappe.provide("millitrix.crashing_refine_list");

millitrix.crashing_refine_list.apply_default_filters = (listview) => {
	if (listview._millitrix_cr_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const mill = frappe.route_options?.millitrix_mill_id;
	if (mill) {
		pending.push(["Crashing Refine", "mill_id", "=", mill, false]);
		delete frappe.route_options.millitrix_mill_id;
	}
	const item = frappe.route_options?.millitrix_primary_item;
	if (item) {
		pending.push(["Crashing Refine", "primary_item", "=", item, false]);
		delete frappe.route_options.millitrix_primary_item;
	}
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["Crashing Refine", "crdate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_cr_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

millitrix.crashing_refine_list.apply_session_mill = (listview) => {
	if (listview._millitrix_cr_session_mill || listview.filter_area?.filter_list?.length) {
		return Promise.resolve(false);
	}
	return frappe
		.xcall("millitrix.api.user_context.get_user_scope")
		.then((scope) => {
			const mill = scope?.location_id;
			if (!mill || listview.filter_area?.filter_list?.length) {
				return false;
			}
			listview._millitrix_cr_session_mill = true;
			return listview.filter_area
				.add([["Crashing Refine", "mill_id", "=", mill, false]])
				.then(() => true);
		})
		.catch(() => false);
};

frappe.listview_settings["Crashing Refine"] = {
	hide_name_filter: true,
	add_fields: [
		"crashid",
		"crdate",
		"mill_id",
		"primary_item",
		"primary_output",
		"input_weight",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter("Crashing Refine", "primary_item", "crashid");
		}
		millitrix.crashing_refine_list.apply_default_filters(listview).then((applied) => {
			if (applied) {
				return;
			}
			millitrix.crashing_refine_list.apply_session_mill(listview).then((millApplied) => {
				if (
					!millApplied &&
					!listview.filter_area?.filter_list?.length &&
					millitrix.list_view?.apply_month_date_filter
				) {
					millitrix.list_view.apply_month_date_filter(listview, "crdate");
				}
			});
		});
	},
};
