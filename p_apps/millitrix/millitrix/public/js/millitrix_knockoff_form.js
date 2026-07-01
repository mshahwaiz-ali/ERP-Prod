// Copyright (c) 2026, Millitrix and contributors
// VIEW_KNOCKOFFDOCS — load outstanding invoices into knockoff child tables

frappe.provide("millitrix.knockoff");

millitrix.knockoff = {
	PNR_DOCUMENT_MAP(row) {
		return {
			doctypeid: row.doctypeid,
			documentid: row.documentid,
			party_name: row.party_name || "",
			item_name: row.item_name || "",
			docbalamnt: row.docbalamnt,
			amount: row.docbalamnt,
			suspense: 0,
			balance: 0,
		};
	},

	recalc_document_balance(cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!("balance" in row)) {
			return;
		}
		const balance = flt(row.docbalamnt) - flt(row.amount) - flt(row.suspense);
		frappe.model.set_value(cdt, cdn, "balance", balance);
	},

	recalc_loaded_row_balance(child_dt, cdn) {
		const row = locals[child_dt]?.[cdn];
		if (!row) {
			return;
		}
		if ("suspense" in row) {
			this.recalc_document_balance(child_dt, cdn);
		} else if ("balance" in row) {
			this.recalc_cnb_document_balance(child_dt, cdn);
		}
	},

	CNB_DOCUMENT_MAP(row, partyid) {
		return {
			partyid: partyid || row.partyid,
			party_name: row.party_name || "",
			doctypeid: row.doctypeid,
			documentid: row.documentid,
			docbalamnt: row.docbalamnt,
			amount: row.docbalamnt,
			accid: row.accid,
			balance: 0,
		};
	},

	recalc_cnb_document_balance(cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(
			cdt,
			cdn,
			"balance",
			flt(row.docbalamnt) - flt(row.amount)
		);
	},

	ADJUSTMENT_INVOICE_MAP(row) {
		return {
			doctypeid: row.doctypeid,
			documentid: row.documentid,
			partyid: row.partyid || "",
			party_name: row.party_name || "",
			item_name: row.item_name || "",
			docbalamnt: row.docbalamnt,
			amount: 0,
			suspense: 0,
		};
	},

	ADVANCE_PNR_MAP(row) {
		return {
			pnrno: row.pnrno,
			pnrdate: row.pnrdate,
			pnrmode: row.pnrmode || "",
			accid: row.accid || "",
			referno: row.referno || "",
			docbalamnt: row.docbalamnt,
			amount: 0,
			doctypeid: row.doctypeid || "",
		};
	},

	CNB_DOCUMENT_PARTY_GRID: [
		"partyid",
		"documentid",
		"docbalamnt",
		"amount",
		"balance",
	],
	CNB_DOCUMENT_EMPLOYEE_GRID: ["empno", "amount"],

	set_document_grid_field(grid, fieldname, updates) {
		const apply = (df) => {
			if (df) {
				Object.assign(df, updates);
			}
		};
		apply((grid.docfields || []).find((d) => d.fieldname === fieldname));
		for (const row of grid.grid_rows || []) {
			apply((row.docfields || []).find((d) => d.fieldname === fieldname));
		}
	},

	set_grid_field(grid, fieldname, updates) {
		this.set_document_grid_field(grid, fieldname, updates);
	},

	apply_cnb_document_grid(frm, child_field, show_fields, attempt = 0) {
		const grid = frm.fields_dict[child_field]?.grid;
		if (!grid?.docfields) {
			if (attempt < 20) {
				setTimeout(
					() => this.apply_cnb_document_grid(frm, child_field, show_fields, attempt + 1),
					100
				);
			}
			return;
		}
		const show = new Set(show_fields);
		for (const df of grid.docfields) {
			if (df.fieldtype === "Section Break" || df.fieldtype === "Column Break") {
				continue;
			}
			const visible = show.has(df.fieldname);
			this.set_document_grid_field(grid, df.fieldname, {
				hidden: visible ? 0 : 1,
				in_list_view: visible ? 1 : 0,
			});
		}
		grid.visible_columns = show_fields
			.map((fieldname) => {
				const df = (grid.docfields || []).find((d) => d.fieldname === fieldname);
				return df ? [df, df.columns || 2] : null;
			})
			.filter(Boolean);
		grid.refresh();
		if (millitrix.child_table?.refresh_table_hints) {
			millitrix.child_table.refresh_table_hints(frm, [child_field]);
		}
	},

	/** One visible toolbar group — not Actions dropdown, not separate sections. */
	VISIBLE_BTN_GROUP: "millitrix-actions",

	add_visible_toolbar_button(frm, label, fn) {
		const group_key = this.VISIBLE_BTN_GROUP;
		const $toolbar = frm.page.inner_toolbar;
		let $group = $toolbar.find(
			`.millitrix-visible-btn-group[data-group="${group_key}"]`
		);
		if (!$group.length) {
			$toolbar.removeClass("hide");
			$group = $(
				`<div class="btn-group millitrix-visible-btn-group" data-group="${group_key}" role="group"></div>`
			);
			$toolbar.append($group);
		}
		const enc = encodeURIComponent(label);
		if ($group.find(`button[data-label="${enc}"]`).length) {
			return;
		}
		const $btn = $(
			`<button type="button" class="btn btn-default btn-sm ellipsis" data-label="${enc}">${__(label)}</button>`
		);
		$btn.on("click", () => fn());
		$group.append($btn);
	},

	_add_custom_button(frm, label, fn, group) {
		if (group) {
			frm.add_custom_button(label, fn, group);
		} else {
			this.add_visible_toolbar_button(frm, label, fn);
		}
	},

	add_load_button(frm, opts) {
		if (frm.doc.docstatus !== 0) {
			return;
		}
		if (frm.is_new() && !opts.allow_unsaved) {
			return;
		}
		this._add_custom_button(
			frm,
			opts.button_label || __("Get Documents"),
			() => this.load(frm, opts),
			opts.button_group
		);
	},

	add_accounting_button(frm, opts = {}) {
		if (frm.is_new()) {
			return;
		}
		this._add_custom_button(
			frm,
			__("Accounting"),
			() => this.open_accounting(frm, opts),
			opts.button_group
		);
	},

	open_accounting(frm, opts = {}) {
		const idField = opts.document_id_field || "pnrno";
		const docId =
			frm.doc[idField] ||
			frm.doc.adjid ||
			frm.doc.cnbvno ||
			frm.doc.empvno ||
			frm.doc.name;
		if (frm.doc.docstatus === 1) {
			frappe.set_route("List", "Voucher Transaction", {
				documentid: docId,
				doctypeid: frm.doc.doctypeid,
			});
			return;
		}
		const method =
			opts.method || "millitrix.api.knockoff.get_pnr_accounting_lines";
		frappe.call({
			method,
			args: {
				doctype: frm.doctype,
				name: frm.doc.name,
				flow: opts.flow,
			},
			freeze: true,
			freeze_message: __("Loading accounting..."),
			error: millitrix.api.default_error(__("Could not load accounting lines")),
		}).then((r) => {
			this.show_accounting_dialog(r.message || [], frm, opts);
		});
	},

	show_accounting_dialog(lines, frm, opts = {}) {
		const fmt = (value) => format_currency(flt(value), frappe.defaults.get_default("currency"));
		const body = (lines || [])
			.map(
				(line) => `<tr>
					<td>${frappe.utils.escape_html(String(line.accid || ""))}</td>
					<td>${frappe.utils.escape_html(line.account || "")}</td>
					<td class="text-right">${fmt(line.debit)}</td>
					<td class="text-right">${fmt(line.credit)}</td>
					<td>${frappe.utils.escape_html(line.detail || "")}</td>
				</tr>`
			)
			.join("");
		const idField = opts.document_id_field || "pnrno";
		const titleId =
			frm.doc[idField] ||
			frm.doc.adjid ||
			frm.doc.cnbvno ||
			frm.doc.empvno ||
			frm.doc.sopenid ||
			frm.doc.name;
		const d = new frappe.ui.Dialog({
			title: __("Accounting — {0}", [titleId]),
			size: "large",
			primary_action_label: __("Close"),
			primary_action() {
				d.hide();
			},
		});
		d.$body.html(`
			<table class="table table-bordered table-sm">
				<thead>
					<tr>
						<th>${__("A/c Id")}</th>
						<th>${__("Account")}</th>
						<th class="text-right">${__("Debit")}</th>
						<th class="text-right">${__("Credit")}</th>
						<th>${__("Detail")}</th>
					</tr>
				</thead>
				<tbody>${body || `<tr><td colspan="5">${__("No accounting lines")}</td></tr>`}</tbody>
			</table>
		`);
		d.show();
	},

	add_load_advance_pnr_button(frm, opts) {
		if (frm.doc.docstatus !== 0) {
			return;
		}
		if (frm.is_new() && !opts.allow_unsaved) {
			return;
		}
		this._add_custom_button(
			frm,
			opts.button_label || __("Get Advance"),
			() => this.load_advance_pnr(frm, opts),
			opts.button_group
		);
	},

	ensure_location(frm) {
		if (frm.doc.location_id) {
			return Promise.resolve(frm.doc.location_id);
		}
		return frappe
			.call({
				method: "millitrix.api.user_context.get_user_scope",
				error: millitrix.api.default_error(__("Could not load user location")),
			})
			.then((r) => {
				const loc =
					r.message?.location_id ||
					(r.message?.allowed_locations || [])[0];
				if (!loc) {
					return null;
				}
				return frm.set_value("location_id", loc).then(() => loc);
			});
	},

	load_advance_pnr(frm, opts) {
		this.ensure_location(frm).then((location_id) => {
			if (!location_id) {
				frappe.msgprint(__("No location assigned to your user"));
				return;
			}
			const party_field = opts.party_field || "partyid";
			if (!frm.doc[party_field]) {
				frappe.msgprint(__("Set Party first"));
				return;
			}
			const as_of_date = this.get_as_of_date(frm, opts.date_field);
			frappe.call({
				method: "millitrix.api.knockoff.get_advance_pnr_lines",
				args: {
					partyid: frm.doc[party_field],
					location_id,
					as_of_date,
				},
				freeze: true,
				freeze_message: __("Loading advance PNR..."),
				error: millitrix.api.default_error(__("Could not load advance PNR lines")),
			}).then((r) => {
				if (!r || !r.message) {
					return;
				}
				this.merge_pnr_rows(frm, opts.child_field, r.message, opts.map_row);
				if (opts.after_load) {
					opts.after_load(frm);
				}
			});
		});
	},

	vouchmode_flow(vouchmode) {
		const mode = (vouchmode || "").toUpperCase();
		if (mode.startsWith("R")) {
			return "receipt";
		}
		if (mode.startsWith("P")) {
			return "payment";
		}
		return null;
	},

	prompt_party(frm, child_field) {
		const from_line = (frm.doc[child_field] || []).find((row) => row.partyid);
		if (from_line && from_line.partyid) {
			return Promise.resolve(from_line.partyid);
		}
		return new Promise((resolve) => {
			frappe.prompt(
				[
					{
						fieldname: "partyid",
						label: __("Party"),
						fieldtype: "Link",
						options: "Party",
						reqd: 1,
					},
				],
				(values) => resolve(values.partyid),
				__("Select Party"),
				__("Load")
			);
		});
	},

	get_as_of_date(frm, date_field) {
		if (date_field && frm.doc[date_field]) {
			return frm.doc[date_field];
		}
		return (
			frm.doc.pnrdate ||
			frm.doc.vouchdate ||
			frm.doc.adjdate ||
			frappe.datetime.get_today()
		);
	},

	resolve_flow(frm, opts, partyid) {
		if (opts.flow) {
			return Promise.resolve(opts.flow);
		}
		if (typeof opts.resolve_flow === "function") {
			const flow = opts.resolve_flow(frm);
			if (flow) {
				return Promise.resolve(flow);
			}
		}
		return frappe
			.call({
				method: "millitrix.api.knockoff.resolve_flow",
				args: { partyid },
				error: millitrix.api.default_error(__("Could not resolve payment/receipt flow")),
			})
			.then((r) => r.message);
	},

	load(frm, opts) {
		this.ensure_location(frm).then((location_id) => {
			if (!location_id) {
				frappe.msgprint(__("No location assigned to your user"));
				return;
			}

			const child_field = opts.child_field;
			const date_field = opts.date_field;
			const map_row = opts.map_row;
			const as_of_date = this.get_as_of_date(frm, date_field);

			const run = (partyid, flow) => {
				if (!partyid) {
					frappe.msgprint(__("Party is required"));
					return Promise.resolve();
				}
				return this.resolve_flow(frm, opts, partyid).then((resolved_flow) => {
					const knockoff_flow = flow || resolved_flow;
					if (!knockoff_flow) {
						frappe.msgprint(__("Could not determine payment/receipt flow"));
						return Promise.resolve();
					}
					const args = {
						location_id,
						as_of_date,
					};
					if (opts.method === "millitrix.api.knockoff.get_broker_documents") {
						args.brokerid = partyid;
					} else {
						args.partyid = partyid;
						args.flow = knockoff_flow;
					}
					return frappe.call({
						method: opts.method || "millitrix.api.knockoff.get_documents",
						args,
						freeze: true,
						freeze_message: __("Loading outstanding documents..."),
						error: millitrix.api.default_error(__("Could not load outstanding documents")),
					});
				}).then((r) => {
					if (!r || !r.message) {
						return;
					}
					this.merge_rows(frm, child_field, r.message, map_row, partyid, opts);
					if (opts.after_load) {
						opts.after_load(frm);
					}
				});
			};

			const party_field = opts.party_field || "partyid";
			if (frm.doc[party_field]) {
				run(frm.doc[party_field], opts.flow);
				return;
			}
			if (opts.prompt_party) {
				this.prompt_party(frm, child_field).then((partyid) => run(partyid, opts.flow));
				return;
			}
			frappe.msgprint(__("Set Party first"));
		});
	},

	merge_rows(frm, child_field, rows, map_row, partyid, opts = {}) {
		if (opts.replace) {
			frm.set_value(child_field, []);
		} else if (opts.replace_flow) {
			const receipt_docs = new Set(["Sales Invoice", "Sales Other Bill"]);
			const payment_docs = new Set(["Purchase Invoice", "Purchase Other Bill"]);
			const kept = (frm.doc[child_field] || []).filter((row) => {
				if (opts.replace_flow === "receipt") {
					return !receipt_docs.has(row.doctypeid);
				}
				if (opts.replace_flow === "payment") {
					return !payment_docs.has(row.doctypeid);
				}
				return true;
			});
			if (kept.length !== (frm.doc[child_field] || []).length) {
				frm.set_value(child_field, kept);
			}
		}
		const existing = new Set(
			(frm.doc[child_field] || []).map((row) => `${row.doctypeid}|${row.documentid}`)
		);
		let added = 0;
		(rows || []).forEach((row) => {
			const key = `${row.doctypeid}|${row.documentid}`;
			if (existing.has(key)) {
				return;
			}
			const child = frm.add_child(child_field);
			Object.assign(child, map_row(row, partyid, frm));
			const child_dt = frm.fields_dict[child_field]?.grid?.doctype;
			if (child_dt) {
				this.recalc_loaded_row_balance(child_dt, child.name);
			}
			existing.add(key);
			added += 1;
		});
		frm.refresh_field(child_field);
		if (added) {
			frappe.show_alert({
				message: __("{0} document(s) loaded", [added]),
				indicator: "green",
			});
		} else {
			frappe.show_alert({
				message: __("No new outstanding documents"),
				indicator: "orange",
			});
		}
	},

	merge_pnr_rows(frm, child_field, rows, map_row) {
		const existing = new Set((frm.doc[child_field] || []).map((row) => String(row.pnrno)));
		let added = 0;
		(rows || []).forEach((row) => {
			const key = String(row.pnrno);
			if (existing.has(key)) {
				return;
			}
			const child = frm.add_child(child_field);
			Object.assign(child, map_row(row));
			existing.add(key);
			added += 1;
		});
		frm.refresh_field(child_field);
		if (added) {
			frappe.show_alert({
				message: __("{0} advance PNR(s) loaded", [added]),
				indicator: "green",
			});
		} else {
			frappe.show_alert({
				message: __("No new advance PNR balances"),
				indicator: "orange",
			});
		}
	},

	cap_amount(cdt, cdn, amount_field, balance_field) {
		const row = locals[cdt][cdn];
		if (flt(row[amount_field]) > flt(row[balance_field])) {
			frappe.show_alert({
				message: __("Amount cannot exceed document balance"),
				indicator: "orange",
			});
			frappe.model.set_value(cdt, cdn, amount_field, row[balance_field]);
		}
	},

	recalc_child_total(frm, child_field, target_field) {
		const total = (frm.doc[child_field] || []).reduce(
			(sum, row) => sum + flt(row.amount),
			0
		);
		frm.set_value(target_field, total);
	},

	recalc_adjustment_invoice_suspense(cdt, cdn) {
		const row = locals[cdt][cdn];
		const suspense = flt(row.docbalamnt) - flt(row.amount);
		if (flt(row.suspense) !== suspense) {
			frappe.model.set_value(cdt, cdn, "suspense", suspense);
		}
	},

	setup_advance_adjustment_form(frm, flow) {
		if (millitrix.child_table) {
			millitrix.child_table.setup(frm);
		}
		if (!frm.is_new()) {
			this.add_accounting_button(frm, {
				flow,
				document_id_field: "adjid",
				method: "millitrix.api.knockoff.get_adjustment_accounting_lines",
			});
		}
		if (frm.doc.docstatus !== 0) {
			return;
		}
		this.add_load_advance_pnr_button(frm, {
			child_field: "pnr_lines",
			date_field: "adjdate",
			party_field: "partyid",
			button_label: __("Get Advance"),
			allow_unsaved: true,
			map_row: this.ADVANCE_PNR_MAP,
			after_load(f) {
				millitrix.knockoff.recalc_child_total(f, "pnr_lines", "amount");
			},
		});
		this.add_load_button(frm, {
			child_field: "invoice_lines",
			date_field: "adjdate",
			party_field: "partyid",
			flow,
			button_label: __("Get Invoices"),
			allow_unsaved: true,
			map_row: this.ADJUSTMENT_INVOICE_MAP,
			after_load(f) {
				millitrix.knockoff.recalc_child_total(f, "invoice_lines", "amount");
			},
		});
	},
};

const ADVANCE_ADJUSTMENT_DOCTYPES = new Set([
	"Paid Advance Adjustment",
	"Received Advance Adjustment",
]);

frappe.ui.form.on("Adjustment Invoice", {
	amount(frm, cdt, cdn) {
		if (!ADVANCE_ADJUSTMENT_DOCTYPES.has(frm.doctype)) {
			return;
		}
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
		millitrix.knockoff.recalc_adjustment_invoice_suspense(cdt, cdn);
		millitrix.knockoff.recalc_child_total(frm, "invoice_lines", "amount");
	},
	docbalamnt(frm, cdt, cdn) {
		if (!ADVANCE_ADJUSTMENT_DOCTYPES.has(frm.doctype)) {
			return;
		}
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
		millitrix.knockoff.recalc_adjustment_invoice_suspense(cdt, cdn);
	},
	form_render(frm, cdt, cdn) {
		if (!ADVANCE_ADJUSTMENT_DOCTYPES.has(frm.doctype)) {
			return;
		}
		millitrix.knockoff.recalc_adjustment_invoice_suspense(cdt, cdn);
	},
});

frappe.ui.form.on("Adjustment PNR", {
	amount(frm, cdt, cdn) {
		if (!ADVANCE_ADJUSTMENT_DOCTYPES.has(frm.doctype)) {
			return;
		}
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
		millitrix.knockoff.recalc_child_total(frm, "pnr_lines", "amount");
	},
	docbalamnt(frm, cdt, cdn) {
		if (!ADVANCE_ADJUSTMENT_DOCTYPES.has(frm.doctype)) {
			return;
		}
		millitrix.knockoff.cap_amount(cdt, cdn, "amount", "docbalamnt");
	},
});
