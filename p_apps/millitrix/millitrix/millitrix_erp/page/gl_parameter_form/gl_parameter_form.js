frappe.provide("millitrix");

const GL_PARA_PAGE = "gl-parameter-form";

frappe.pages[GL_PARA_PAGE].on_page_load = function (wrapper) {
	millitrix.gl_parameter_form.boot(wrapper);
};

frappe.pages[GL_PARA_PAGE].on_page_show = function (wrapper) {
	const inst = wrapper._gl_para_form;
	if (!inst || !inst.root?.length || !$.contains(document, inst.root[0])) {
		wrapper._gl_para_form = null;
		millitrix.gl_parameter_form.boot(wrapper);
		return;
	}
	inst.reload_defaults().then(() => inst.apply_defaults());
};

millitrix.gl_parameter_form = {
	boot(wrapper) {
		if (wrapper._gl_para_form) {
			return;
		}
		wrapper._gl_para_form = new millitrix.GLParameterForm(wrapper);
	},
};

millitrix.GLParameterForm = class {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.fields = {};
		this.report_legacy_map = {};
		this.legacy_label_map = {};
		this.section_nodes = {};
		this.session_location_id = null;
		this.defaults = {};
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("GL Parameter Form"),
			single_column: false,
		});
		this.bind_actions();
		this.init();
	}

	async init() {
		await this.reload_defaults();
		if (!this.root) {
			this.make_layout();
			this.apply_defaults();
		} else {
			this.apply_defaults();
		}
	}

	async reload_defaults() {
		try {
			this.defaults = await frappe.xcall("millitrix.api.gl_parameter_form.get_defaults");
		} catch (e) {
			this.defaults = { reports: [] };
			frappe.msgprint(__("Could not load GL Parameter defaults."));
		}
		this.session_location_id = this.defaults?.location_id || null;
		this.build_report_maps(this.defaults?.reports || []);
		if (this.fields.selected_report) {
			this.update_report_select();
		}
	}

	build_report_maps(reports) {
		this.report_legacy_map = Object.fromEntries(
			(reports || []).map((r) => [r.label, r.legacy])
		);
		this.legacy_label_map = Object.fromEntries(
			(reports || []).map((r) => [r.legacy, r.label])
		);
	}

	report_select_options() {
		const labels = Object.keys(this.report_legacy_map);
		return ["", ...labels].join("\n");
	}

	make_layout() {
		this.root = $('<div class="std-form-layout"></div>').appendTo(this.page.main);

		this.add_section(__("Report Format"), (col) => {
			this.add_field(col, {
				fieldname: "selected_report",
				label: __("Report Format"),
				fieldtype: "Select",
				reqd: 1,
				options: this.report_select_options(),
			});
		});

		this.add_section(__("Parameters Selection"), (col) => {
			this.add_field(col, {
				fieldname: "filter_mode",
				label: __("Filter By"),
				fieldtype: "Select",
				options: "Date\nVoucher No",
				default: "Date",
			});
		});

		this.section_nodes.date = this.add_section(__("Date"), (col) => {
			this.add_field(col, {
				fieldname: "from_date",
				label: __("From Date"),
				fieldtype: "Date",
				default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			});
			this.add_field(col, {
				fieldname: "to_date",
				label: __("To Date"),
				fieldtype: "Date",
				default: frappe.datetime.get_today(),
			});
		});

		this.section_nodes.voucher = this.add_section(__("Voucher No"), (col) => {
			this.add_field(col, {
				fieldname: "from_voucherno",
				label: __("From Voucher No"),
				fieldtype: "Link",
				options: "Voucher Transaction",
			});
			this.add_field(col, {
				fieldname: "to_voucherno",
				label: __("To Voucher No"),
				fieldtype: "Link",
				options: "Voucher Transaction",
			});
		});

		// Session location — backend only, not shown on Oracle-style screens.
		this.add_field(this.root, {
			fieldname: "location_id",
			label: __("Location"),
			fieldtype: "Link",
			options: "Location",
			hidden: 1,
			read_only: 1,
		});

		this.add_section(__("Condition"), (col) => {
			this.add_field(col, {
				fieldname: "partyid",
				label: __("Party"),
				fieldtype: "Link",
				options: "Party",
			});
			this.add_field(col, {
				fieldname: "accid",
				label: __("Account"),
				fieldtype: "Link",
				options: "Chart of Accounting",
			});
			this.add_field(col, {
				fieldname: "coa_level",
				label: __("Chart of Accounts Level"),
				fieldtype: "Int",
			});
		});

		this.add_section(__("Output"), (col) => {
			this.add_field(col, {
				fieldname: "output_mode",
				label: __("Output"),
				fieldtype: "Select",
				options: "Preview\nFile",
				default: "Preview",
			});
		});

		this.fields.accid?.set_query(() => ({
			filters: { chartlevel: 5, transflag: "Yes" },
		}));
		this.fields.partyid?.set_query(() => ({
			filters: { pcat_id: ["in", ["11", "12", "13"]] },
		}));
		const voucher_query = () => {
			const filters = {};
			if (this.session_location_id) {
				filters.location_id = this.session_location_id;
			}
			return { filters };
		};
		this.fields.from_voucherno?.set_query(voucher_query);
		this.fields.to_voucherno?.set_query(voucher_query);

		const filter_mode = this.fields.filter_mode;
		if (filter_mode) {
			const prev = filter_mode.df.onchange;
			filter_mode.df.onchange = () => {
				prev && prev();
				this.toggle_filter_mode();
			};
		}
		this.toggle_filter_mode();
	}

	add_section(label, build_fn) {
		const $section = $(`
			<div class="form-section visible-section">
				<div class="section-head collapsible">
					<span class="section-title">${frappe.utils.escape_html(label)}</span>
				</div>
				<div class="section-body">
					<div class="form-column col-sm-12"></div>
				</div>
			</div>
		`).appendTo(this.root);
		const $col = $section.find(".form-column");
		build_fn($col);
		return $section;
	}

	add_field(parent, df) {
		const field = frappe.ui.form.make_control({
			df,
			parent,
			render_input: true,
		});
		field.refresh();
		if (df.default !== undefined && df.default !== null) {
			field.set_value(df.default);
		}
		if (df.fieldname) {
			this.fields[df.fieldname] = field;
		}
		return field;
	}

	update_report_select() {
		const field = this.fields.selected_report;
		if (!field) {
			return;
		}
		const current = field.get_value();
		field.df.options = this.report_select_options();
		field.last_options = null;
		field.set_options?.();
		if (current) {
			field.set_value(current);
		}
	}

	bind_actions() {
		this.page.set_primary_action(__("Execute"), () => this.run_execute());
		this.page.add_inner_button(__("Condition"), () => this.save_parameters());
	}

	toggle_filter_mode() {
		const mode = this.get_value("filter_mode") || "Date";
		this.section_nodes.date?.toggle(mode === "Date");
		this.section_nodes.voucher?.toggle(mode === "Voucher No");
	}

	get_value(fieldname) {
		return this.fields[fieldname]?.get_value?.();
	}

	set_value(fieldname, value) {
		if (value === undefined || value === null || value === "") {
			return;
		}
		this.fields[fieldname]?.set_value?.(value);
	}

	apply_defaults() {
		const data = this.defaults || {};
		if (data.from_date) {
			this.set_value("from_date", data.from_date);
		}
		if (data.to_date) {
			this.set_value("to_date", data.to_date);
		}
		if (data.from_voucherno) {
			this.set_value("from_voucherno", data.from_voucherno);
		}
		if (data.to_voucherno) {
			this.set_value("to_voucherno", data.to_voucherno);
		}
		if (data.partyid) {
			this.set_value("partyid", data.partyid);
		}
		if (data.accid) {
			this.set_value("accid", data.accid);
		}
		if (data.coa_level) {
			this.set_value("coa_level", data.coa_level);
		}
		if (this.session_location_id) {
			this.set_value("location_id", this.session_location_id);
		}
		this.set_value("filter_mode", data.filter_mode === "voucherno" ? "Voucher No" : "Date");
		this.set_value("output_mode", data.output_mode === "file" ? "File" : "Preview");
		if (data.selected_report && this.legacy_label_map[data.selected_report]) {
			this.set_value("selected_report", this.legacy_label_map[data.selected_report]);
		}
		this.toggle_filter_mode();
	}

	get_payload() {
		const report_label = this.get_value("selected_report");
		return {
			location_id: this.session_location_id || this.get_value("location_id"),
			partyid: this.get_value("partyid"),
			accid: this.get_value("accid"),
			coa_level: this.get_value("coa_level"),
			filter_mode: this.get_value("filter_mode") === "Voucher No" ? "voucherno" : "date",
			output_mode: (this.get_value("output_mode") || "Preview").toLowerCase(),
			selected_report: this.report_legacy_map[report_label] || null,
			from_voucherno: this.get_value("from_voucherno"),
			to_voucherno: this.get_value("to_voucherno"),
			from_date: this.get_value("from_date"),
			to_date: this.get_value("to_date"),
		};
	}

	save_parameters() {
		const payload = this.get_payload();
		if (!payload.location_id) {
			frappe.msgprint(
				__(
					"Your User Rights record has no Location. Set Location on User Rights, then reload this page."
				)
			);
			return;
		}
		frappe.xcall("millitrix.api.gl_parameter_form.save_condition", { payload }).then(() => {
			frappe.show_alert({ message: __("Condition saved"), indicator: "green" });
		});
	}

	run_execute() {
		const payload = this.get_payload();
		if (!payload.selected_report) {
			frappe.msgprint(__("Select a report format."));
			return;
		}
		if (!payload.location_id) {
			frappe.msgprint(
				__(
					"Your User Rights record has no Location. Set Location on User Rights, then reload this page."
				)
			);
			return;
		}

		frappe.call({
			method: "millitrix.api.gl_parameter_form.execute",
			args: { payload },
			freeze: true,
			freeze_message: __("Running report..."),
			callback: (r) => {
				const result = r.message;
				if (!result?.report_name) {
					return;
				}
				if (result.output_mode === "file") {
					frappe.msgprint(
						__(
							"File output opens from the report view — use Menu → Export after the report loads."
						)
					);
				}
				frappe.route_options = result.filters || {};
				frappe.set_route("query-report", result.report_name);
			},
		});
	}
};
