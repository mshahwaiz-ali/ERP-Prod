frappe.query_reports["Sip_Outstanding"] = {
	filters: [
		{
			fieldname: "as_of_date",
			label: __("As Of Date"),
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
			label: __("Customer"),
			fieldtype: "Link",
			options: "Party",
			get_query: () => ({filters: {pcat_id: 13}}),
		},
		{
			fieldname: "itemcode",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item Setup",
		},
		{
			fieldname: "from_date",
			label: __("Invoice From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("Invoice To Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "show_zero",
			label: __("Show Fully Paid"),
			fieldtype: "Check",
			default: 0,
		},
	],
};
