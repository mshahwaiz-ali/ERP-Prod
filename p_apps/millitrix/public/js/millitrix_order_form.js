// Copyright (c) 2026, Millitrix and contributors
// Purchase Order / Sales Order — Oracle PurchOrder.fmb / SalesOrder.fmb

frappe.provide("millitrix.order_form");

millitrix.order_form.CONFIG = {
	"Purchase Order": {
		party_field: "supplierid",
		party_categories: ["12"],
		qty_fields: ["truckqty", "weight", "rate"],
		received_fields: ["truckreceived", "weightreceived"],
	},
	"Sales Order": {
		party_field: "customerid",
		party_categories: ["13"],
		qty_fields: ["truckqty", "weight", "rate"],
		received_fields: ["truckissued", "weightissued"],
	},
};

millitrix.order_form.setup = function (frm) {
	const cfg = millitrix.order_form.CONFIG[frm.doctype];
	if (!cfg) {
		return;
	}

	["amount", "payable", "receivable", "truckqtycancel"].forEach((field) => {
		if (frm.fields_dict[field]) {
			frm.set_df_property(field, "read_only", 1);
		}
	});
	(cfg.received_fields || []).forEach((field) => {
		if (frm.fields_dict[field]) {
			frm.set_df_property(field, "read_only", 1);
		}
	});

	if (frm.fields_dict.brokerid) {
		frm.set_query("brokerid", () => ({ filters: { pcat_id: ["in", ["11"]] } }));
	}
	if (frm.fields_dict[cfg.party_field]) {
		frm.set_query(cfg.party_field, () => ({
			filters: { pcat_id: ["in", cfg.party_categories] },
		}));
	}
	if (frm.fields_dict.sub_partyid) {
		frm.set_query("sub_partyid", () => ({ filters: { pcat_id: ["in", ["11", "12", "13"]] } }));
	}

	millitrix.order_form.recalc(frm);
};

millitrix.order_form.MUND_FACTORS = { N: 40, O: 37.324, Q: 1 };

millitrix.order_form.mund_factor = function (mundtype) {
	const key = (mundtype || "N").toString().toUpperCase();
	return millitrix.order_form.MUND_FACTORS[key] || 40;
};

millitrix.order_form.calc_qty = function (frm) {
	const weight = flt(frm.doc.weight);
	const truckqty = flt(frm.doc.truckqty);
	if (weight > 0) {
		const mundtype = frm._order_mundtype || "N";
		return weight / millitrix.order_form.mund_factor(mundtype);
	}
	return truckqty;
};

millitrix.order_form.recalc = function (frm) {
	const qty = millitrix.order_form.calc_qty(frm);
	const rate = flt(frm.doc.rate);
	const amount = flt(qty * rate, 2);
	if (flt(frm.doc.amount) !== amount) {
		frm.set_value("amount", amount);
	}
};

millitrix.order_form.load_item_mundtype = function (frm) {
	if (!frm.doc.itemcode) {
		frm._order_mundtype = "N";
		millitrix.order_form.recalc(frm);
		return;
	}
	frappe.db.get_value("Item Setup", frm.doc.itemcode, "mundtype").then((r) => {
		const raw = (r.message && r.message.mundtype) || "N";
		const key = raw.toString().trim().toUpperCase();
		frm._order_mundtype = key === "OLD" || key === "O" ? "O" : key === "Q" || key === "QUANTITY" ? "Q" : "N";
		millitrix.order_form.recalc(frm);
	});
};

Object.keys(millitrix.order_form.CONFIG).forEach((doctype) => {
	const cfg = millitrix.order_form.CONFIG[doctype];
	const handlers = {
		refresh(frm) {
			millitrix.order_form.setup(frm);
			millitrix.order_form.load_item_mundtype(frm);
		},
		itemcode(frm) {
			millitrix.order_form.load_item_mundtype(frm);
		},
	};
	cfg.qty_fields.forEach((field) => {
		handlers[field] = (frm) => millitrix.order_form.recalc(frm);
	});
	frappe.ui.form.on(doctype, handlers);
});
