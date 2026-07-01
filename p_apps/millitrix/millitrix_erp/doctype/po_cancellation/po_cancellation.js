// Copyright (c) 2026, Millitrix and contributors
// Oracle POCancel.fmb parity — open PO lines, balance qty, cancel validation.

frappe.ui.form.on("PO Cancellation", {
	onload(frm) {
		if (millitrix.form_links?.apply_default_location) {
			millitrix.form_links.apply_default_location(frm);
		}
	},

	refresh(frm) {
		if (frm.fields_dict.partyid) {
			frm.set_query("partyid", () => ({
				filters: { pcat_id: ["in", ["12"]] },
			}));
		}
		frm.set_query("ponumber", "details", () => ({
			query: "millitrix.utils.po_cancellation_form.search_open_purchase_orders",
			filters: {
				partyid: frm.doc.partyid,
				location_id: frm.doc.location_id,
			},
		}));
	},

	partyid(frm) {
		if (frm.doc.details?.length) {
			frappe.show_alert({
				message: __("Party changed — verify PO lines still match"),
				indicator: "orange",
			});
		}
	},
});

frappe.ui.form.on("PO Cancellation Detail", {
	ponumber(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.ponumber) {
			return;
		}
		frappe.call({
			method: "millitrix.api.invoice_form.get_open_truck_qty",
			args: {
				order_doctype: "Purchase Order",
				order_name: row.ponumber,
			},
			error: millitrix.api.default_error(__("Could not load open truck qty")),
			callback(r) {
				const balance = flt(r.message);
				frappe.model.set_value(cdt, cdn, "truckqty", balance);
				if (!flt(row.cancelqty)) {
					frappe.model.set_value(cdt, cdn, "cancelqty", 0);
				}
			},
		});
	},

	cancelqty(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.ponumber || !flt(row.cancelqty)) {
			return;
		}
		if (flt(row.cancelqty) <= 0) {
			frappe.msgprint(__("Cancel Qty must be greater than zero"));
			return;
		}
		if (flt(row.cancelqty) > flt(row.truckqty)) {
			frappe.msgprint(
				__("Only {0} quantity remaining on this order.", [flt(row.truckqty)])
			);
		}
	},
});
