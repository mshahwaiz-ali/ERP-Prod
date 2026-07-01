frappe.query_reports["Party_Info"] = {
	filters: [
		{fieldname: "pcat_id", label: __("Party Category"), fieldtype: "Link", options: "Party Category"},
		{fieldname: "cityid", label: __("City"), fieldtype: "Link", options: "City Setup"},
		{fieldname: "partyid", label: __("Party"), fieldtype: "Link", options: "Party"},
	],
};
