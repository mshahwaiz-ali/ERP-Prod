// Oracle GL/ChartOfAccount.fmb — tabbed Level (1,2) / (3,4) / (5) builder.
// Copyright (c) 2026, Millitrix and contributors

frappe.provide("millitrix.coa_setup");

const NATURE_OPTIONS = "Assets\nLiabilities\nCapital\nRevenue\nExpenses";
const TRANS_OPTIONS = "No\nYes";

frappe.pages["chart-of-accounting-setup"].on_page_load = function (wrapper) {
	new millitrix.coa_setup.Page(wrapper);
};

millitrix.coa_setup.Page = class {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Chart Of Accounting"),
			single_column: false,
		});
		this.state = { l1: null, l3: null, l4: null };
		this.make_layout();
		this.switch_tab("12");
	}

	make_layout() {
		this.root = $(`
			<div class="mill-coa-setup">
				<ul class="nav nav-tabs coa-tabs">
					<li class="nav-item"><a class="nav-link" data-tab="12">${__("Level (1, 2)")}</a></li>
					<li class="nav-item"><a class="nav-link" data-tab="34">${__("Level (3, 4)")}</a></li>
					<li class="nav-item"><a class="nav-link" data-tab="5">${__("Level (5)")}</a></li>
				</ul>
				<div class="coa-tab-panel" data-panel="12"></div>
				<div class="coa-tab-panel hide" data-panel="34"></div>
				<div class="coa-tab-panel hide" data-panel="5"></div>
			</div>
		`).appendTo(this.page.main);

		this.inject_styles();
		this.root.find(".coa-tabs .nav-link").on("click", (e) => {
			e.preventDefault();
			this.switch_tab($(e.currentTarget).data("tab"));
		});

		this.page.add_menu_item(__("Account List"), () => frappe.set_route("List", "Chart of Accounting"));
		this.make_tab_12();
		this.make_tab_34();
		this.make_tab_5();
	}

	inject_styles() {
		if ($("#mill-coa-setup-style").length) {
			return;
		}
		$("head").append(`
			<style id="mill-coa-setup-style">
				.mill-coa-setup { max-width: 960px; margin: 0 auto; }
				.mill-coa-setup .coa-tabs { margin-bottom: 12px; }
				.mill-coa-setup .coa-section {
					border: 1px solid var(--border-color);
					padding: 12px;
					margin-bottom: 12px;
					background: var(--card-bg);
				}
				.mill-coa-setup .coa-section-title { font-weight: 600; margin-bottom: 8px; }
				.mill-coa-setup .coa-field-row {
					display: grid;
					grid-template-columns: 140px 1fr;
					gap: 8px 12px;
					align-items: center;
				}
				.mill-coa-setup table.coa-grid { width: 100%; margin-top: 8px; }
				.mill-coa-setup table.coa-grid th,
				.mill-coa-setup table.coa-grid td { padding: 6px 8px; vertical-align: middle; }
				.mill-coa-setup table.coa-grid tbody tr { cursor: pointer; }
				.mill-coa-setup table.coa-grid tbody tr.selected { background: var(--highlight-color); }
				.mill-coa-setup .coa-actions { margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; }
			</style>
		`);
	}

	switch_tab(tab) {
		this.root.find(".coa-tabs .nav-link").removeClass("active");
		this.root.find(`.coa-tabs .nav-link[data-tab="${tab}"]`).addClass("active");
		this.root.find(".coa-tab-panel").addClass("hide");
		this.root.find(`.coa-tab-panel[data-panel="${tab}"]`).removeClass("hide");
		if (tab === "34") {
			this.refresh_l3();
		}
		if (tab === "5") {
			this.refresh_l5();
		}
	}

	make_tab_12() {
		const panel = this.root.find('[data-panel="12"]');
		panel.html(`
			<div class="coa-section">
				<div class="coa-section-title">${__("Level (1)")}</div>
				<div class="coa-header-grid l1-fields"></div>
				<div class="coa-actions">
					<button type="button" class="btn btn-primary btn-sm btn-save-l1">${__("Save")}</button>
					<button type="button" class="btn btn-default btn-sm btn-new-l1">${__("New Level (1)")}</button>
				</div>
			</div>
			<div class="coa-section">
				<div class="coa-section-title">${__("Level (2)")}</div>
				<table class="table table-bordered coa-grid l2-grid">
					<thead><tr><th>${__("Level (2)")}</th><th>${__("Description")}</th><th></th></tr></thead>
					<tbody></tbody>
				</table>
				<div class="coa-actions">
					<button type="button" class="btn btn-default btn-sm btn-add-l2">${__("Add Level (2)")}</button>
				</div>
			</div>
		`);

		this.l1_fields = {};
		const mount = panel.find(".l1-fields");
		[
			["l1_link", __("Level (1)"), "Link", "Chart of Accounting"],
			["nature", __("Type"), "Select", NATURE_OPTIONS],
			["description", __("Description"), "Data"],
		].forEach(([fieldname, label, fieldtype, options]) => {
			const row = $(`<div class="coa-field-row" data-field="${fieldname}"></div>`).appendTo(mount);
			row.append(`<label>${label}</label>`);
			const cell = $('<div class="coa-field-cell"></div>').appendTo(row);
			this.l1_fields[fieldname] = frappe.ui.form.make_control({
				df: {
					fieldname,
					label,
					fieldtype,
					options: options || undefined,
					change: () => {
						if (fieldname === "l1_link") {
							this.load_l1(this.l1_fields.l1_link.get_value());
						}
					},
				},
				parent: cell,
				render_input: true,
			});
		});
		frappe.after_ajax(() => {
			this.l1_fields.l1_link.set_query(() => ({ filters: { chartlevel: 1 } }));
		});

		panel.find(".btn-save-l1").on("click", () => this.save_l1());
		panel.find(".btn-new-l1").on("click", () => this.new_l1());
		panel.find(".btn-add-l2").on("click", () => this.add_child_row(2));
	}

	make_tab_34() {
		const panel = this.root.find('[data-panel="34"]');
		panel.html(`
			<div class="coa-section">
				<div class="coa-section-title">${__("Level (3)")}</div>
				<table class="table table-bordered coa-grid l3-grid">
					<thead><tr><th>${__("Level (3)")}</th><th>${__("Description")}</th><th></th></tr></thead>
					<tbody></tbody>
				</table>
				<div class="coa-actions">
					<button type="button" class="btn btn-default btn-sm btn-add-l3">${__("Add Level (3)")}</button>
				</div>
			</div>
			<div class="coa-section">
				<div class="coa-section-title">${__("Level (4)")}</div>
				<table class="table table-bordered coa-grid l4-grid">
					<thead><tr><th>${__("Level (4)")}</th><th>${__("Description")}</th><th></th></tr></thead>
					<tbody></tbody>
				</table>
				<div class="coa-actions">
					<button type="button" class="btn btn-default btn-sm btn-add-l4">${__("Add Level (4)")}</button>
				</div>
			</div>
		`);
		panel.find(".btn-add-l3").on("click", () => this.add_level3());
		panel.find(".btn-add-l4").on("click", () => this.add_child_row(4));
		panel.find(".l3-grid tbody").on("click", "tr", (e) => {
			const name = $(e.currentTarget).data("name");
			if (!name) {
				return;
			}
			this.state.l3 = name;
			panel.find(".l3-grid tbody tr").removeClass("selected");
			$(e.currentTarget).addClass("selected");
			this.refresh_l4();
		});
	}

	make_tab_5() {
		const panel = this.root.find('[data-panel="5"]');
		panel.html(`
			<div class="coa-section">
				<div class="coa-section-title">${__("Level (5)")}</div>
				<div class="coa-header-grid l5-filter"></div>
				<table class="table table-bordered coa-grid l5-grid">
					<thead><tr><th>${__("Level (5)")}</th><th>${__("Description")}</th><th>${__("Transaction")}</th><th></th></tr></thead>
					<tbody></tbody>
				</table>
				<div class="coa-actions">
					<button type="button" class="btn btn-default btn-sm btn-add-l5">${__("Add Level (5)")}</button>
				</div>
			</div>
		`);
		const mount = panel.find(".l5-filter");
		const row = $(`<div class="coa-field-row" data-field="l4_filter"></div>`).appendTo(mount);
		row.append(`<label>${__("Parent Level (4)")}</label>`);
		const cell = $('<div class="coa-field-cell"></div>').appendTo(row);
		this.l4_filter = frappe.ui.form.make_control({
			df: {
				fieldname: "l4_filter",
				label: __("Parent Level (4)"),
				fieldtype: "Link",
				options: "Chart of Accounting",
				change: () => {
					this.state.l4 = this.l4_filter.get_value();
					this.refresh_l5();
				},
			},
			parent: cell,
			render_input: true,
		});
		frappe.after_ajax(() => {
			this.l4_filter.set_query(() => ({ filters: { chartlevel: 4 } }));
		});
		panel.find(".btn-add-l5").on("click", () => this.add_child_row(5));
	}

	call_save(payload) {
		return frappe.call({
			method: "millitrix.api.coa_setup.save_account",
			args: { data: payload },
			freeze: true,
		});
	}

	call_delete(name) {
		return frappe.call({
			method: "millitrix.api.coa_setup.delete_account",
			args: { name },
			freeze: true,
		});
	}

	load_l1(name) {
		if (!name) {
			this.state.l1 = null;
			this.l1_fields.nature.set_value("");
			this.l1_fields.description.set_value("");
			this.render_grid(this.root.find(".l2-grid tbody"), []);
			return;
		}
		frappe.call({
			method: "millitrix.api.coa_setup.get_account",
			args: { name },
			callback: (r) => {
				const doc = r.message;
				this.state.l1 = doc.name;
				this.l1_fields.nature.set_value(doc.nature);
				this.l1_fields.description.set_value(doc.description);
				this.refresh_l2();
			},
		});
	}

	save_l1() {
		const description = (this.l1_fields.description.get_value() || "").trim();
		const nature = this.l1_fields.nature.get_value();
		if (!description || !nature) {
			frappe.msgprint(__("Type and Description are required for Level (1)."));
			return;
		}
		const payload = {
			name: this.state.l1 || undefined,
			chartlevel: 1,
			description,
			nature,
			transflag: "No",
		};
		this.call_save(payload).then((r) => {
			const doc = r.message;
			this.state.l1 = doc.name;
			this.l1_fields.l1_link.set_value(doc.name);
			frappe.show_alert({ message: __("Saved"), indicator: "green" });
			this.refresh_l2();
		});
	}

	new_l1() {
		this.state.l1 = null;
		this.l1_fields.l1_link.set_value("");
		this.l1_fields.nature.set_value("Assets");
		this.l1_fields.description.set_value("");
		this.render_grid(this.root.find(".l2-grid tbody"), []);
	}

	refresh_l2() {
		if (!this.state.l1) {
			this.render_grid(this.root.find(".l2-grid tbody"), []);
			return;
		}
		frappe.call({
			method: "millitrix.api.coa_setup.get_accounts",
			args: { chartlevel: 2, parentid: this.state.l1 },
			callback: (r) => this.render_grid(this.root.find(".l2-grid tbody"), r.message || [], 2),
		});
	}

	refresh_l3() {
		frappe.call({
			method: "millitrix.api.coa_setup.get_accounts",
			args: { chartlevel: 3 },
			callback: (r) => {
				const rows = r.message || [];
				this.render_grid(this.root.find(".l3-grid tbody"), rows, 3, { selectable: true });
				if (this.state.l3 && rows.some((row) => row.name === this.state.l3)) {
					this.root.find(`.l3-grid tbody tr[data-name="${this.state.l3}"]`).addClass("selected");
					this.refresh_l4();
				} else {
					this.state.l3 = null;
					this.render_grid(this.root.find(".l4-grid tbody"), [], 4);
				}
			},
		});
	}

	refresh_l4() {
		if (!this.state.l3) {
			this.render_grid(this.root.find(".l4-grid tbody"), [], 4);
			return;
		}
		frappe.call({
			method: "millitrix.api.coa_setup.get_accounts",
			args: { chartlevel: 4, parentid: this.state.l3 },
			callback: (r) => this.render_grid(this.root.find(".l4-grid tbody"), r.message || [], 4),
		});
	}

	refresh_l5() {
		const parentid = this.state.l4 || this.l4_filter?.get_value?.() || null;
		frappe.call({
			method: "millitrix.api.coa_setup.get_accounts",
			args: { chartlevel: 5, parentid: parentid || undefined },
			callback: (r) => this.render_grid(this.root.find(".l5-grid tbody"), r.message || [], 5),
		});
	}

	render_grid($tbody, rows, level, opts = {}) {
		$tbody.empty();
		rows.forEach((row) => {
			const tr = $(`<tr data-name="${frappe.utils.escape_html(row.name)}"></tr>`);
			if (opts.selectable && row.name === this.state.l3) {
				tr.addClass("selected");
			}
			tr.append(`<td>${row.accid}</td>`);
			const desc = $(`<td><input class="form-control input-sm" data-field="description" value="${frappe.utils.escape_html(row.description || "")}"></td>`);
			tr.append(desc);
			if (level === 5) {
				const sel = $(`<td><select class="form-control input-sm" data-field="transflag"></select></td>`);
				TRANS_OPTIONS.split("\n").forEach((opt) => {
					sel.find("select").append(`<option value="${opt}" ${row.transflag === opt ? "selected" : ""}>${opt}</option>`);
				});
				tr.append(sel);
			}
			const actions = $('<td class="text-right"></td>');
			actions.append(`<button type="button" class="btn btn-xs btn-default btn-save-row">${__("Save")}</button> `);
			actions.append(`<button type="button" class="btn btn-xs btn-danger btn-del-row">${__("Delete")}</button>`);
			tr.append(actions);
			tr.find(".btn-save-row").on("click", (e) => {
				e.stopPropagation();
				const payload = {
					name: row.name,
					description: tr.find('[data-field="description"]').val(),
				};
				if (level === 5) {
					payload.transflag = tr.find('[data-field="transflag"]').val();
				}
				this.call_save(payload).then(() => frappe.show_alert({ message: __("Saved"), indicator: "green" }));
			});
			tr.find(".btn-del-row").on("click", (e) => {
				e.stopPropagation();
				frappe.confirm(__("Delete this account?"), () => {
					this.call_delete(row.name).then(() => {
						if (level === 2) this.refresh_l2();
						if (level === 3) this.refresh_l3();
						if (level === 4) this.refresh_l4();
						if (level === 5) this.refresh_l5();
					});
				});
			});
			$tbody.append(tr);
		});
	}

	prompt_description(title, callback) {
		frappe.prompt(
			[{ fieldname: "description", label: __("Description"), fieldtype: "Data", reqd: 1 }],
			(values) => callback((values.description || "").trim()),
			title,
			__("Save")
		);
	}

	add_child_row(level) {
		let parentid = null;
		let nature = null;
		if (level === 2) {
			if (!this.state.l1) {
				frappe.msgprint(__("Select or save a Level (1) account first."));
				return;
			}
			parentid = this.state.l1;
			nature = this.l1_fields.nature.get_value();
		} else if (level === 4) {
			if (!this.state.l3) {
				frappe.msgprint(__("Select a Level (3) account first."));
				return;
			}
			parentid = this.state.l3;
		} else if (level === 5) {
			parentid = this.state.l4 || this.l4_filter?.get_value?.();
			if (!parentid) {
				frappe.msgprint(__("Select a Level (4) parent account first."));
				return;
			}
			nature = "Assets";
		}
		this.prompt_description(__("Add Level ({0})", [level]), (description) => {
			if (!description) {
				return;
			}
			const payload = {
				chartlevel: level,
				parentid,
				description,
				transflag: level === 5 ? "Yes" : "No",
			};
			if (nature) {
				payload.nature = nature;
			}
			this.resolve_nature(parentid, level).then((resolvedNature) => {
				if (resolvedNature) {
					payload.nature = resolvedNature;
				}
				if (!payload.nature) {
					payload.nature = "Assets";
				}
				this.call_save(payload).then(() => {
					frappe.show_alert({ message: __("Added"), indicator: "green" });
					if (level === 2) this.refresh_l2();
					if (level === 4) this.refresh_l4();
					if (level === 5) this.refresh_l5();
				});
			});
		});
	}

	add_level3() {
		frappe.prompt(
			[
				{
					fieldname: "parentid",
					label: __("Parent Level (2)"),
					fieldtype: "Link",
					options: "Chart of Accounting",
					reqd: 1,
					get_query: () => ({ filters: { chartlevel: 2 } }),
				},
				{ fieldname: "description", label: __("Description"), fieldtype: "Data", reqd: 1 },
			],
			(values) => {
				const description = (values.description || "").trim();
				if (!description || !values.parentid) {
					return;
				}
				this.resolve_nature(values.parentid, 3).then((nature) => {
					this.call_save({
						chartlevel: 3,
						parentid: values.parentid,
						description,
						nature: nature || "Assets",
						transflag: "No",
					}).then(() => {
						frappe.show_alert({ message: __("Added"), indicator: "green" });
						this.refresh_l3();
					});
				});
			},
			__("Add Level (3)"),
			__("Save")
		);
	}

	async resolve_nature(parentid, level) {
		if (!parentid) {
			return "Assets";
		}
		const row = await frappe.db.get_value("Chart of Accounting", parentid, ["nature", "parentid"]);
		if (row?.nature) {
			return row.nature;
		}
		if (level > 2 && row?.parentid) {
			return this.resolve_nature(row.parentid, level - 1);
		}
		return "Assets";
	}
};
