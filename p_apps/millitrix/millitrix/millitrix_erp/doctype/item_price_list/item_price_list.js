// Copyright (c) 2026, Millitrix and contributors
// Oracle Item_Price_List.fmb — mill-scoped daily item rates.

frappe.provide("millitrix.item_price_list");

millitrix.item_price_list.apply_scope = function (frm) {
	frappe.call({
		method: "millitrix.api.user_context.get_user_scope",
		callback(r) {
			const scope = r.message || {};
			const locations = scope.bypass ? [] : scope.allowed_locations || [];
			frm.set_query("location_id", () => {
				if (locations.length) {
					return { filters: { name: ["in", locations] } };
				}
				return {};
			});
			if (frm.is_new() && !frm.doc.location_id && scope.location_id) {
				frm.set_value("location_id", scope.location_id);
			}
		},
	});
};

frappe.ui.form.on("Item Price List", {
	onload(frm) {
		millitrix.item_price_list.apply_scope(frm);
	},

	refresh(frm) {
		millitrix.item_price_list.apply_scope(frm);
	},

	itemcode(frm) {
		if (!frm.doc.itemcode) {
			return;
		}
		frappe.db
			.get_value("Item Setup", frm.doc.itemcode, ["bagweight", "mundtype"])
			.then((r) => {
				const row = r.message || {};
				if (flt(row.bagweight)) {
					frm.set_value("bagweight", row.bagweight);
				}
			})
			.catch(() => {
				frappe.msgprint(__("Could not load item defaults"));
			});
	},
});
