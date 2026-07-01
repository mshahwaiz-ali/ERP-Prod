frappe.query_reports["Item_Wise_Stock"] = {
	filters: [
		{fieldname: "location_id", label: __("Location"), fieldtype: "Link", options: "Location"},
		{fieldname: "itemcode", label: __("Item"), fieldtype: "Link", options: "Item Setup"},
		{fieldname: "iclassid", label: __("Item Class"), fieldtype: "Link", options: "Item Class"},
		{fieldname: "show_zero_stock", label: __("Show Zero Stock"), fieldtype: "Check", default: 0},
	],
};
