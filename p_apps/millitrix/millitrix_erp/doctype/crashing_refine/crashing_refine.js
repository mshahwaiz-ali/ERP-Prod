// Copyright (c) 2026, Millitrix and contributors
// Crashing / Refine — Oracle CrashRefine.fmb input grid parity.

frappe.provide("millitrix.crashing_refine");

const MUND_FACTORS = { N: 40, O: 37.324, Q: 1 };

millitrix.crashing_refine.mund_factor = (mundtype) => {
	const code = String(mundtype || "N").trim().toUpperCase();
	if (code === "O" || mundtype === 37.324) return MUND_FACTORS.O;
	if (code === "Q" || mundtype === 1) return MUND_FACTORS.Q;
	return MUND_FACTORS.N;
};

millitrix.crashing_refine.calc_line = (row) => {
	const bagqty = flt(row.bagqty);
	const per_bag = flt(row.bagweight);
	const westage = flt(row.bagdust);
	const weight = Math.round(bagqty * per_bag);
	const net_per_bag = Math.max(0, per_bag - westage);
	const ref_weight = Math.round(bagqty * net_per_bag);
	const ref_bags = per_bag > 0 ? Math.round(ref_weight / per_bag) : 0;
	const dip = flt(row.dip);
	let prod_1 = 0;
	let prod_2 = 0;
	if (dip) {
		prod_1 = Math.round(millitrix.crashing_refine.mund_factor(row.mundtype) * dip);
		prod_2 = Math.round(ref_weight - prod_1);
	}
	return { weight, ref_bags, ref_weight, prod_1, prod_2 };
};

millitrix.crashing_refine.set_calc_field = (frm, cdt, cdn, fieldname, value) => {
	frappe.model.set_value(cdt, cdn, fieldname, value);
};

millitrix.crashing_refine.setup_queries = (frm) => {
	frm.set_query("mill_id", () => ({
		filters: { activestatus: ["in", ["Yes", "Y", "1", ""]] },
	}));
	frm.set_query("storeid", "inputs", () => {
		const loc = millitrix.crashing_refine.location_for_api(frm);
		return loc ? { filters: { location_id: loc } } : {};
	});
	frm.set_query("critem", "inputs", (_doc, cdt, cdn) => {
		const row = locals[cdt][cdn];
		return {
			query: "millitrix.api.crash_refine_form.critem_query",
			filters: { storeid: row.storeid || "" },
		};
	});
	frm.set_query("crbagid", "inputs", (_doc, cdt, cdn) => {
		const row = locals[cdt][cdn];
		return {
			query: "millitrix.api.crash_refine_form.crbagid_query",
			filters: {
				storeid: row.storeid || "",
				critem: row.critem || "",
			},
		};
	});
	frm.set_query("proditem", "outputs", () => ({
		query: "millitrix.api.crash_refine_form.proditem_query",
	}));
};

millitrix.crashing_refine.recalc_input_row = (frm, cdt, cdn) => {
	const row = locals[cdt][cdn];
	const calc = millitrix.crashing_refine.calc_line(row);

	millitrix.crashing_refine.set_calc_field(frm, cdt, cdn, "total_weight", calc.weight);
	millitrix.crashing_refine.set_calc_field(frm, cdt, cdn, "ref_bags", calc.ref_bags);
	millitrix.crashing_refine.set_calc_field(frm, cdt, cdn, "ref_weight", calc.ref_weight);
	frappe.model.set_value(cdt, cdn, "prod_1", calc.prod_1);
	frappe.model.set_value(cdt, cdn, "prod_2", calc.prod_2);
	millitrix.crashing_refine.recalc_all_outputs(frm);
};

millitrix.crashing_refine.output_weight_for_index = (frm, idx) => {
	const input = (frm.doc.inputs || [])[0];
	if (!input || !flt(input.dip)) {
		return 0;
	}
	if (idx === 0) {
		return flt(input.prod_1);
	}
	if (idx === 1) {
		return flt(input.prod_2);
	}
	return 0;
};

millitrix.crashing_refine.recalc_output_row = (frm, cdt, cdn) => {
	const rows = frm.doc.outputs || [];
	const idx = rows.findIndex((r) => r.name === cdn);
	const input = (frm.doc.inputs || [])[0];
	const updates = {};
	if (input?.storeid) {
		updates.storeid = input.storeid;
	}
	const weight = millitrix.crashing_refine.output_weight_for_index(frm, idx);
	if (weight) {
		updates.weight = weight;
	}
	Object.keys(updates).forEach((field) => {
		frappe.model.set_value(cdt, cdn, field, updates[field]);
	});
};

millitrix.crashing_refine.recalc_all_outputs = (frm) => {
	(frm.doc.outputs || []).forEach((row) => {
		if (row.name) {
			millitrix.crashing_refine.recalc_output_row(frm, row.doctype, row.name);
		}
	});
};

millitrix.crashing_refine.sync_location = (frm) => {
	if (frm.doc.mill_id && frm.doc.location_id !== frm.doc.mill_id) {
		frm.set_value("location_id", frm.doc.mill_id);
	}
};

millitrix.crashing_refine.location_for_api = (frm) =>
	frm.doc.mill_id || frm.doc.location_id || "";

millitrix.crashing_refine.apply_output_defaults = (frm, cdt, cdn) => {
	const row = locals[cdt][cdn];
	if (!row.proditem) {
		return;
	}
	millitrix.crashing_refine.sync_location(frm);
	frappe.call({
		method: "millitrix.api.crash_refine_form.fetch_output_defaults",
		args: {
			location_id: millitrix.crashing_refine.location_for_api(frm),
			proditem: row.proditem,
			crdate: frm.doc.crdate,
		},
		callback(r) {
			const d = r.message || {};
			if (flt(d.rate)) {
				frappe.model.set_value(cdt, cdn, "rate", d.rate);
			}
			millitrix.crashing_refine.recalc_output_row(frm, cdt, cdn);
		},
	});
};

millitrix.crashing_refine.recalc_all_inputs = (frm) => {
	(frm.doc.inputs || []).forEach((row) => {
		if (row.name) {
			millitrix.crashing_refine.recalc_input_row(frm, row.doctype, row.name);
		}
	});
};

millitrix.crashing_refine.apply_input_defaults = (frm, cdt, cdn, { critem, crbagid } = {}) => {
	const row = locals[cdt][cdn];
	if (!row.storeid) {
		return;
	}
	millitrix.crashing_refine.sync_location(frm);
	frappe.call({
		method: "millitrix.api.crash_refine_form.fetch_input_defaults",
		args: {
			location_id: millitrix.crashing_refine.location_for_api(frm),
			storeid: row.storeid,
			critem: critem !== undefined ? critem : row.critem,
			crbagid: crbagid !== undefined ? crbagid : row.crbagid,
			crdate: frm.doc.crdate,
		},
		callback(r) {
			const d = r.message || {};
			const updates = {};
			if (flt(d.rate)) updates.rate = d.rate;
			if (flt(d.bagrate)) updates.bagrate = d.bagrate;
			if (flt(d.bagweight)) updates.bagweight = d.bagweight;
			if (d.mundtype) updates.mundtype = d.mundtype;
			Object.keys(updates).forEach((field) => {
				frappe.model.set_value(cdt, cdn, field, updates[field]);
			});
			millitrix.crashing_refine.recalc_input_row(frm, cdt, cdn);
		},
	});
};

millitrix.crashing_refine.apply_bagdust_defaults = (frm, cdt, cdn) => {
	const row = locals[cdt][cdn];
	if (!flt(row.bagdust)) {
		frappe.model.set_value(cdt, cdn, "dustitemid", "");
		frappe.model.set_value(cdt, cdn, "dust_rate", 0);
		millitrix.crashing_refine.recalc_input_row(frm, cdt, cdn);
		return;
	}
	millitrix.crashing_refine.sync_location(frm);
	frappe.call({
		method: "millitrix.api.crash_refine_form.fetch_bagdust_defaults",
		args: {
			location_id: millitrix.crashing_refine.location_for_api(frm),
			bagdust: row.bagdust,
			crdate: frm.doc.crdate,
		},
		callback(r) {
			const d = r.message || {};
			if (d.dustitemid) {
				frappe.model.set_value(cdt, cdn, "dustitemid", d.dustitemid);
			}
			if (flt(d.dust_rate)) {
				frappe.model.set_value(cdt, cdn, "dust_rate", d.dust_rate);
			}
			millitrix.crashing_refine.recalc_input_row(frm, cdt, cdn);
		},
	});
};

millitrix.crashing_refine.apply_default_mill = (frm) => {
	if (!frm.is_new() || frm.doc.mill_id) {
		return;
	}
	frappe.call({
		method: "millitrix.api.user_context.get_user_scope",
		callback(r) {
			const loc = r.message?.location_id;
			if (loc && !frm.doc.mill_id) {
				frm.set_value("mill_id", loc);
			}
		},
	});
};

millitrix.crashing_refine.show_dip_hint = (frm) => {
	const input = (frm.doc.inputs || [])[0];
	const needs_dip =
		(frm.doc.outputs || []).length > 0 && input && !flt(input.dip);
	const hint = needs_dip
		? __("Enter Dip on the input row to calculate Prod. 1 / Prod. 2 output weights.")
		: "";
	if (frm.fields_dict.inputs?.grid) {
		frm.fields_dict.inputs.grid.update_docfield_property("dip", "description", hint);
	}
};

frappe.ui.form.on("Crashing Refine", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "Crashing Refine");
		}
		millitrix.crashing_refine.apply_default_mill(frm);
		if (frm.is_new()) {
			let changed = false;
			if (!(frm.doc.inputs || []).length) {
				frm.add_child("inputs");
				changed = true;
			}
			if (!(frm.doc.outputs || []).length) {
				frm.add_child("outputs");
				changed = true;
			}
			if (changed) {
				frm.refresh_fields(["inputs", "outputs"]);
			}
		}
	},

	refresh(frm) {
		millitrix.crashing_refine.sync_location(frm);
		millitrix.crashing_refine.setup_queries(frm);
		millitrix.crashing_refine.recalc_all_inputs(frm);
		millitrix.crashing_refine.recalc_all_outputs(frm);
		millitrix.crashing_refine.show_dip_hint(frm);
	},

	outputs_add(frm) {
		setTimeout(() => {
			millitrix.crashing_refine.recalc_all_outputs(frm);
			millitrix.crashing_refine.show_dip_hint(frm);
		}, 100);
	},

	mill_id(frm) {
		millitrix.crashing_refine.sync_location(frm);
	},
});

frappe.ui.form.on("Crash Refine Input", {
	critem(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "bagweight", 0);
		if (row.storeid) {
			millitrix.crashing_refine.apply_input_defaults(frm, cdt, cdn, {
				critem: row.critem,
			});
		}
	},

	crbagid(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.storeid) {
			millitrix.crashing_refine.apply_input_defaults(frm, cdt, cdn, {
				crbagid: row.crbagid,
			});
		}
	},

	bagqty(frm, cdt, cdn) {
		millitrix.crashing_refine.recalc_input_row(frm, cdt, cdn);
	},

	bagweight(frm, cdt, cdn) {
		millitrix.crashing_refine.recalc_input_row(frm, cdt, cdn);
	},

	bagdust(frm, cdt, cdn) {
		millitrix.crashing_refine.apply_bagdust_defaults(frm, cdt, cdn);
	},

	dip(frm, cdt, cdn) {
		millitrix.crashing_refine.recalc_input_row(frm, cdt, cdn);
		millitrix.crashing_refine.show_dip_hint(frm);
	},

	storeid(frm, cdt, cdn) {
		millitrix.crashing_refine.recalc_all_outputs(frm);
	},
});

frappe.ui.form.on("Crash Refine Output", {
	proditem(frm, cdt, cdn) {
		const parent = frm.doctype === "Crashing Refine" ? frm : cur_frm;
		if (!parent || parent.doctype !== "Crashing Refine") {
			return;
		}
		millitrix.crashing_refine.apply_output_defaults(parent, cdt, cdn);
	},
});
