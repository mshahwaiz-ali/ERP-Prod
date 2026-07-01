// Copyright (c) 2026, Millitrix and contributors
// In Out Gate Pass — Oracle GatePass.fmb parity.

frappe.provide("millitrix.gate_pass_form");

millitrix.gate_pass_form = {
	LINE_FIELDS: [
		"truckqty",
		"bagqty",
		"bagweight",
		"inkanta",
		"delikanta",
		"lessweight",
	],

	is_in_type(frm) {
		return String(frm.doc.gptype || "").toUpperCase().startsWith("I");
	},

	normalize_kanta(frm) {
		return millitrix.invoice_form?.normalize_kanta
			? millitrix.invoice_form.normalize_kanta(frm.doc.kantatype)
			: "T";
	},

	default_bags_are(frm) {
		return millitrix.gate_pass_form.is_in_type(frm) ? "Our" : "Party";
	},

	setup_queries(frm) {
		frm.set_query("itemcode", () => {
			const storeid = (frm.doc.details || [])[0]?.storeid;
			return {
				query: "millitrix.api.gate_pass_form.itemcode_query",
				filters: {
					storeid: storeid || "",
					location_id: frm.doc.location_id || "",
				},
			};
		});
		frm.set_query("brokerid", () => ({
			filters: { pcat_id: ["in", ["11"]] },
		}));
		frm.set_query("partyid", () => {
			const cats = millitrix.gate_pass_form.is_in_type(frm) ? ["12"] : ["13"];
			return { filters: { pcat_id: ["in", cats] } };
		});
		frm.set_query("storeid", "details", () => {
			const loc = frm.doc.location_id;
			return loc ? { filters: { location_id: loc } } : {};
		});
		frm.set_query("bagid", "details", (_doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			return {
				query: "millitrix.api.gate_pass_form.bagid_query",
				filters: {
					storeid: row.storeid || "",
					itemcode: frm.doc.itemcode || "",
					emptybags: row.emptybags || "No",
				},
			};
		});
	},

	apply_field_rules(frm) {
		const kanta = millitrix.gate_pass_form.normalize_kanta(frm);
		const bag_fields = ["bagid", "bagqty", "bagweight", "emptybags", "bags_are"];
		const enable_bags = kanta !== "D";
		bag_fields.forEach((field) => {
			frm.fields_dict.details?.grid?.update_docfield_property(
				field,
				"read_only",
				enable_bags ? 0 : 1
			);
		});
		const is_in = millitrix.gate_pass_form.is_in_type(frm);
		const inkanta_editable = is_in && (kanta === "I" || kanta === "T");
		const delikanta_editable = kanta === "D" || kanta === "T";
		frm.fields_dict.details?.grid?.update_docfield_property(
			"inkanta",
			"read_only",
			inkanta_editable ? 0 : 1
		);
		frm.fields_dict.details?.grid?.update_docfield_property(
			"delikanta",
			"read_only",
			delikanta_editable ? 0 : 1
		);
		frm.refresh_field("details");
	},

	display_total_weight(row, frm) {
		const kanta = millitrix.gate_pass_form.normalize_kanta(frm);
		const is_in = millitrix.gate_pass_form.is_in_type(frm);
		if (flt(row.bagweight) > 0 && flt(row.bagqty) > 0) {
			return flt(row.bagqty) * flt(row.bagweight);
		}
		if (flt(row.bagweight) > 0 && flt(row.truckqty) > 0) {
			return flt(row.truckqty) * flt(row.bagweight);
		}
		if (kanta === "Q") {
			return flt(row.truckqty);
		}
		if (kanta === "I" && is_in) {
			return flt(row.inkanta);
		}
		if (kanta === "T" && is_in) {
			return flt(row.inkanta) + flt(row.delikanta);
		}
		if (kanta === "D" || kanta === "T") {
			return flt(row.delikanta);
		}
		return flt(row.truckqty);
	},

	recalc_all(frm) {
		(frm.doc.details || []).forEach((row) => {
			if (row.name) {
				millitrix.gate_pass_form.recalc_line(frm, row.doctype, row.name);
			}
		});
	},

	recalc_line(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const total_weight = millitrix.gate_pass_form.display_total_weight(row, frm);
		frappe.model.set_value(cdt, cdn, "total_weight", flt(total_weight, 2));
		let net = total_weight - flt(row.lessweight);
		if (net < 0) {
			net = 0;
		}
		frappe.model.set_value(cdt, cdn, "netweight", flt(net, 2));
	},

	apply_item_defaults(frm) {
		if (!frm.doc.itemcode || frm.doc.docstatus !== 0) {
			return;
		}
		frappe.call({
			method: "millitrix.api.gate_pass_form.fetch_item_defaults",
			args: {
				itemcode: frm.doc.itemcode,
				location_id: frm.doc.location_id,
				gpdate: frm.doc.gpdate,
			},
			callback(r) {
				const d = r.message || {};
				if (d.mundtype) {
					frm.set_value("mundtype", d.mundtype);
				}
				(frm.doc.details || []).forEach((row) => {
					if (row.name && flt(d.rate)) {
						frappe.model.set_value(row.doctype, row.name, "rate", d.rate);
					}
				});
			},
		});
	},

	apply_bag_defaults(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.storeid || !row.bagid) {
			return;
		}
		frappe.call({
			method: "millitrix.api.gate_pass_form.fetch_bag_defaults",
			args: {
				storeid: row.storeid,
				bagid: row.bagid,
				location_id: frm.doc.location_id,
				emptybags: row.emptybags,
				itemcode: frm.doc.itemcode,
				gpdate: frm.doc.gpdate,
			},
			callback(r) {
				const d = r.message || {};
				const updates = {};
				if (flt(d.bagweight)) updates.bagweight = d.bagweight;
				if (flt(d.bagrate)) updates.bagrate = d.bagrate;
				Object.keys(updates).forEach((field) => {
					frappe.model.set_value(cdt, cdn, field, updates[field]);
				});
				millitrix.gate_pass_form.recalc_line(frm, cdt, cdn);
			},
		});
	},

	apply_default_bags_are(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.bags_are) {
			frappe.model.set_value(cdt, cdn, "bags_are", millitrix.gate_pass_form.default_bags_are(frm));
		}
	},
};

millitrix.gate_pass_form.LINE_FIELDS.forEach((field) => {
	frappe.ui.form.on("Gate Pass Detail", field, (frm, cdt, cdn) => {
		millitrix.gate_pass_form.recalc_line(frm, cdt, cdn);
	});
});

frappe.ui.form.on("Gate Pass Detail", {
	storeid(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "bagid", "");
	},
	emptybags(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "bagid", "");
	},
	bagid(frm, cdt, cdn) {
		millitrix.gate_pass_form.apply_bag_defaults(frm, cdt, cdn);
	},
});

frappe.ui.form.on("In Out Gate Pass", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "In Out Gate Pass");
		}
	},

	refresh(frm) {
		millitrix.gate_pass_form.setup_queries(frm);
		millitrix.gate_pass_form.apply_field_rules(frm);
		millitrix.gate_pass_form.recalc_all(frm);
		if (millitrix.child_table) {
			millitrix.child_table.setup(frm);
		}
	},

	gptype(frm) {
		millitrix.gate_pass_form.apply_field_rules(frm);
		millitrix.gate_pass_form.recalc_all(frm);
	},

	gatepassno(frm) {
		const gpno = String(frm.doc.gatepassno || "").trim();
		if (!gpno) {
			return;
		}
		const first = gpno[0].toUpperCase();
		if (first === "I" && frm.doc.gptype !== "In") {
			frm.set_value("gptype", "In");
		} else if (first === "O" && frm.doc.gptype !== "Out") {
			frm.set_value("gptype", "Out");
		}
	},

	kantatype(frm) {
		millitrix.gate_pass_form.apply_field_rules(frm);
		millitrix.gate_pass_form.recalc_all(frm);
	},

	itemcode(frm) {
		millitrix.gate_pass_form.apply_item_defaults(frm);
	},

	details_add(frm, cdt, cdn) {
		millitrix.gate_pass_form.apply_default_bags_are(frm, cdt, cdn);
		millitrix.gate_pass_form.recalc_line(frm, cdt, cdn);
	},

	details_remove(frm) {
		millitrix.gate_pass_form.recalc_all(frm);
	},
});
