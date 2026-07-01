// Premium list views — meaningful first column, date filters, not ID-first.
frappe.provide("millitrix.list_view");

millitrix.list_view.apply_month_date_filter = (listview, date_field = "crdate") => {
	if (listview._millitrix_month_filter || listview.filter_area?.filter_list?.length) {
		return Promise.resolve(false);
	}
	const today = frappe.datetime.get_today();
	const month_start = frappe.datetime.month_start(today);
	listview._millitrix_month_filter = true;
	return listview.filter_area
		.add([[listview.doctype, date_field, "Between", [month_start, today], false]])
		.then(() => true)
		.catch(() => false);
};

millitrix.list_view.subject_fallback = (doc, title_field, fallback_field = "name") => {
	const primary = doc[title_field];
	if (primary) {
		return primary;
	}
	return doc[fallback_field] || doc.name || "";
};

millitrix.list_view.patch_subject_formatter = (doctype, title_field, fallback_field) => {
	const settings = frappe.listview_settings[doctype] || {};
	if (settings._millitrix_subject_patched) {
		return;
	}
	const prev_get_subject = settings.get_formate_value || settings.formatters?.[title_field];
	frappe.listview_settings[doctype] = {
		...settings,
		_millitrix_subject_patched: true,
		get_formate_value(doc, df) {
			if (df?.fieldname === title_field || df?.fieldname === "name") {
				return millitrix.list_view.subject_fallback(doc, title_field, fallback_field);
			}
			if (typeof prev_get_subject === "function") {
				return prev_get_subject(doc, df);
			}
			return doc[df.fieldname];
		},
	};
};
