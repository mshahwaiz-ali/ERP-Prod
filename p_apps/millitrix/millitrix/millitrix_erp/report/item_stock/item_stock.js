frappe.query_reports["Item_Stock"] = {
	filters: [
		{
			fieldname: "location_id",
			label: __("Location"),
			fieldtype: "Link",
			options: "Location",
		},
		{
			fieldname: "storeid",
			label: __("Store"),
			fieldtype: "Link",
			options: "Store Setup",
		},
		{
			fieldname: "itemcode",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item Setup",
		},
		{
			fieldname: "iclassid",
			label: __("Item Class"),
			fieldtype: "Link",
			options: "Item Class",
		},
		{
			fieldname: "partyid",
			label: __("Party"),
			fieldtype: "Link",
			options: "Party",
		},
		{
			fieldname: "show_zero_stock",
			label: __("Show Zero Stock"),
			fieldtype: "Check",
			default: 0,
		},
	],
};
