// Copyright (c) 2026, Millitrix and contributors
// Other Contacts — party categories other than Broker / Supplier / Customer.

const OTHER_CONTACT_PCAT_EXCLUDE = ["11", "12", "13"];

frappe.ui.form.on("Other Contact Setup", {
	refresh(frm) {
		frm.set_query("pcat_id", () => ({
			filters: { name: ["not in", OTHER_CONTACT_PCAT_EXCLUDE] },
		}));
		frm.set_query("cityid", () => ({ filters: {} }));
		if (frm.fields_dict.accid) {
			frm.set_query("accid", () => ({
				filters: { chartlevel: 5, transflag: "Yes" },
			}));
		}
	},
});
