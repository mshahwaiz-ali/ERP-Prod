// Copyright (c) 2026, Millitrix and contributors

frappe.provide("millitrix.invoice_form");

millitrix.invoice_form = {
	HEADER_FIELDS: [
		"itemcode",
		"amntby",
		"kantatype",
		"brokery",
		"brokery_auto_calc",
		"brokery_dr_supplier",
		"borrow",
		"brokerid",
		"supplierid",
		"customerid",
	],
	LINE_FIELDS: [
		"ponumber",
		"sonumber",
		"inkanta",
		"dust",
		"storeid",
		"bagid",
		"truckno",
		"truckadv",
		"truckqty",
		"cartage",
		"bagqty",
		"bagweight",
		"bagrate",
		"bags_are",
		"emptybags",
		"delikanta",
		"lessweight",
		"rate",
		"discount",
		"labouramnt",
		"brokeramnt",
	],

	register(doctype, detail_doctype, is_purchase) {
		const recalc = (frm) => millitrix.invoice_form.recalc(frm, is_purchase);
		const refresh_grid_totals = (frm) => {
			if (millitrix.child_table) {
				millitrix.child_table.schedule_render_grid_totals(frm, ["details"]);
			}
		};

		const parent_handlers = {
			refresh(frm) {
				millitrix.invoice_form.apply_field_rules(frm);
				if (millitrix.child_table) {
					millitrix.child_table.setup(frm);
				}
			},
			details_add(frm) {
				recalc(frm);
				refresh_grid_totals(frm);
			},
			details_remove(frm) {
				recalc(frm);
				refresh_grid_totals(frm);
			},
			kantatype(frm) {
				millitrix.invoice_form.apply_field_rules(frm);
				recalc(frm);
			},
			amntby(frm) {
				millitrix.invoice_form.apply_field_rules(frm);
				recalc(frm);
			},
		};
		millitrix.invoice_form.HEADER_FIELDS.forEach((field) => {
			if (!parent_handlers[field]) {
				parent_handlers[field] = recalc;
			}
		});
		frappe.ui.form.on(doctype, parent_handlers);

		const child_handlers = {};
		millitrix.invoice_form.LINE_FIELDS.forEach((field) => {
			child_handlers[field] = recalc;
		});
		frappe.ui.form.on(detail_doctype, child_handlers);
	},

	apply_field_rules(frm) {
		const auto_brokery = millitrix.invoice_form.is_yes(frm.doc.brokery_auto_calc);
		const brokery_paid = (frm.doc.brokery || "").toLowerCase() === "paid";
		const kanta = millitrix.invoice_form.normalize_kanta(frm.doc.kantatype);
		const amntby = millitrix.invoice_form.normalize_amntby(frm.doc.amntby);

		["amount", "payable", "receivable", "brokerypayable", "brokeramnt"].forEach((field) => {
			if (frm.fields_dict[field]) {
				frm.set_df_property(field, "read_only", 1);
			}
		});

		if (frm.fields_dict.brokerypayable) {
			frm.set_df_property("brokerypayable", "read_only", brokery_paid ? 1 : 0);
		}

		const grid = frm.fields_dict.details && frm.fields_dict.details.grid;
		if (!grid || !grid.update_docfields_property) {
			return;
		}

		const read_only_cols = ["netweight", "total_weight", "mund", "bagamnt", "totalamnt"];
		read_only_cols.forEach((col) => {
			grid.update_docfields_property(col, "read_only", 1);
		});
		grid.update_docfields_property("brokeramnt", "read_only", auto_brokery ? 1 : 0);

		const kanta_editable = {
			inkanta: kanta === "I" || kanta === "T",
			delikanta: kanta === "D" || kanta === "T" || kanta === "W",
		};
		Object.entries(kanta_editable).forEach(([col, editable]) => {
			grid.update_docfields_property(col, "read_only", editable ? 0 : 1);
		});

		grid.update_docfields_property("mund", "hidden", amntby === "B" ? 1 : 0);
		grid.update_docfields_property("bagqty", "read_only", amntby === "B" ? 0 : 1);
	},

	recalc(frm, is_purchase) {
		if (frm.doc.docstatus !== 0 || millitrix.is_form_read_only(frm)) {
			return;
		}
		if (frm._millitrix_recalc_seq == null) {
			frm._millitrix_recalc_seq = 0;
		}
		frm._millitrix_recalc_seq += 1;
		const seq = frm._millitrix_recalc_seq;
		clearTimeout(frm._millitrix_recalc_timer);
		frm._millitrix_recalc_timer = setTimeout(() => {
			frappe.call({
				method: "millitrix.api.invoice_form.recalc",
				args: {
					doc: frm.doc,
					is_purchase: is_purchase ? 1 : 0,
				},
				freeze: false,
				callback(r) {
					if (seq !== frm._millitrix_recalc_seq) {
						return;
					}
					if (!r.message) {
						return;
					}
					frappe.model.sync(r.message);
					frm.refresh_fields();
					millitrix.invoice_form.apply_field_rules(frm);
					if (millitrix.child_table) {
						millitrix.child_table.schedule_render_grid_totals(frm, ["details"]);
					}
				},
				error(r) {
					if (seq !== frm._millitrix_recalc_seq) {
						return;
					}
					frappe.msgprint({
						title: __("Recalculation failed"),
						message: r?.message || __("Could not recalculate invoice totals."),
						indicator: "red",
					});
				},
			});
		}, 250);
	},

	is_yes(value) {
		if (value === 1 || value === true) {
			return true;
		}
		return ["Y", "YES", "1", "TRUE", "SUBMITTED"].includes(String(value || "N").trim().toUpperCase());
	},

	normalize_kanta(value) {
		const key = String(value || "Total Weight").trim().toUpperCase();
		if (key.startsWith("IN")) {
			return "I";
		}
		if (key.startsWith("DEL")) {
			return "D";
		}
		if (key.includes("BAG")) {
			return "B";
		}
		return "T";
	},

	normalize_amntby(value) {
		const key = String(value || "Mund").trim().toUpperCase();
		if (key.startsWith("BAG") || key === "B") {
			return "B";
		}
		if (key.startsWith("TRUCK") || key === "T" || key === "QUANTITY") {
			return "T";
		}
		if (key.startsWith("MUND") || key === "M") {
			return "M";
		}
		return key.slice(0, 1) || "M";
	},
};
