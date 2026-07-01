// Copyright (c) 2026, Millitrix and contributors
// Payable / Receivable Discount Note — Oracle PNRDiscount.fmb

frappe.provide("millitrix.discount_note");

millitrix.discount_note.DOCTYPES = {
	"Payable Discount Note": {
		flow: "payment",
		party_categories: ["12"],
		balance_label: "Payable",
	},
	"Receivable Discount Note": {
		flow: "receipt",
		party_categories: ["13"],
		balance_label: "Receivable",
	},
};

millitrix.discount_note.DOCUMENT_GRID = [
	"documentid",
	"party_name",
	"item_name",
	"docbalamnt",
	"amount",
	"balance",
];

millitrix.discount_note.DISCOUNT_DOCUMENT_MAP = function (row) {
	const mapped = millitrix.knockoff.PNR_DOCUMENT_MAP(row);
	mapped.amount = 0;
	mapped.balance = flt(row.docbalamnt);
	return mapped;
};

millitrix.discount_note.apply_document_grid = function (frm, attempt = 0) {
	const grid = frm.fields_dict.documents?.grid;
	if (!grid?.docfields) {
		if (attempt < 20) {
			setTimeout(() => this.apply_document_grid(frm, attempt + 1), 100);
		}
		return;
	}
	const cfg = this.DOCTYPES[frm.doctype];
	const show = new Set(this.DOCUMENT_GRID);
	for (const df of grid.docfields) {
		if (frappe.model.layout_fields.includes(df.fieldtype)) {
			continue;
		}
		const visible = show.has(df.fieldname);
		millitrix.knockoff.set_grid_field(grid, df.fieldname, {
			hidden: visible ? 0 : 1,
			in_list_view: visible ? 1 : 0,
		});
	}
	if (cfg) {
		millitrix.knockoff.set_grid_field(grid, "party_name", { label: __("Party") });
		millitrix.knockoff.set_grid_field(grid, "docbalamnt", {
			label: __(cfg.balance_label),
		});
		millitrix.knockoff.set_grid_field(grid, "amount", { label: __("Discount") });
	}
	grid.visible_columns = null;
	if (typeof grid.setup_visible_columns === "function") {
		grid.setup_visible_columns();
	}
	grid.refresh();
	if (millitrix.child_table?.refresh_table_hints) {
		millitrix.child_table.refresh_table_hints(frm, ["documents"]);
	}
};

millitrix.discount_note.update_total = function (frm) {
	if (!this.DOCTYPES[frm.doctype]) {
		return;
	}
	const total = (frm.doc.documents || []).reduce((sum, row) => sum + flt(row.amount), 0);
	if (frm.doc.docstatus === 0) {
		frm.set_value("amount", total);
	}
};

millitrix.discount_note.setup = function (frm) {
	const cfg = this.DOCTYPES[frm.doctype];
	if (!cfg) {
		return;
	}
	if (!frm.doc.doctypeid) {
		frm.set_value("doctypeid", frm.doctype);
	}
	frm.set_query("partyid", () => ({
		filters: { pcat_id: ["in", cfg.party_categories] },
	}));
	if (frm.fields_dict.party_name) {
		frm.set_df_property("party_name", "label", "");
	}
	this.apply_document_grid(frm);
	this.update_total(frm);
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, {
			document_id_field: "pnrno",
			method: "millitrix.api.knockoff.get_discount_accounting_lines",
			flow: cfg.flow,
		});
	}
	if (!frm.is_new() && frm.doc.docstatus === 0) {
		millitrix.knockoff.add_load_button(frm, {
			child_field: "documents",
			date_field: "pnrdate",
			party_field: "partyid",
			flow: cfg.flow,
			map_row: millitrix.discount_note.DISCOUNT_DOCUMENT_MAP,
			after_load(f) {
				millitrix.discount_note.update_total(f);
			},
		});
	}
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
};

Object.keys(millitrix.discount_note.DOCTYPES).forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			millitrix.discount_note.setup(frm);
		},

		documents_add(frm) {
			setTimeout(() => millitrix.discount_note.setup(frm), 100);
		},

		documents_remove(frm) {
			millitrix.discount_note.update_total(frm);
		},
	});
});

frappe.ui.form.on("Payment and Receipt Document", {
	amount(frm, cdt, cdn) {
		if (!millitrix.discount_note.DOCTYPES[frm.doctype]) {
			return;
		}
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
		millitrix.knockoff.recalc_document_balance(cdt, cdn);
		millitrix.discount_note.update_total(frm);
	},
	suspense(frm, cdt, cdn) {
		if (!millitrix.discount_note.DOCTYPES[frm.doctype]) {
			return;
		}
		millitrix.knockoff.recalc_document_balance(cdt, cdn);
	},
	form_render(frm, cdt, cdn) {
		if (!millitrix.discount_note.DOCTYPES[frm.doctype]) {
			return;
		}
		millitrix.knockoff.recalc_document_balance(cdt, cdn);
	},
});
