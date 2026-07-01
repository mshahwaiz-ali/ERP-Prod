frappe.query_reports["Cust_Aging"] = {
	filters: [
		{fieldname: "as_of_date", label: __("As Of Date"), fieldtype: "Date",
		 default: frappe.datetime.get_today(), reqd: 1},
		{fieldname: "location_id", label: __("Location"), fieldtype: "Link", options: "Location"},
		{fieldname: "partyid", label: __("Customer"), fieldtype: "Link", options: "Party",
		 get_query: () => ({filters: {pcat_id: 13}})},
		{fieldname: "show_zero", label: __("Show Zero Balance"), fieldtype: "Check", default: 0},
	],
};
