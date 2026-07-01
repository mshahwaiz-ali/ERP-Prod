// Copyright (c) 2026, Millitrix and contributors
// Oracle PNRVoucher.fmb — Purchase / Sales / Broker invoice payment screens.

frappe.provide("millitrix.pnr_invoice");

millitrix.pnr_invoice.DOCTYPES = new Set([
	"Purchase Invoice Payment",
	"Sales Invoice Receipt",
	"Broker Invoice Payment",
]);

millitrix.pnr_invoice.CONFIG = {
	"Purchase Invoice Payment": {
		party_categories: ["12"],
		flow: "payment",
		mode_label: "Payment Mode",
		balance_label: "Payable",
		amount_label: "Paid",
		instruments_label: "Payment Mode",
	},
	"Sales Invoice Receipt": {
		party_categories: ["13"],
		flow: "receipt",
		mode_label: "Receipt Mode",
		balance_label: "Receivable",
		amount_label: "Received",
		instruments_label: "Receipt Mode",
	},
	"Broker Invoice Payment": {
		party_categories: ["11"],
		flow: "payment",
		knockoff_method: "millitrix.api.knockoff.get_broker_documents",
		mode_label: "Payment Mode",
		balance_label: "Payable",
		amount_label: "Paid",
		instruments_label: "Payment Mode",
	},
};

millitrix.pnr_invoice.setup_form = function (frm) {
	const cfg = millitrix.pnr_invoice.CONFIG[frm.doctype];
	if (!cfg) {
		return;
	}

	frm.set_query("partyid", () => ({
		filters: { pcat_id: ["in", cfg.party_categories] },
	}));

	millitrix.pnr_invoice.apply_grid_rules(frm, cfg);

	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}

	if (!frm.is_new()) {
		if (frm.doc.docstatus === 0) {
			const load_opts = {
				child_field: "documents",
				date_field: "pnrdate",
				party_field: "partyid",
				flow: cfg.flow,
				map_row: millitrix.knockoff.PNR_DOCUMENT_MAP,
				button_label: __("Get Documents"),
				after_load(f) {
					millitrix.knockoff.recalc_child_total(f, "documents", "amount");
				},
			};
			if (cfg.knockoff_method) {
				load_opts.method = cfg.knockoff_method;
			}
			millitrix.knockoff.add_load_button(frm, load_opts);
		}

		millitrix.knockoff.add_accounting_button(frm, { flow: cfg.flow });
	}

	millitrix.knockoff.recalc_child_total(frm, "documents", "amount");
};

millitrix.pnr_invoice.apply_document_grid_labels = function (frm, cfg, attempt = 0) {
	const grid = frm.fields_dict.documents?.grid;
	if (!grid?.docfields || !cfg) {
		if (attempt < 25) {
			setTimeout(
				() => millitrix.pnr_invoice.apply_document_grid_labels(frm, cfg, attempt + 1),
				80
			);
		}
		return;
	}
	["party_name", "item_name", "docbalamnt", "balance"].forEach((col) => {
		millitrix.knockoff.set_grid_field(grid, col, { read_only: 1 });
	});
	millitrix.knockoff.set_grid_field(grid, "docbalamnt", { label: __(cfg.balance_label) });
	millitrix.knockoff.set_grid_field(grid, "amount", { label: __(cfg.amount_label) });
	grid.visible_columns = null;
	if (typeof grid.setup_visible_columns === "function") {
		grid.setup_visible_columns();
	}
	grid.refresh();
	if (millitrix.child_table?.refresh_table_hints) {
		millitrix.child_table.refresh_table_hints(frm, ["documents"]);
	}
};

millitrix.pnr_invoice.apply_instrument_grid_labels = function (frm, cfg, attempt = 0) {
	const grid = frm.fields_dict.instruments?.grid;
	if (!grid?.docfields || !cfg) {
		if (attempt < 25) {
			setTimeout(
				() => millitrix.pnr_invoice.apply_instrument_grid_labels(frm, cfg, attempt + 1),
				80
			);
		}
		return;
	}
	if (cfg.mode_label) {
		millitrix.knockoff.set_grid_field(grid, "pnrmode", { label: __(cfg.mode_label) });
	}
	millitrix.knockoff.set_grid_field(grid, "bankaccid", { label: __("Bank Account") });
	grid.refresh();
	if (frm.fields_dict.instruments && cfg.instruments_label) {
		frm.set_df_property("instruments", "label", cfg.instruments_label);
	}
};

millitrix.pnr_invoice.apply_grid_rules = function (frm, cfg) {
	millitrix.pnr_invoice.apply_document_grid_labels(frm, cfg);
	millitrix.pnr_invoice.apply_instrument_grid_labels(frm, cfg);
};

millitrix.pnr_invoice.DOCTYPES.forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			millitrix.pnr_invoice.setup_form(frm);
		},
		documents_add(frm) {
			const cfg = millitrix.pnr_invoice.CONFIG[frm.doctype];
			setTimeout(() => millitrix.pnr_invoice.apply_document_grid_labels(frm, cfg), 80);
		},
		documents_remove(frm) {
			millitrix.knockoff.recalc_child_total(frm, "documents", "amount");
		},
		instruments_add(frm) {
			const cfg = millitrix.pnr_invoice.CONFIG[frm.doctype];
			setTimeout(() => millitrix.pnr_invoice.apply_instrument_grid_labels(frm, cfg), 80);
		},
		instruments_remove(frm) {
			millitrix.knockoff.recalc_child_total(frm, "instruments", "amount");
		},
	});
});

frappe.ui.form.on("Payment and Receipt Document", {
	form_render(frm) {
		if (!millitrix.pnr_invoice.DOCTYPES.has(frm.doctype)) {
			return;
		}
		const cfg = millitrix.pnr_invoice.CONFIG[frm.doctype];
		millitrix.pnr_invoice.apply_document_grid_labels(frm, cfg);
	},
	amount(frm, cdt, cdn) {
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
		if (millitrix.pnr_invoice.DOCTYPES.has(frm.doctype)) {
			millitrix.knockoff.recalc_document_balance(cdt, cdn);
			millitrix.knockoff.recalc_child_total(frm, "documents", "amount");
		}
	},
	suspense(frm, cdt, cdn) {
		if (millitrix.pnr_invoice.DOCTYPES.has(frm.doctype)) {
			millitrix.knockoff.recalc_document_balance(cdt, cdn);
		}
	},
});
