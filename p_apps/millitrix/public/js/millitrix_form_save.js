// Copyright (c) 2026, Millitrix and contributors
// before_save: strip blank child rows + await server recalc where configured.

frappe.provide("millitrix.form_save");

millitrix.form_save._before_save_registered = millitrix.form_save._before_save_registered || new Set();

millitrix.form_save.register_before_save = (doctype, handler) => {
	if (millitrix.form_save._before_save_registered.has(doctype)) {
		return;
	}
	millitrix.form_save._before_save_registered.add(doctype);
	frappe.ui.form.on(doctype, {
		async before_save(frm) {
			if (frm.doc.docstatus !== 0) {
				return;
			}
			if (millitrix.child_table?.strip_blank_rows_for_form) {
				millitrix.child_table.strip_blank_rows_for_form(frm);
			}
			await handler(frm);
		},
	});
};

millitrix.form_save.recalc_invoice = (frm, is_purchase) =>
	new Promise((resolve, reject) => {
		if (frm.doc.docstatus !== 0 || millitrix.is_form_read_only(frm)) {
			resolve();
			return;
		}
		frappe.call({
			method: "millitrix.api.invoice_form.recalc",
			args: {
				doc: frm.doc,
				is_purchase: is_purchase ? 1 : 0,
			},
			callback(r) {
				if (r.message) {
					frappe.model.sync(r.message);
					frm.refresh_fields();
					if (millitrix.invoice_form?.apply_field_rules) {
						millitrix.invoice_form.apply_field_rules(frm);
					}
				}
				resolve();
			},
			error(r) {
				frappe.msgprint({
					title: __("Recalculation failed"),
					message: r?.message || __("Could not recalculate invoice totals before save."),
					indicator: "red",
				});
				frappe.validated = false;
				reject(r);
			},
		});
	});

millitrix.form_save.recalc_crashing_refine = (frm) =>
	new Promise((resolve, reject) => {
		if (frm.doc.docstatus !== 0 || millitrix.is_form_read_only(frm)) {
			resolve();
			return;
		}
		// Sync client-side calcs first (instant).
		if (millitrix.crashing_refine?.recalc_all_inputs) {
			millitrix.crashing_refine.recalc_all_inputs(frm);
		}
		if (millitrix.crashing_refine?.recalc_all_outputs) {
			millitrix.crashing_refine.recalc_all_outputs(frm);
		}
		frappe.call({
			method: "millitrix.api.crash_refine_form.recalc",
			args: { doc: frm.doc },
			callback(r) {
				if (r.message) {
					frappe.model.sync(r.message);
					frm.refresh_fields();
				}
				resolve();
			},
			error(r) {
				frappe.msgprint({
					title: __("Recalculation failed"),
					message: r?.message || __("Could not recalculate crashing/refine before save."),
					indicator: "red",
				});
				frappe.validated = false;
				reject(r);
			},
		});
	});

millitrix.form_save.recalc_gate_pass = (frm) =>
	new Promise((resolve) => {
		if (frm.doc.docstatus !== 0 || millitrix.is_form_read_only(frm)) {
			resolve();
			return;
		}
		if (millitrix.gate_pass_form?.recalc_all) {
			millitrix.gate_pass_form.recalc_all(frm);
		}
		resolve();
	});

// Register standard before_save handlers.
millitrix.form_save.register_before_save("Sales Invoice", (frm) =>
	millitrix.form_save.recalc_invoice(frm, false)
);
millitrix.form_save.register_before_save("Purchase Invoice", (frm) =>
	millitrix.form_save.recalc_invoice(frm, true)
);
millitrix.form_save.register_before_save("Sales Return", async (frm) => {
	if (frm._millitrix_sr_sync) {
		await frm._millitrix_sr_sync;
		frm._millitrix_sr_sync = null;
	}
	await millitrix.form_save.recalc_invoice(frm, false);
});
millitrix.form_save.register_before_save("Purchase Return", async (frm) => {
	if (frm._millitrix_pr_sync) {
		await frm._millitrix_pr_sync;
		frm._millitrix_pr_sync = null;
	}
	await millitrix.form_save.recalc_invoice(frm, true);
});
millitrix.form_save.register_before_save("Crashing Refine", (frm) =>
	millitrix.form_save.recalc_crashing_refine(frm)
);
millitrix.form_save.register_before_save("In Out Gate Pass", (frm) =>
	millitrix.form_save.recalc_gate_pass(frm)
);

millitrix.form_save.recalc_other_bill = (frm) =>
	new Promise((resolve) => {
		if (millitrix.other_bill?.recalc_parent) {
			(frm.doc.details || []).forEach((row) => {
				if (row.name && row.doctype) {
					millitrix.other_bill.recalc_line(row.doctype, row.name);
				}
			});
			millitrix.other_bill.recalc_parent(frm);
		}
		resolve();
	});

millitrix.form_save.register_before_save("Stock Transfer Note", (frm) =>
	new Promise((resolve) => {
		if (millitrix.stock_forms?.recalc_transfer_line) {
			(frm.doc.details || []).forEach((row) => {
				if (row.name) {
					millitrix.stock_forms.recalc_transfer_line(row.doctype, row.name, frm);
				}
			});
		}
		resolve();
	})
);

["Purchase Other Bill", "Sales Other Bill"].forEach((doctype) => {
	millitrix.form_save.register_before_save(doctype, (frm) =>
		millitrix.form_save.recalc_other_bill(frm)
	);
});

millitrix.form_save.recalc_stock_adjustment = (frm) =>
	new Promise((resolve, reject) => {
		const rows = frm.doc.details || [];
		const waits = rows
			.filter((row) => row.name && row.doctype && millitrix.stock_forms?.recalc_adjustment_line)
			.map((row) => millitrix.stock_forms.recalc_adjustment_line(row.doctype, row.name));
		if (!waits.length) {
			resolve();
			return;
		}
		Promise.all(waits).then(() => resolve()).catch((err) => {
			frappe.validated = false;
			reject(err);
		});
	});

millitrix.form_save.register_before_save("Stock Adjustment", (frm) =>
	millitrix.form_save.recalc_stock_adjustment(frm)
);

["Purchase Return Other Bill", "Sales Return Other Bill"].forEach((doctype) => {
	millitrix.form_save.register_before_save(doctype, (frm) =>
		millitrix.form_save.recalc_other_bill(frm)
	);
});

["Opening Stock", "Closing Stock"].forEach((doctype) => {
	millitrix.form_save.register_before_save(doctype, (frm) =>
		new Promise((resolve) => {
			if (millitrix.stock_forms?.update_total_stock) {
				millitrix.stock_forms.update_total_stock(frm);
			}
			resolve();
		})
	);
});

["Purchase Order", "Sales Order"].forEach((doctype) => {
	millitrix.form_save.register_before_save(doctype, (frm) =>
		new Promise((resolve) => {
			if (millitrix.order_form?.recalc) {
				millitrix.order_form.recalc(frm);
			}
			resolve();
		})
	);
});

["Paid Advance Adjustment", "Received Advance Adjustment", "Advance Adjustment"].forEach(
	(doctype) => {
		millitrix.form_save.register_before_save(doctype, (frm) =>
			new Promise((resolve) => {
				if (millitrix.knockoff?.recalc_child_total) {
					millitrix.knockoff.recalc_child_total(frm, "pnr_lines", "amount");
					millitrix.knockoff.recalc_child_total(frm, "invoice_lines", "amount");
				}
				resolve();
			})
		);
	}
);

millitrix.form_save.register_before_save("Payment and Receipt Voucher", (frm) =>
	new Promise((resolve) => {
		if (millitrix.knockoff?.recalc_child_total) {
			millitrix.knockoff.recalc_child_total(frm, "documents", "amount");
		}
		resolve();
	})
);
