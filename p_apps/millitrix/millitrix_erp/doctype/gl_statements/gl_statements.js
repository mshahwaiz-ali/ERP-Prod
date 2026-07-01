// Copyright (c) 2026, Millitrix and contributors
// Oracle GL_Statements.fmb — header, statement lines (sub), GL codes per selected line.

frappe.ui.form.on("GL Statements", {
	setup(frm) {
		frm.set_query("accid", "gl_accounts", () => ({
			filters: { chartlevel: 5, transflag: "Yes" },
		}));
	},

	onload(frm) {
		frm.selected_sub_statement = null;
	},

	refresh(frm) {
		if (millitrix.child_table) {
			millitrix.child_table.setup(frm);
		}
		if (!frm.is_new() && frm.doc.statementid) {
			frm.set_df_property("statementid", "read_only", 1);
		}
		setup_sub_statement_grid(frm);
		setup_gl_accounts_grid(frm);
		filter_gl_accounts(frm);
	},
});

frappe.ui.form.on("GL Sub Statement", {
	sub_statements_add(frm) {
		setup_sub_statement_grid(frm);
	},
});

frappe.ui.form.on("GL Statement Account", {
	gl_accounts_add(frm) {
		if (frm.selected_sub_statement) {
			const rows = frm.doc.gl_accounts || [];
			const row = rows[rows.length - 1];
			if (row && !row.sub_statement_ref) {
				row.sub_statement_ref = frm.selected_sub_statement;
				frm.refresh_field("gl_accounts");
			}
		}
	},
});

function setup_sub_statement_grid(frm) {
	const grid = frm.fields_dict.sub_statements?.grid;
	if (!grid || grid.__gl_sub_setup) {
		return;
	}
	grid.__gl_sub_setup = true;

	grid.wrapper.on("click", ".grid-row", function () {
		const $row = $(this);
		const idx = cint($row.attr("data-idx"));
		const row = (frm.doc.sub_statements || []).find((r) => r.idx === idx);
		if (row?.name) {
			frm.selected_sub_statement = row.name;
			filter_gl_accounts(frm);
		}
	});

	if (!grid.custom_buttons?.Get) {
		grid.add_custom_button(__("Get"), () => get_gl_accounts_for_selected_line(frm));
	}
}

function setup_gl_accounts_grid(frm) {
	const grid = frm.fields_dict.gl_accounts?.grid;
	if (!grid) {
		return;
	}
	const label = frm.selected_sub_statement
		? __("GL Codes (selected statement line)")
		: __("GL Codes (select a statement line above)");
	grid.wrapper.find(".grid-heading-row .grid-label").text(label);
}

function filter_gl_accounts(frm) {
	const grid = frm.fields_dict.gl_accounts?.grid;
	if (!grid) {
		return;
	}
	const selected = frm.selected_sub_statement;
	grid.grid_rows.forEach((grid_row) => {
		const show = !selected || grid_row.doc.sub_statement_ref === selected;
		grid_row.wrapper.toggle(show);
	});
	setup_gl_accounts_grid(frm);
}

function get_selected_sub_statement_row(frm) {
	const grid = frm.fields_dict.sub_statements?.grid;
	if (!grid) {
		return null;
	}
	const selected = grid.get_selected();
	if (selected?.length === 1) {
		return selected[0];
	}
	if (frm.selected_sub_statement) {
		return (frm.doc.sub_statements || []).find((r) => r.name === frm.selected_sub_statement);
	}
	const rows = frm.doc.sub_statements || [];
	return rows.length ? rows[rows.length - 1] : null;
}

function get_gl_accounts_for_selected_line(frm) {
	const line = get_selected_sub_statement_row(frm);
	if (!line) {
		frappe.msgprint(__("Add or select a statement line first."));
		return;
	}
	if (!line.statement_type) {
		frappe.msgprint(__("Set Type on the statement line before Get."));
		return;
	}

	frappe.call({
		method: "millitrix.millitrix_erp.doctype.gl_statements.gl_statements.get_accounts_by_type",
		args: { statement_type: line.statement_type },
		freeze: true,
		freeze_message: __("Loading GL accounts..."),
		callback(r) {
			const accounts = r.message || [];
			if (!accounts.length) {
				frappe.msgprint(__("No level-5 accounts found for Type {0}.", [line.statement_type]));
				return;
			}

			const existing = new Set(
				(frm.doc.gl_accounts || [])
					.filter((row) => row.sub_statement_ref === line.name && row.accid)
					.map((row) => row.accid)
			);

			let added = 0;
			accounts.forEach((acc) => {
				if (existing.has(acc.name)) {
					return;
				}
				const child = frm.add_child("gl_accounts");
				child.sub_statement_ref = line.name;
				child.accid = acc.name;
				child.account_description = acc.description;
				child.show_side = "Net";
				added += 1;
			});

			frm.selected_sub_statement = line.name;
			frm.refresh_field("gl_accounts");
			filter_gl_accounts(frm);
			frappe.show_alert({
				message: __("Added {0} GL account(s) for {1}.", [added, line.description || line.note || line.name]),
				indicator: "green",
			});
		},
	});
}
