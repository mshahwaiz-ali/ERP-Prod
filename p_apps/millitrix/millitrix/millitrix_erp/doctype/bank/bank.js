// Copyright (c) 2026, Millitrix and contributors

const COA_POSTING = { chartlevel: 5, transflag: "Yes" };

frappe.provide("millitrix.bank");

if (!document.getElementById("millitrix-bank-branch-style")) {
	const style = document.createElement("style");
	style.id = "millitrix-bank-branch-style";
	style.textContent = ".millitrix-branch-dim { opacity: 0.4; }";
	document.head.appendChild(style);
}

millitrix.bank.bind_branch_selection = function (frm) {
	const grid = frm.fields_dict.branches?.grid;
	if (!grid?.$wrapper) {
		return;
	}
	if (!frm._selected_branch_id && frm.doc.branches?.length === 1) {
		frm._selected_branch_id = frm.doc.branches[0].branchid;
	}
	grid.wrapper
		.off("click.millitrix-branch")
		.on("click.millitrix-branch", ".grid-row", function () {
			const idx = cint($(this).attr("data-idx"));
			if (!idx) {
				return;
			}
			const branch = (frm.doc.branches || [])[idx - 1];
			frm._selected_branch_id = branch?.branchid || null;
			if (frm._selected_branch_id) {
				frappe.show_alert({
					message: __("Selected branch {0} — new accounts will use this Branch Id", [
						frm._selected_branch_id,
					]),
					indicator: "blue",
				});
			}
			millitrix.bank.highlight_accounts_for_branch(frm);
		});
	millitrix.bank.highlight_accounts_for_branch(frm);
};

millitrix.bank.highlight_accounts_for_branch = function (frm) {
	const branch_id = frm._selected_branch_id;
	const grid = frm.fields_dict.accounts?.grid;
	if (!grid?.grid_rows) {
		return;
	}
	grid.grid_rows.forEach((grid_row) => {
		const match = !branch_id || cint(grid_row.doc.branchid) === cint(branch_id);
		grid_row.row.toggleClass("millitrix-branch-match", Boolean(match && branch_id));
		grid_row.row.toggleClass("millitrix-branch-dim", Boolean(branch_id && !match));
	});
};

frappe.ui.form.on("Bank", {
	refresh(frm) {
		frm.set_query("accid", "accounts", () => ({ filters: COA_POSTING }));
		millitrix.bank.bind_branch_selection(frm);
	},
	accounts_add(frm, cdt, cdn) {
		if (frm._selected_branch_id) {
			frappe.model.set_value(cdt, cdn, "branchid", frm._selected_branch_id);
		}
	},
	branches_add(frm) {
		if ((frm.doc.branches || []).length === 1) {
			frm._selected_branch_id = frm.doc.branches[0].branchid;
		}
	},
});

frappe.ui.form.on("Bank Account", {
	accid(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "acc_description", "");
		const row = locals[cdt][cdn];
		if (!row.accid) {
			return;
		}
		frappe.db.get_value("Chart of Accounting", row.accid, "description").then((r) => {
			frappe.model.set_value(cdt, cdn, "acc_description", r.message?.description || "");
		});
	},
	location_id(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "location_description", "");
		const row = locals[cdt][cdn];
		if (!row.location_id) {
			return;
		}
		frappe.db.get_value("Location", row.location_id, "description").then((r) => {
			frappe.model.set_value(cdt, cdn, "location_description", r.message?.description || "");
		});
	},
});
