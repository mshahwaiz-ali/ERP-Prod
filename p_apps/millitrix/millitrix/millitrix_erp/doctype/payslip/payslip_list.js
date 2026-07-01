// PaySlip — premium list: Salary Month first, not PS-xxx ID.
frappe.provide("millitrix.payslip_list");

millitrix.payslip_list.apply_default_filters = (listview) => {
	if (listview._millitrix_ps_filters_applied) {
		return Promise.resolve(false);
	}
	const pending = [];
	const from_date = frappe.route_options?.millitrix_from_date;
	const to_date = frappe.route_options?.millitrix_to_date;
	if (from_date && to_date) {
		pending.push(["PaySlip", "pdate", "Between", [from_date, to_date], false]);
		delete frappe.route_options.millitrix_from_date;
		delete frappe.route_options.millitrix_to_date;
	}
	const paymonth = frappe.route_options?.millitrix_paymonth;
	if (paymonth) {
		pending.push(["PaySlip", "paymonth", "=", paymonth, false]);
		delete frappe.route_options.millitrix_paymonth;
	}
	if (!pending.length) {
		return Promise.resolve(false);
	}
	listview._millitrix_ps_filters_applied = true;
	return listview.filter_area.add(pending).then(() => true);
};

frappe.listview_settings["PaySlip"] = {
	hide_name_filter: true,
	add_fields: [
		"pslipid",
		"pdate",
		"paymonth",
		"primary_employee",
		"employee_count",
		"total_salary",
		"remarks",
		"docstatus",
	],

	onload(listview) {
		if (millitrix.list_view?.patch_subject_formatter) {
			millitrix.list_view.patch_subject_formatter("PaySlip", "paymonth", "pslipid");
		}
		millitrix.payslip_list.apply_default_filters(listview).then((applied) => {
			if (
				!applied &&
				!listview.filter_area?.filter_list?.length &&
				millitrix.list_view?.apply_month_date_filter
			) {
				millitrix.list_view.apply_month_date_filter(listview, "pdate");
			}
		});
	},
};
