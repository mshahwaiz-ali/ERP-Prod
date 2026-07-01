// Oracle PurchParaForm / SalesParaForm / … — shared report launcher UI.
frappe.provide("millitrix.para_form");

millitrix.para_form.boot = function (wrapper, formKey) {
	const cacheKey = `_para_form_${formKey}`;
	if (wrapper[cacheKey]) {
		return;
	}
	wrapper[cacheKey] = new millitrix.ParaFormLauncher(wrapper, formKey);
};

millitrix.para_form.on_page_show = function (wrapper, formKey) {
	const cacheKey = `_para_form_${formKey}`;
	const inst = wrapper[cacheKey];
	if (!inst || !inst.root?.length || !$.contains(document, inst.root[0])) {
		wrapper[cacheKey] = null;
		millitrix.para_form.boot(wrapper, formKey);
		return;
	}
	const refresh = inst._initPromise || inst.reload_defaults();
	refresh.then(() => inst.apply_defaults());
};

millitrix.ParaFormLauncher = class {
	constructor(wrapper, formKey) {
		this.wrapper = wrapper;
		this.formKey = formKey;
		this.fields = {};
		this.report_legacy_map = {};
		this.legacy_label_map = {};
		this.session_location_id = null;
		this.defaults = {};
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Parameter Form"),
			single_column: false,
		});
		this.bind_actions();
		this.init();
	}

	async init() {
		this._initPromise = this.reload_defaults();
		await this._initPromise;
		this._initPromise = null;
		if (this.page?.set_title && this.defaults?.title) {
			this.page.set_title(this.defaults.title);
		}
		if (!this.root) {
			this.make_layout();
			this.apply_defaults();
		} else {
			this.apply_defaults();
		}
	}

	async reload_defaults() {
		if (this._reloadPromise) {
			return this._reloadPromise;
		}
		this._reloadPromise = this._fetch_defaults().finally(() => {
			this._reloadPromise = null;
		});
		return this._reloadPromise;
	}

	async _fetch_defaults() {
		try {
			this.defaults = await frappe.xcall("millitrix.api.para_form.get_defaults", {
				form_key: this.formKey,
			});
		} catch (e) {
			this.defaults = { reports: [], condition_fields: [] };
			if (!frappe.request.is_frozen) {
				frappe.msgprint(__("Could not load parameter form defaults."));
			}
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
		return ["", ...Object.keys(this.report_legacy_map)].join("\n");
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

		this.add_section(__("Date"), (col) => {
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

		this.add_field(this.root, {
			fieldname: "location_id",
			label: __("Location"),
			fieldtype: "Link",
			options: "Location",
			hidden: 1,
			read_only: 1,
		});

		this.add_section(__("Condition"), (col) => {
			(this.defaults?.condition_fields || []).forEach((df) => {
				this.add_field(col, df);
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

		this.apply_field_queries();
	}

	apply_field_queries() {
		this.fields.accid?.set_query(() => ({
			filters: { chartlevel: 5, transflag: "Yes" },
		}));
		(this.defaults?.condition_fields || []).forEach((df) => {
			if (!df.pcat_id?.length) {
				return;
			}
			this.fields[df.fieldname]?.set_query(() => ({
				filters: { pcat_id: ["in", df.pcat_id] },
			}));
		});
		if (this.fields.storeid) {
			this.fields.storeid.set_query(() => {
				const filters = {};
				if (this.session_location_id) {
					filters.location_id = this.session_location_id;
				}
				return { filters };
			});
		}
		["from_storeid", "to_storeid"].forEach((fieldname) => {
			if (!this.fields[fieldname]) {
				return;
			}
			this.fields[fieldname].set_query(() => {
				const filters = {};
				if (this.session_location_id) {
					filters.location_id = this.session_location_id;
				}
				return { filters };
			});
		});
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
		build_fn($section.find(".form-column"));
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
		if (this.session_location_id) {
			this.set_value("location_id", this.session_location_id);
		}
		this.set_value("output_mode", data.output_mode === "file" ? "File" : "Preview");
		if (data.selected_report && this.legacy_label_map[data.selected_report]) {
			this.set_value("selected_report", this.legacy_label_map[data.selected_report]);
		}
		(data.condition_fields || []).forEach((df) => {
			if (data[df.fieldname] !== undefined) {
				this.set_value(df.fieldname, data[df.fieldname]);
			}
		});
	}

	get_payload() {
		const report_label = this.get_value("selected_report");
		const payload = {
			location_id: this.session_location_id || this.get_value("location_id"),
			output_mode: (this.get_value("output_mode") || "Preview").toLowerCase(),
			selected_report: this.report_legacy_map[report_label] || null,
			from_date: this.get_value("from_date"),
			to_date: this.get_value("to_date"),
		};
		(this.defaults?.condition_fields || []).forEach((df) => {
			payload[df.fieldname] = this.get_value(df.fieldname);
		});
		return payload;
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
		frappe
			.xcall("millitrix.api.para_form.save_condition", {
				form_key: this.formKey,
				payload,
			})
			.then(() => {
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
			method: "millitrix.api.para_form.execute",
			args: { form_key: this.formKey, payload },
			freeze: true,
			freeze_message: __("Running report..."),
			error: millitrix.api.default_error(__("Report execution failed")),
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
