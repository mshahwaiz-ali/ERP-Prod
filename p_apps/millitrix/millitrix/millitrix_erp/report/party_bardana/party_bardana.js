frappe.query_reports["Party_Bardana"] = {
	filters: [
		{fieldname: "location_id", label: __("Location"), fieldtype: "Link", options: "Location"},
		{fieldname: "partyid", label: __("Party"), fieldtype: "Link", options: "Party"},
		{fieldname: "storeid", label: __("Store"), fieldtype: "Link", options: "Store Setup"},
		{fieldname: "itemcode", label: __("Item"), fieldtype: "Link", options: "Item Setup"},
		{fieldname: "show_zero_stock", label: __("Show Zero Stock"), fieldtype: "Check", default: 0},
	],
};
