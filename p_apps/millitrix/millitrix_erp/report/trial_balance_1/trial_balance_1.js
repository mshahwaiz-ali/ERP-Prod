frappe.query_reports["Trial_Balance_1"] = {
	filters: [
		{fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
		 default: frappe.datetime.year_start(), reqd: 1},
		{fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
		 default: frappe.datetime.get_today(), reqd: 1},
		{fieldname: "location_id", label: __("Location"), fieldtype: "Link", options: "Location", reqd: 1},
		{fieldname: "accid", label: __("Account"), fieldtype: "Link", options: "Chart of Accounting"},
		{fieldname: "show_zero_values", label: __("Show Zero Values"), fieldtype: "Check"},
	],
};
