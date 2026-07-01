frappe.query_reports["Gl_Voucher"] = {
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
			fieldname: "accid",
			label: __("Account"),
			fieldtype: "Link",
			options: "Chart of Accounting",
		},
		{
			fieldname: "doctypeid",
			label: __("Doc Type"),
			fieldtype: "Data",
		},
	],
};
