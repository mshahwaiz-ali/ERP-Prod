// Copyright (c) 2026, Millitrix and contributors

frappe.provide("millitrix.purchase_invoice");

const PI = "Purchase Invoice";
const PI_DETAIL = "Purchase Invoice Detail";
const PI_DOCTYPE_ID = "Purchase Invoice";

if (millitrix.invoice_form && millitrix.invoice_form.register) {
	millitrix.invoice_form.register(PI, PI_DETAIL, true);
}

function pi_header_ready(frm) {
	return frm.doc.itemcode && frm.doc.brokerid && frm.doc.supplierid;
}

function pi_line_is_blank(row) {
	return !row.ponumber && !row.truckno && !flt(row.truckqty) && !flt(row.inkanta) && !flt(row.delikanta);
}

function pi_sync_item_defaults(frm) {
	if (!frm.doc.itemcode || frm.doc.docstatus !== 0) {
		return;
	}
	frappe
		.xcall("millitrix.api.purchase_invoice_form.fetch_item_header_defaults", {
			itemcode: frm.doc.itemcode,
		})
		.then((defaults) => {
			if (!defaults) {
				return;
			}
			if (defaults.mundtype && frm.doc.mundtype !== defaults.mundtype) {
				frm.set_value("mundtype", defaults.mundtype);
			}
			if (defaults.amntby && frm.doc.amntby !== defaults.amntby) {
				frm.set_value("amntby", defaults.amntby);
			}
			if (frm.fields_dict.amntby) {
				frm.set_df_property("amntby", "read_only", defaults.is_bardana ? 1 : 0);
			}
			if (millitrix.invoice_form) {
				millitrix.invoice_form.apply_field_rules(frm);
			}
		})
		.catch(() => {});
}

function pi_fetch_open_lines(frm, force_replace) {
	if (!pi_header_ready(frm) || frm.doc.docstatus !== 0 || millitrix.is_form_read_only(frm)) {
		return;
	}
	frappe.call({
		method: "millitrix.api.invoice_form.fetch_open_po_lines",
		args: { doc: frm.doc },
		freeze: true,
		freeze_message: __("Fetching open PO lines..."),
		callback(r) {
			const lines = r.message || [];
			if (!lines.length) {
				return;
			}
			const rows = frm.doc.details || [];
			const can_replace =
				force_replace || !rows.length || rows.every((row) => pi_line_is_blank(row));
			if (can_replace) {
				frm.clear_table("details");
			}
			lines.forEach((line) => {
				const row = frm.add_child("details");
				Object.assign(row, line);
			});
			frm.refresh_field("details");
			millitrix.invoice_form.recalc(frm, true);
		},
	});
}

frappe.ui.form.on(PI, {
	setup(frm) {
		frm.set_query("ponumber", "details", () => {
			const filters = {
				docstatus: 1,
				status: ["in", ["Initial", "In Progress", "IN", "IP"]],
			};
			if (frm.doc.location_id) {
				filters.location_id = frm.doc.location_id;
			}
			if (frm.doc.itemcode) {
				filters.itemcode = frm.doc.itemcode;
			}
			if (frm.doc.brokerid) {
				filters.brokerid = frm.doc.brokerid;
			}
			if (frm.doc.supplierid) {
				filters.supplierid = frm.doc.supplierid;
			}
			if (frm.doc.sub_partyid) {
				filters.sub_partyid = frm.doc.sub_partyid;
			}
			return { filters };
		});
	},

	refresh(frm) {
		if (frm.doc.docstatus === 0 && !millitrix.is_form_read_only(frm)) {
			frm.add_custom_button(__("Get Open PO Lines"), () => pi_fetch_open_lines(frm, true), __("Fetch"));
		}

		if (!frm.is_new() && frm.doc.docstatus === 1) {
			millitrix.knockoff.add_accounting_button(frm, { document_id_field: "purchinvno" });
		}

		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", PI_DOCTYPE_ID);
		}

		if (millitrix.child_table) {
			millitrix.child_table.schedule_render_grid_totals(frm, ["details"]);
		}
	},

	onload(frm) {
		pi_sync_item_defaults(frm);
	},

	itemcode(frm) {
		pi_sync_item_defaults(frm);
		pi_fetch_open_lines(frm, false);
	},
	brokerid(frm) {
		pi_fetch_open_lines(frm, false);
	},
	supplierid(frm) {
		pi_fetch_open_lines(frm, false);
	},
	sub_partyid(frm) {
		pi_fetch_open_lines(frm, false);
	},
});
