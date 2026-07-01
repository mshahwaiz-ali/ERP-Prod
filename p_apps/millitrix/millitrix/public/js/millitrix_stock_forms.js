// Copyright (c) 2026, Millitrix and contributors
// Opening vs Closing stock — Oracle: Per_Bag → Closing → Avg Rate → Stock (read-only).

frappe.provide("millitrix.stock_forms");

millitrix.stock_forms.setup_bagitem_query = (frm, child_table) => {
	frm.set_query("bagitemcode", child_table, (_doc, cdt, cdn) => {
		const row = locals[cdt][cdn];
		return {
			query: "millitrix.api.stock.bagitem_query",
			filters: { itemcode: row.itemcode || "" },
		};
	});
};

millitrix.stock_forms.sync_bagitem_for_item = (frm, cdt, cdn) => {
	const row = locals[cdt][cdn];
	if (!row.itemcode) {
		if (row.bagitemcode) {
			frappe.model.set_value(cdt, cdn, "bagitemcode", "");
		}
		return;
	}
	frappe.call({
		method: "millitrix.api.stock.is_bardana_line_item",
		args: { itemcode: row.itemcode },
		error: millitrix.api.default_error(__("Could not check bardana item")),
		callback(r) {
			if (!r.message && row.bagitemcode) {
				frappe.model.set_value(cdt, cdn, "bagitemcode", "");
			}
		},
	});
};

millitrix.stock_forms.set_grid_field = (grid, fieldname, updates) => {
	const apply = (df) => {
		if (df) {
			Object.assign(df, updates);
		}
	};
	apply((grid.docfields || []).find((d) => d.fieldname === fieldname));
	for (const row of grid.grid_rows || []) {
		apply((row.docfields || []).find((d) => d.fieldname === fieldname));
	}
};

millitrix.stock_forms.apply_opening_closing_grid = (frm, mode, attempt = 0) => {
	if (mode !== "closing") {
		return;
	}

	const grid = frm.fields_dict.details?.grid;
	if (!grid?.docfields) {
		if (attempt < 20) {
			setTimeout(() => millitrix.stock_forms.apply_opening_closing_grid(frm, mode, attempt + 1), 100);
		}
		return;
	}

	const opening_fields = [
		"storeid",
		"store_name",
		"itemcode",
		"item_name",
		"bagitemcode",
		"filled_item_name",
		"partyid",
		"party_name",
	];
	const grid_columns = [
		"storeid",
		"store_name",
		"itemcode",
		"item_name",
		"bagitemcode",
		"filled_item_name",
		"partyid",
		"party_name",
		"bags_are",
		"bagweight",
	];
	const row_panel_fields = ["closing_stock", "movingrate", "stock_value"];

	opening_fields.forEach((fieldname) => {
		millitrix.stock_forms.set_grid_field(grid, fieldname, {
			hidden: 0,
			in_list_view: grid_columns.includes(fieldname) ? 1 : 0,
		});
	});

	millitrix.stock_forms.set_grid_field(grid, "bagweight", { label: __("Per Bag") });
	millitrix.stock_forms.set_grid_field(grid, "closing_stock", {
		hidden: 0,
		in_list_view: 0,
		label: __("Closing"),
	});
	millitrix.stock_forms.set_grid_field(grid, "movingrate", {
		hidden: 0,
		in_list_view: 0,
		label: __("Avg Rate"),
	});
	millitrix.stock_forms.set_grid_field(grid, "stock_value", {
		hidden: 0,
		in_list_view: 0,
		label: __("Stock value"),
		read_only: 1,
	});

	row_panel_fields.forEach((fieldname) => {
		millitrix.stock_forms.set_grid_field(grid, fieldname, {
			hidden: 0,
			in_list_view: 0,
		});
	});

	millitrix.stock_forms.set_grid_field(grid, "bags_are", {
		hidden: 0,
		in_list_view: grid_columns.includes("bags_are") ? 1 : 0,
	});

	millitrix.stock_forms.set_grid_field(grid, "opening_stock", {
		hidden: 1,
		in_list_view: 0,
	});

	grid.visible_columns = null;
	if (typeof grid.setup_visible_columns === "function") {
		grid.setup_visible_columns();
	}
	frm.refresh_field("details");
	millitrix.stock_forms.recalc_all_lines(frm, true);

	if (millitrix.child_table?.refresh_table_hints) {
		millitrix.child_table.refresh_table_hints(frm, ["details"]);
	}
};

millitrix.stock_forms.recalc_line_stock = (cdt, cdn, frm) => {
	const row = locals[cdt][cdn];
	const qty =
		frm && frm.doctype === "Opening Stock"
			? flt(row.opening_stock)
			: flt(row.closing_stock);
	frappe.model.set_value(cdt, cdn, "stock_value", qty * flt(row.movingrate));
};

millitrix.stock_forms.recalc_all_lines = (frm, is_closing) => {
	if (!is_closing) {
		return;
	}
	(frm.doc.details || []).forEach((row) => {
		if (row.name) {
			millitrix.stock_forms.recalc_line_stock(row.doctype, row.name, frm);
		}
	});
	millitrix.stock_forms.update_total_stock(frm);
};

millitrix.stock_forms.update_total_stock = (frm) => {
	if (frm.doctype !== "Closing Stock") {
		return;
	}
	const rows = frm.doc.details || [];
	let total = 0;
	rows.forEach((row) => {
		total += flt(row.stock_value) || flt(row.closing_stock) * flt(row.movingrate);
	});
	frm.set_value("total_stock", total);
	const show_total = rows.length > 1;
	frm.toggle_display("total_stock", show_total);
};

millitrix.stock_forms.setup_closing_accounting = (frm) => {
	if (frm.doctype !== "Closing Stock" || frm.is_new()) {
		return;
	}
	millitrix.knockoff.add_visible_toolbar_button(frm, __("Accounting"), () => {
		if (frm.doc.docstatus === 1) {
			frappe.set_route("List", "Voucher Transaction", {
				documentid: frm.doc.sopenid,
				doctypeid: frm.doc.doctypeid || "Closing Stock",
			});
			return;
		}
		frappe.call({
			method: "millitrix.api.stock.get_closing_stock_accounting_lines",
			args: { name: frm.doc.name },
			freeze: true,
			freeze_message: __("Loading accounting..."),
			error: millitrix.api.default_error(__("Could not load accounting lines")),
		}).then((r) => {
			millitrix.knockoff.show_accounting_dialog(r.message || [], frm);
		});
	});
};

frappe.ui.form.on("Opening Stock", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "Opening Stock");
		}
		if (frm.is_new() && !frm.doc.opendate) {
			frm.set_value("opendate", frappe.datetime.get_today());
		}
	},

	refresh(frm) {
		millitrix.stock_forms.setup_bagitem_query(frm, "details");
		if (millitrix.child_table) {
			millitrix.child_table.setup(frm);
		}
		(frm.doc.details || []).forEach((row) => {
			if (row.name) {
				millitrix.stock_forms.recalc_line_stock(row.doctype, row.name, frm);
			}
		});
	},
});

frappe.ui.form.on("Closing Stock", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "Closing Stock");
		}
		if (frm.is_new() && !frm.doc.opendate) {
			frm.set_value("opendate", frappe.datetime.get_today());
		}
	},

	refresh(frm) {
		millitrix.stock_forms.apply_opening_closing_grid(frm, "closing");
		millitrix.stock_forms.setup_bagitem_query(frm, "details");
		millitrix.stock_forms.setup_closing_accounting(frm);
		if (millitrix.child_table) {
			millitrix.child_table.setup(frm);
		}
	},

	details_add(frm) {
		setTimeout(() => millitrix.stock_forms.apply_opening_closing_grid(frm, "closing"), 100);
	},

	details_remove(frm) {
		millitrix.stock_forms.update_total_stock(frm);
	},
});

frappe.ui.form.on("Opening Stock Detail", {
	itemcode(frm, cdt, cdn) {
		millitrix.stock_forms.sync_bagitem_for_item(frm, cdt, cdn);
	},
	opening_stock(frm, cdt, cdn) {
		if (frm.doctype === "Opening Stock") {
			millitrix.stock_forms.recalc_line_stock(cdt, cdn, frm);
		}
	},
	closing_stock(frm, cdt, cdn) {
		if (frm.doctype === "Closing Stock") {
			millitrix.stock_forms.recalc_line_stock(cdt, cdn, frm);
			millitrix.stock_forms.update_total_stock(frm);
		}
	},
	movingrate(frm, cdt, cdn) {
		millitrix.stock_forms.recalc_line_stock(cdt, cdn, frm);
		if (frm.doctype === "Closing Stock") {
			millitrix.stock_forms.update_total_stock(frm);
		}
	},
	form_render(frm, cdt, cdn) {
		millitrix.stock_forms.recalc_line_stock(cdt, cdn, frm);
	},
});

// ——— Stock Adjustment ———

millitrix.stock_forms.fetch_adjustment_balance = (frm, cdt, cdn) => {
	const row = locals[cdt][cdn];
	if (!row.storeid || !row.itemcode) {
		return;
	}
	frappe.call({
		method: "millitrix.api.stock.get_stock_balance",
		args: {
			storeid: row.storeid,
			itemcode: row.itemcode,
			bagitemcode: row.bagitemcode || "",
			partyid: row.partyid || "",
			bags_are: row.bags_are || "",
		},
		error: millitrix.api.default_error(__("Could not load stock balance")),
		callback(r) {
			const bal = r.message || {};
			frappe.model.set_value(cdt, cdn, "current_stock", flt(bal.stock_in_hand));
			if (!flt(row.rate) && flt(bal.movingrate)) {
				frappe.model.set_value(cdt, cdn, "rate", flt(bal.movingrate));
			}
			millitrix.stock_forms.recalc_adjustment_line(cdt, cdn);
		},
	});
};

millitrix.stock_forms.adjustment_mund_cache = {};

millitrix.stock_forms.adjustment_mundtype = (itemcode) => {
	if (!itemcode) {
		return Promise.resolve("N");
	}
	if (millitrix.stock_forms.adjustment_mund_cache[itemcode]) {
		return Promise.resolve(millitrix.stock_forms.adjustment_mund_cache[itemcode]);
	}
	return frappe.db.get_value("Item Setup", itemcode, "mundtype").then((r) => {
		const raw = (r.message && r.message.mundtype) || "N";
		const key = String(raw).toUpperCase();
		const code =
			key === "OLD" || key === "O" ? "O" : key === "Q" || key === "QUANTITY" ? "Q" : "N";
		millitrix.stock_forms.adjustment_mund_cache[itemcode] = code;
		return code;
	}).catch(() => "N");
};

millitrix.stock_forms.adjustment_mund_factor = (mundtype) => {
	if (millitrix.order_form && millitrix.order_form.mund_factor) {
		return millitrix.order_form.mund_factor(mundtype);
	}
	const key = (mundtype || "N").toString().toUpperCase();
	return { N: 40, O: 37.324, Q: 1 }[key] || 40;
};

millitrix.stock_forms.recalc_adjustment_line = (cdt, cdn) => {
	const row = locals[cdt][cdn];
	const adjusted =
		flt(row.current_stock) + flt(row.inc_stock) - flt(row.dec_stock);
	const delta = flt(row.inc_stock) - flt(row.dec_stock);
	return millitrix.stock_forms.adjustment_mundtype(row.itemcode).then(() => {
		const amount = flt(-delta * flt(row.rate), 2);
		frappe.model.set_value(cdt, cdn, "adjusted_stock", flt(adjusted, 2));
		frappe.model.set_value(cdt, cdn, "amount", amount);
	});
};

millitrix.stock_forms.transfer_kanta_weight = (row, kanta) => {
	const bagweight = flt(row.bagweight);
	const bagqty = flt(row.bagqty);
	const truckqty = flt(row.truckqty);
	if (kanta === "T" || kanta === "W") {
		if (bagweight > 0 && bagqty > 0) {
			return bagqty * bagweight;
		}
		if (bagweight > 0 && truckqty > 0) {
			return truckqty * bagweight;
		}
		return flt(row.delikanta);
	}
	if (kanta === "I") {
		return 0;
	}
	if (kanta === "D") {
		return flt(row.delikanta);
	}
	return truckqty;
};

millitrix.stock_forms.transfer_display_total_weight = (row, kanta) => {
	const bagweight = flt(row.bagweight);
	const bagqty = flt(row.bagqty);
	const truckqty = flt(row.truckqty);
	if (bagweight > 0 && bagqty > 0) {
		return bagqty * bagweight;
	}
	if (bagweight > 0 && truckqty > 0) {
		return truckqty * bagweight;
	}
	return millitrix.stock_forms.transfer_kanta_weight(row, kanta);
};

millitrix.stock_forms.setup_adjustment = (frm) => {
	millitrix.stock_forms.setup_bagitem_query(frm, "details");
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
};

const ADJUSTMENT_KEY_FIELDS = [
	"storeid",
	"itemcode",
	"bagitemcode",
	"partyid",
	"bags_are",
];

frappe.ui.form.on("Stock Adjustment", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "Stock Adjustment");
		}
	},
	refresh(frm) {
		millitrix.stock_forms.setup_adjustment(frm);
	},
});

frappe.ui.form.on("Stock Adjustment Detail", {
	itemcode(frm, cdt, cdn) {
		millitrix.stock_forms.sync_bagitem_for_item(frm, cdt, cdn);
	},
	form_render(frm, cdt, cdn) {
		millitrix.stock_forms.fetch_adjustment_balance(frm, cdt, cdn);
	},
	inc_stock(frm, cdt, cdn) {
		millitrix.stock_forms.recalc_adjustment_line(cdt, cdn);
	},
	dec_stock(frm, cdt, cdn) {
		millitrix.stock_forms.recalc_adjustment_line(cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		millitrix.stock_forms.recalc_adjustment_line(cdt, cdn);
	},
});

ADJUSTMENT_KEY_FIELDS.forEach((field) => {
	frappe.ui.form.on("Stock Adjustment Detail", field, (frm, cdt, cdn) => {
		millitrix.stock_forms.fetch_adjustment_balance(frm, cdt, cdn);
	});
});

// ——— Stock Transfer Note ———

millitrix.stock_forms.recalc_transfer_line = (cdt, cdn, frm) => {
	const row = locals[cdt][cdn];
	const kanta = millitrix.invoice_form?.normalize_kanta
		? millitrix.invoice_form.normalize_kanta(frm.doc.kantatype)
		: "D";
	const total_weight = millitrix.stock_forms.transfer_display_total_weight(row, kanta);
	const net = Math.max(
		millitrix.stock_forms.transfer_kanta_weight(row, kanta) - flt(row.lessweight),
		0
	);
	const bag_amnt = flt(row.bagqty) * flt(row.bagrate);
	const totalamnt = net * flt(row.rate) + bag_amnt;
	frappe.model.set_value(cdt, cdn, "total_weight", flt(total_weight, 2));
	frappe.model.set_value(cdt, cdn, "netweight", flt(net, 2));
	frappe.model.set_value(cdt, cdn, "totalamnt", flt(totalamnt, 2));
};

millitrix.stock_forms.apply_transfer_grid = (frm) => {
	const grid = frm.fields_dict.details?.grid;
	if (!grid?.update_docfields_property) {
		return;
	}
	const kanta = millitrix.invoice_form?.normalize_kanta
		? millitrix.invoice_form.normalize_kanta(frm.doc.kantatype)
		: "D";
	grid.update_docfields_property("delikanta", "read_only", kanta === "D" ? 0 : 1);
	grid.update_docfields_property("truckqty", "read_only", kanta === "T" ? 0 : 1);
	["total_weight", "netweight", "totalamnt"].forEach((col) => {
		grid.update_docfields_property(col, "read_only", 1);
	});
};

millitrix.stock_forms.setup_transfer = (frm) => {
	millitrix.stock_forms.apply_transfer_grid(frm);
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, { document_id_field: "transferno" });
	}
};

const TRANSFER_LINE_FIELDS = [
	"truckqty",
	"bagweight",
	"delikanta",
	"bagqty",
	"bagrate",
	"rate",
];

frappe.ui.form.on("Stock Transfer Note", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "Stock Transfer Note");
		}
	},
	refresh(frm) {
		millitrix.stock_forms.setup_transfer(frm);
		(frm.doc.details || []).forEach((row) => {
			if (row.name) {
				millitrix.stock_forms.recalc_transfer_line(row.doctype, row.name, frm);
			}
		});
	},
	kantatype(frm) {
		millitrix.stock_forms.apply_transfer_grid(frm);
		(frm.doc.details || []).forEach((row) => {
			if (row.name) {
				millitrix.stock_forms.recalc_transfer_line(row.doctype, row.name, frm);
			}
		});
	},
	details_add(frm) {
		setTimeout(() => millitrix.stock_forms.apply_transfer_grid(frm), 80);
	},
});

frappe.ui.form.on("Stock Transfer Detail", {
	form_render(frm, cdt, cdn) {
		millitrix.stock_forms.recalc_transfer_line(cdt, cdn, frm);
	},
});

TRANSFER_LINE_FIELDS.forEach((field) => {
	frappe.ui.form.on("Stock Transfer Detail", field, (frm, cdt, cdn) => {
		millitrix.stock_forms.recalc_transfer_line(cdt, cdn, frm);
	});
});
