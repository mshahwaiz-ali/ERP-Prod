// Copyright (c) 2026, Millitrix and contributors
// Accounts Opening — Frappe Link pickers on row panel; Accounting → Acc_Ledger after save.

const COA_POSTING = { chartlevel: 5, transflag: "Yes" };

frappe.ui.form.on("Accounts Opening", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "Accounts Opening");
		}
	},

	refresh(frm) {
		millitrix.gl_opening.setup_queries(frm);
		millitrix.gl_opening.setup_accounting_button(frm);
		millitrix.gl_opening.apply_grid_rules(frm);
		millitrix.gl_opening.update_totals(frm);
	},

	details_add(frm) {
		millitrix.gl_opening.update_totals(frm);
	},

	details_remove(frm) {
		millitrix.gl_opening.update_totals(frm);
	},
});

frappe.ui.form.on("Accounts Opening Detail", {
	debit(frm) {
		millitrix.gl_opening.update_totals(frm);
	},
	credit(frm) {
		millitrix.gl_opening.update_totals(frm);
	},
	itemcode(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.itemcode) {
			return;
		}
		millitrix.gl_opening.fill_row_from_entity(frm, "Item", row.itemcode, cdn);
	},
	partyid(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.partyid) {
			return;
		}
		millitrix.gl_opening.fill_row_from_entity(frm, "Party", row.partyid, cdn);
	},
	empno(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.empno) {
			return;
		}
		millitrix.gl_opening.fill_row_from_entity(frm, "Employee", row.empno, cdn);
	},
});

frappe.provide("millitrix.gl_opening");

millitrix.gl_opening.setup_queries = (frm) => {
	frm.set_query("accid", "details", () => ({ filters: COA_POSTING }));
	frm.set_query("itemcode", "details", () => ({ filters: { stockable: "Yes" } }));
	frm.set_query("empno", "details", () => {
		const filters = {};
		if (frm.doc.location_id) {
			filters.location_id = frm.doc.location_id;
		}
		return { filters };
	});
};

millitrix.gl_opening.setup_accounting_button = (frm) => {
	const details = frm.fields_dict.details;
	if (!details?.$wrapper) {
		return;
	}

	if (!frm._gl_opening_accounting_bar) {
		frm._gl_opening_accounting_bar = $(`
			<div class="gl-opening-accounting-bar" style="margin: 10px 0 0 0;"></div>
		`);
		details.$wrapper.after(frm._gl_opening_accounting_bar);
	}

	const bar = frm._gl_opening_accounting_bar;
	bar.empty();

	if (frm.is_new()) {
		bar.hide();
		return;
	}
	bar.show();

	$(`<button type="button" class="btn btn-sm btn-default">`)
		.text(__("Accounting"))
		.on("click", () => millitrix.gl_opening.open_account_ledger(frm))
		.appendTo(bar);
};

millitrix.gl_opening.fill_row_from_entity = (frm, entry_mode, entity_id, cdn) => {
	frappe.call({
		method: "millitrix.api.accounts_opening.get_detail_lines",
		args: { entry_mode, entity_id },
		freeze: true,
		freeze_message: __("Loading accounts..."),
		error: millitrix.api.default_error(__("Could not load account lines")),
		callback(r) {
			const rows = r.message || [];
			if (!rows.length) {
				frappe.msgprint(__("No accounts found for this selection"));
				return;
			}
			const row = locals["Accounts Opening Detail"][cdn];
			const first = rows[0];
			frappe.model.set_value(row.doctype, row.name, "accid", first.accid);
			frappe.model.set_value(
				row.doctype,
				row.name,
				"account_description",
				first.account_description || ""
			);
			if (entry_mode === "Item") {
				frappe.model.set_value(row.doctype, row.name, "partyid", "");
				frappe.model.set_value(row.doctype, row.name, "empno", "");
			} else if (entry_mode === "Party") {
				frappe.model.set_value(row.doctype, row.name, "itemcode", "");
				frappe.model.set_value(row.doctype, row.name, "empno", "");
			} else if (entry_mode === "Employee") {
				frappe.model.set_value(row.doctype, row.name, "itemcode", "");
				frappe.model.set_value(row.doctype, row.name, "partyid", "");
			}
			if (rows.length > 1) {
				millitrix.gl_opening.merge_detail_rows(frm, rows.slice(1));
			}
			frm.refresh_field("details");
		},
	});
};

millitrix.gl_opening.get_selected_detail_row = (frm) => {
	const grid = frm.fields_dict.details?.grid;
	if (!grid) {
		return null;
	}

	const selected = grid.get_selected_children?.() || [];
	if (selected.length) {
		return selected[0];
	}

	if (grid.grid_rows?.length) {
		const highlighted = grid.grid_rows.find((row) => row.doc.__highlighted);
		if (highlighted) {
			return highlighted.doc;
		}
	}

	const rows = frm.doc.details || [];
	if (rows.length === 1 && rows[0].accid) {
		return rows[0];
	}

	return null;
};

millitrix.gl_opening.open_account_ledger = (frm) => {
	const row = millitrix.gl_opening.get_selected_detail_row(frm);
	if (!row?.accid) {
		frappe.msgprint(__("Select an account line in the Details table first"));
		return;
	}

	const opening_date = frm.doc.opening_date || frappe.datetime.get_today();
	const from_date = frappe.datetime.add_months(opening_date, -12);

	frappe.set_route("query-report", "Acc_Ledger", {
		from_date,
		to_date: opening_date,
		location_id: frm.doc.location_id || "",
		accid: row.accid,
	});
};

millitrix.gl_opening.merge_detail_rows = (frm, rows) => {
	const existing = new Set(
		(frm.doc.details || []).map((row) =>
			[row.accid, row.itemcode || "", row.partyid || "", row.empno || ""].join("|")
		)
	);
	let added = 0;
	(rows || []).forEach((row) => {
		const key = [row.accid, row.itemcode || "", row.partyid || "", row.empno || ""].join("|");
		if (existing.has(key)) {
			return;
		}
		const child = frm.add_child("details");
		Object.assign(child, row);
		existing.add(key);
		added += 1;
	});
	frm.refresh_field("details");
	millitrix.gl_opening.update_totals(frm);
	if (added) {
		frappe.show_alert({
			message: __("{0} account line(s) added", [added]),
			indicator: "green",
		});
	}
};

millitrix.gl_opening.apply_grid_rules = (frm) => {
	const grid = frm.fields_dict.details?.grid;
	if (!grid?.update_docfields_property) {
		return;
	}
	if (frm.doc.docstatus === 0) {
		grid.cannot_add_rows = false;
	}
	["opndetlid", "balance"].forEach((field) => {
		grid.update_docfields_property(field, "hidden", 1);
		grid.update_docfields_property(field, "in_list_view", 0);
	});
	["itemcode", "partyid", "empno", "trans_id"].forEach((field) => {
		grid.update_docfields_property(field, "hidden", 0);
		grid.update_docfields_property(field, "in_list_view", 0);
	});
	grid.update_docfields_property("accid", "in_list_view", 1);
	grid.update_docfields_property("account_description", "in_list_view", 1);
	grid.update_docfields_property("debit", "in_list_view", 1);
	grid.update_docfields_property("credit", "in_list_view", 1);
	frm.refresh_field("details");
};

millitrix.gl_opening.update_totals = (frm) => {
	let total_debit = 0;
	let total_credit = 0;
	(frm.doc.details || []).forEach((row) => {
		total_debit += flt(row.debit);
		total_credit += flt(row.credit);
	});
	frm.set_value("total_debit", total_debit);
	frm.set_value("total_credit", total_credit);
};
