frappe.query_reports["Sales_Item_Summary"] = {
	filters: [
		{fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
		 default: frappe.datetime.add_months(frappe.datetime.get_today(), -1), reqd: 1},
		{fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
		 default: frappe.datetime.get_today(), reqd: 1},
		{fieldname: "location_id", label: __("Location"), fieldtype: "Link", options: "Location"},
		{fieldname: "customerid", label: __("Customer"), fieldtype: "Link", options: "Party",
		 get_query: () => ({filters: {pcat_id: 13}})},
		{fieldname: "itemcode", label: __("Item"), fieldtype: "Link", options: "Item Setup"},
	],
};
