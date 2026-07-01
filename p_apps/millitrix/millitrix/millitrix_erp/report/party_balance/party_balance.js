frappe.query_reports["Party_Balance"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "location_id",
			label: __("Location"),
			fieldtype: "Link",
			options: "Location",
		},
		{
			fieldname: "partyid",
			label: __("Party"),
			fieldtype: "Link",
			options: "Party",
		},
		{
			fieldname: "pcat_id",
			label: __("Party Category"),
			fieldtype: "Link",
			options: "Party Category",
		},
		{
			fieldname: "show_zero_balance",
			label: __("Show Zero Balance"),
			fieldtype: "Check",
			default: 0,
		},
	],
};
