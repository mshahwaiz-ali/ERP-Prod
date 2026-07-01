// Copyright (c) 2026, Millitrix and contributors
// Purchase Return — Oracle PurchReturn.fmb

frappe.provide("millitrix.purchase_return");

const PR = "Purchase Return";
const PR_DETAIL = "Purchase Return Detail";

if (millitrix.invoice_form?.register) {
	millitrix.invoice_form.register(PR, PR_DETAIL, true);
}

millitrix.purchase_return.map_kanta_for_return = function (kantatype) {
	return kantatype || "Delivery Kanta";
};

millitrix.purchase_return.copy_line_from_invoice = function (line, idx) {
	return {
		pidetlno: line.pidetlno || idx + 1,
		ponumber: line.ponumber,
		biltyno: line.biltyno,
		truckno: line.truckno,
		truckqty: line.truckqty,
		cartage: line.cartage,
		storeid: line.storeid,
		emptybags: line.emptybags,
		bagid: line.bagid,
		bagqty: line.bagqty,
		bags_are: line.bags_are,
		bagweight: line.bagweight,
		bagrate: line.bagrate,
		inkanta: line.inkanta,
		delikanta: line.delikanta,
		lessweight: line.lessweight,
		rate: line.rate,
		labouramnt: line.labouramnt,
		brokeramnt: line.brokeramnt,
		transporter: line.transporter,
		gprefeno: line.gprefeno,
	};
};

millitrix.purchase_return.sync_from_invoice = function (frm, force_lines = false) {
	if (!frm.doc.purchinvno) {
		return Promise.resolve();
	}
	return frappe.db
		.get_doc("Purchase Invoice", frm.doc.purchinvno)
		.then((pi) => {
			const kantatype = millitrix.purchase_return.map_kanta_for_return(pi.kantatype);
			const updates = {
				itemcode: pi.itemcode || "",
				supplierid: pi.supplierid || "",
				brokerid: pi.brokerid || "",
				sub_partyid: pi.sub_partyid || "",
				amntby: pi.amntby,
				kantatype,
				brokery: pi.brokery,
				borrow: pi.borrow,
				mundtype: pi.mundtype,
			};
			Object.entries(updates).forEach(([field, value]) => {
				if (frm.fields_dict[field] && frm.doc[field] !== value) {
					frm.set_value(field, value);
				}
			});

			if (!force_lines && (frm.doc.details || []).length) {
				millitrix.purchase_return.apply_rules(frm);
				millitrix.invoice_form.recalc(frm, true);
				return;
			}

			frm.clear_table("details");
			(pi.details || []).forEach((line, idx) => {
				const row = frm.add_child("details");
				Object.assign(row, millitrix.purchase_return.copy_line_from_invoice(line, idx));
			});
			frm.refresh_field("details");
			millitrix.purchase_return.apply_rules(frm);
			millitrix.invoice_form.recalc(frm, true);
		})
		.catch(() => {
			frappe.msgprint(__("Could not load purchase invoice for return"));
		});
};

millitrix.purchase_return.apply_rules = function (frm) {
	const grid = frm.fields_dict.details?.grid;
	if (!grid?.update_docfields_property) {
		return;
	}
	["pidetlno", "ponumber", "total_weight", "mund", "bagamnt", "netweight", "totalamnt"].forEach(
		(col) => {
			grid.update_docfields_property(col, "read_only", 1);
		}
	);
	const kanta = millitrix.invoice_form.normalize_kanta(frm.doc.kantatype);
	const amntby = millitrix.invoice_form.normalize_amntby(frm.doc.amntby);
	const inkanta_editable = kanta === "I" || kanta === "T";
	const delikanta_editable = kanta === "D" || kanta === "T";
	grid.update_docfields_property("inkanta", "read_only", inkanta_editable ? 0 : 1);
	grid.update_docfields_property("delikanta", "read_only", delikanta_editable ? 0 : 1);
	grid.update_docfields_property("mund", "hidden", amntby === "B" ? 1 : 0);
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
};

frappe.ui.form.on(PR, {
	refresh(frm) {
		millitrix.purchase_return.apply_rules(frm);
		frm.set_query("purchinvno", () => ({
			filters: { docstatus: 1, location_id: frm.doc.location_id || undefined },
		}));
		if (!frm.is_new()) {
			millitrix.knockoff.add_accounting_button(frm, { document_id_field: "purchretno" });
		}
	},
	purchinvno(frm) {
		frm._millitrix_pr_sync = millitrix.purchase_return.sync_from_invoice(frm, true);
	},
	kantatype(frm) {
		millitrix.purchase_return.apply_rules(frm);
		millitrix.invoice_form.recalc(frm, true);
	},
	amntby(frm) {
		millitrix.purchase_return.apply_rules(frm);
		millitrix.invoice_form.recalc(frm, true);
	},
});
