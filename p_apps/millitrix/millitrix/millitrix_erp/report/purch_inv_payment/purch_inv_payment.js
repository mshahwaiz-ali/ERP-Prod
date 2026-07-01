const _purch_inv_payment_filters = [
	{fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
	 default: frappe.datetime.add_months(frappe.datetime.get_today(), -1), reqd: 1},
	{fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
	 default: frappe.datetime.get_today(), reqd: 1},
	{fieldname: "location_id", label: __("Location"), fieldtype: "Link", options: "Location"},
	{fieldname: "partyid", label: __("Supplier"), fieldtype: "Link", options: "Party",
	 get_query: () => ({filters: {pcat_id: 12}})},
	{fieldname: "itemcode", label: __("Item"), fieldtype: "Link", options: "Item Setup"},
];

frappe.query_reports["Purch_Inv_Payment"] = {filters: _purch_inv_payment_filters};
frappe.query_reports["Purch_Inv_Pay_Detl"] = {filters: _purch_inv_payment_filters};
frappe.query_reports["Purch_Inv_Pay_Detl_Consider"] = {filters: _purch_inv_payment_filters};
