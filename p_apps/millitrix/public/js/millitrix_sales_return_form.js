// Copyright (c) 2026, Millitrix and contributors
// Sales Return — Oracle SalesReturn.fmb

frappe.provide("millitrix.sales_return");

const SR = "Sales Return";
const SR_DETAIL = "Sales Return Detail";

if (millitrix.invoice_form?.register) {
	millitrix.invoice_form.register(SR, SR_DETAIL, false);
}

millitrix.sales_return.copy_line_from_invoice = function (line, idx) {
	return {
		sidetlno: line.sidetlno || idx + 1,
		sonumber: line.sonumber,
		biltyno: line.biltyno,
		truckno: line.truckno,
		truckqty: line.truckqty,
		cartage: line.cartage,
		storeid: line.storeid,
		bagid: line.bagid,
		bagqty: line.bagqty,
		bags_are: line.bags_are,
		bagweight: line.bagweight,
		bagrate: line.bagrate,
		delikanta: line.delikanta,
		lessweight: line.lessweight,
		rate: line.rate,
		labouramnt: line.labouramnt,
		brokeramnt: line.brokeramnt,
		transporter: line.transporter,
		gprefeno: line.gprefeno,
	};
};

millitrix.sales_return.sync_from_invoice = function (frm, force_lines = false) {
	if (!frm.doc.salesinvno) {
		return Promise.resolve();
	}
	return frappe.db
		.get_doc("Sales Invoice", frm.doc.salesinvno)
		.then((si) => {
			const updates = {
				itemcode: si.itemcode || "",
				customerid: si.customerid || "",
				brokerid: si.brokerid || "",
				sub_partyid: si.sub_partyid || "",
				amntby: si.amntby,
				kantatype: si.kantatype || "Total Weight",
				brokery: si.brokery,
				borrow: si.borrow,
			};
			Object.entries(updates).forEach(([field, value]) => {
				if (frm.fields_dict[field] && frm.doc[field] !== value) {
					frm.set_value(field, value);
				}
			});

			if (!force_lines && (frm.doc.details || []).length) {
				millitrix.sales_return.apply_rules(frm);
				millitrix.invoice_form.recalc(frm, false);
				return;
			}

			frm.clear_table("details");
			(si.details || []).forEach((line, idx) => {
				const row = frm.add_child("details");
				Object.assign(row, millitrix.sales_return.copy_line_from_invoice(line, idx));
			});
			frm.refresh_field("details");
			millitrix.sales_return.apply_rules(frm);
			millitrix.invoice_form.recalc(frm, false);
		})
		.catch(() => {
			frappe.msgprint(__("Could not load sales invoice for return"));
		});
};

millitrix.sales_return.apply_rules = function (frm) {
	const grid = frm.fields_dict.details?.grid;
	if (!grid?.update_docfields_property) {
		return;
	}
	[
		"sidetlno",
		"sonumber",
		"total_weight",
		"mund",
		"bagamnt",
		"netweight",
		"totalamnt",
		"brokeramnt",
	].forEach((col) => {
		grid.update_docfields_property(col, "read_only", 1);
	});
	const kanta = millitrix.invoice_form.normalize_kanta(frm.doc.kantatype);
	const amntby = millitrix.invoice_form.normalize_amntby(frm.doc.amntby);
	grid.update_docfields_property("inkanta", "read_only", kanta === "I" || kanta === "T" ? 0 : 1);
	grid.update_docfields_property(
		"delikanta",
		"read_only",
		kanta === "D" || kanta === "T" || kanta === "W" ? 0 : 1
	);
	grid.update_docfields_property("mund", "hidden", amntby === "B" ? 1 : 0);
	["amount", "payable"].forEach((field) => {
		if (frm.fields_dict[field]) {
			frm.set_df_property(field, "read_only", 1);
		}
	});
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
};

frappe.ui.form.on(SR, {
	refresh(frm) {
		millitrix.sales_return.apply_rules(frm);
		frm.set_query("salesinvno", () => ({
			filters: { docstatus: 1, location_id: frm.doc.location_id || undefined },
		}));
		if (!frm.is_new()) {
			millitrix.knockoff.add_accounting_button(frm, { document_id_field: "salesretno" });
		}
	},
	salesinvno(frm) {
		frm._millitrix_sr_sync = millitrix.sales_return.sync_from_invoice(frm, true);
	},
	kantatype(frm) {
		millitrix.sales_return.apply_rules(frm);
		millitrix.invoice_form.recalc(frm, false);
	},
	amntby(frm) {
		millitrix.sales_return.apply_rules(frm);
		millitrix.invoice_form.recalc(frm, false);
	},
	borrow(frm) {
		millitrix.invoice_form.recalc(frm, false);
	},
});
