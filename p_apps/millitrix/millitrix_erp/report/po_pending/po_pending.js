frappe.query_reports["Po_Pending"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "location_id",
			label: __("Location"),
			fieldtype: "Link",
			options: "Location",
		},
		{
			fieldname: "supplierid",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Party",
			get_query: () => ({filters: {pcat_id: 12}}),
		},
		{
			fieldname: "itemcode",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item Setup",
		},
		{
			fieldname: "brokerid",
			label: __("Broker"),
			fieldtype: "Link",
			options: "Party",
			get_query: () => ({filters: {pcat_id: 11}}),
		},
	],
};
