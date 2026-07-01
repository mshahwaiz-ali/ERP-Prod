// Copyright (c) 2026, Millitrix and contributors
// Purchase Other Bill + Purchase Return Other Bill

frappe.provide("millitrix.other_bill");

millitrix.other_bill.recalc_line = function (cdt, cdn) {
	const row = locals[cdt][cdn];
	const amount = flt(row.quantity) * flt(row.rate);
	if (flt(row.amount) !== amount) {
		frappe.model.set_value(cdt, cdn, "amount", flt(amount, 2));
	}
};

millitrix.other_bill.recalc_parent = function (frm) {
	if (!frm.doc.details?.length) {
		return;
	}
	let total = 0;
	for (const row of frm.doc.details) {
		total += flt(row.amount) || flt(row.quantity) * flt(row.rate);
	}
	const amount = flt(total, 2);
	if (flt(frm.doc.amount) !== amount) {
		frm.set_value("amount", amount);
	}
};

millitrix.other_bill.setup_purchase_bill = function (frm) {
	frm.set_query("partyid", () => ({ filters: { pcat_id: ["in", ["12"]] } }));
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
	millitrix.other_bill.recalc_parent(frm);
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, { document_id_field: "pbillno" });
	}
};

millitrix.other_bill.setup_sales_bill = function (frm) {
	frm.set_query("partyid", () => ({ filters: { pcat_id: ["in", ["13"]] } }));
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
	millitrix.other_bill.recalc_parent(frm);
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, { document_id_field: "sbillno" });
	}
};

millitrix.other_bill.sync_return_line = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row.pbdetlno || !frm.doc.pbillno) {
		return;
	}
	frappe.db.get_doc("Purchase Other Bill", frm.doc.pbillno).then((bill) => {
		const orig = (bill.details || []).find(
			(line) => cint(line.pbdetlno) === cint(row.pbdetlno)
		) || (bill.details || [])[cint(row.pbdetlno) - 1];
		if (!orig) {
			return;
		}
		frappe.model.set_value(cdt, cdn, "item_name", orig.item_name || orig.itemcode || "");
		frappe.model.set_value(cdt, cdn, "rate", flt(orig.rate));
		frappe.model.set_value(cdt, cdn, "storeid", orig.storeid || "");
		millitrix.other_bill.recalc_return_line(cdt, cdn);
	});
};

millitrix.other_bill.recalc_return_line = function (cdt, cdn) {
	const row = locals[cdt][cdn];
	const amount = flt(row.quantity) * flt(row.rate);
	frappe.model.set_value(cdt, cdn, "amount", flt(amount, 2));
};

millitrix.other_bill.sync_sales_return_line = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row.sbdetlno || !frm.doc.sbillno) {
		return;
	}
	frappe.db.get_doc("Sales Other Bill", frm.doc.sbillno).then((bill) => {
		const orig =
			(bill.details || []).find((line) => cint(line.sbdetlno) === cint(row.sbdetlno)) ||
			(bill.details || [])[cint(row.sbdetlno) - 1];
		if (!orig) {
			return;
		}
		frappe.model.set_value(cdt, cdn, "item_name", orig.item_name || orig.itemcode || "");
		frappe.model.set_value(cdt, cdn, "rate", flt(orig.rate));
		frappe.model.set_value(cdt, cdn, "storeid", orig.storeid || "");
		millitrix.other_bill.recalc_return_line(cdt, cdn);
		millitrix.other_bill.recalc_parent(frm);
	});
};

millitrix.other_bill.resolve_party_name = (partyid) => {
	if (!partyid) {
		return Promise.resolve("");
	}
	return frappe.db
		.get_value("Party", partyid, "party_name")
		.then((r) => r.message?.party_name || partyid);
};

millitrix.other_bill.sync_party_from_sales_bill = function (frm) {
	if (!frm.doc.sbillno) {
		return;
	}
	frappe.db
		.get_value("Sales Other Bill", frm.doc.sbillno, "partyid")
		.then((r) => {
			const partyid = r.message?.partyid;
			if (partyid) {
				frm.set_value("partyid", partyid);
			}
		})
		.catch(() => {
			frappe.msgprint(__("Could not load party from sales bill"));
		});
};

millitrix.other_bill.setup_sales_return_bill = function (frm) {
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
	millitrix.other_bill.recalc_parent(frm);
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, { document_id_field: "srbillno" });
	}
};

millitrix.other_bill.setup_return_bill = function (frm) {
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
	millitrix.other_bill.recalc_parent(frm);
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, { document_id_field: "prbillno" });
	}
};

millitrix.other_bill.sync_party_from_bill = function (frm) {
	if (!frm.doc.pbillno) {
		return;
	}
	frappe.db
		.get_value("Purchase Other Bill", frm.doc.pbillno, "partyid")
		.then((r) => {
			const partyid = r.message?.partyid;
			if (partyid) {
				frm.set_value("partyid", partyid);
			}
		})
		.catch(() => {
			frappe.msgprint(__("Could not load party from purchase bill"));
		});
};

frappe.ui.form.on("Purchase Other Bill", {
	refresh(frm) {
		millitrix.other_bill.setup_purchase_bill(frm);
	},
	details_add(frm) {
		millitrix.other_bill.recalc_parent(frm);
	},
	details_remove(frm) {
		millitrix.other_bill.recalc_parent(frm);
	},
});

frappe.ui.form.on("Purchase Other Bill Detail", {
	quantity(frm, cdt, cdn) {
		millitrix.other_bill.recalc_line(cdt, cdn);
		millitrix.other_bill.recalc_parent(frm);
	},
	rate(frm, cdt, cdn) {
		millitrix.other_bill.recalc_line(cdt, cdn);
		millitrix.other_bill.recalc_parent(frm);
	},
});

frappe.ui.form.on("Sales Other Bill", {
	refresh(frm) {
		millitrix.other_bill.setup_sales_bill(frm);
	},
	details_add(frm) {
		millitrix.other_bill.recalc_parent(frm);
	},
	details_remove(frm) {
		millitrix.other_bill.recalc_parent(frm);
	},
});

frappe.ui.form.on("Sales Other Bill Detail", {
	quantity(frm, cdt, cdn) {
		millitrix.other_bill.recalc_line(cdt, cdn);
		millitrix.other_bill.recalc_parent(frm);
	},
	rate(frm, cdt, cdn) {
		millitrix.other_bill.recalc_line(cdt, cdn);
		millitrix.other_bill.recalc_parent(frm);
	},
});

frappe.ui.form.on("Purchase Return Other Bill", {
	refresh(frm) {
		millitrix.other_bill.setup_return_bill(frm);
		frm.set_query("pbillno", () => ({
			filters: { docstatus: 1, location_id: frm.doc.location_id || undefined },
		}));
	},
	pbillno(frm) {
		millitrix.other_bill.sync_party_from_bill(frm);
	},
	details_add(frm) {
		millitrix.other_bill.recalc_parent(frm);
	},
	details_remove(frm) {
		millitrix.other_bill.recalc_parent(frm);
	},
});

frappe.ui.form.on("Sales Return Other Bill", {
	refresh(frm) {
		millitrix.other_bill.setup_sales_return_bill(frm);
		frm.set_query("sbillno", () => ({
			filters: { docstatus: 1, location_id: frm.doc.location_id || undefined },
		}));
	},
	sbillno(frm) {
		millitrix.other_bill.sync_party_from_sales_bill(frm);
	},
	details_add(frm) {
		millitrix.other_bill.recalc_parent(frm);
	},
	details_remove(frm) {
		millitrix.other_bill.recalc_parent(frm);
	},
});

frappe.ui.form.on("Purchase Other Bill Return Detail", {
	pbdetlno(frm, cdt, cdn) {
		millitrix.other_bill.sync_return_line(frm, cdt, cdn);
	},
	quantity(frm, cdt, cdn) {
		millitrix.other_bill.recalc_return_line(cdt, cdn);
		millitrix.other_bill.recalc_parent(frm);
	},
});

frappe.ui.form.on("Sales Other Bill Return Detail", {
	sbdetlno(frm, cdt, cdn) {
		millitrix.other_bill.sync_sales_return_line(frm, cdt, cdn);
	},
	quantity(frm, cdt, cdn) {
		millitrix.other_bill.recalc_return_line(cdt, cdn);
		millitrix.other_bill.recalc_parent(frm);
	},
});
