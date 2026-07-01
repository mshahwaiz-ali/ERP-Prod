frappe.provide("millitrix");

frappe.pages["year-end-closing"].on_page_load = function (wrapper) {
	new millitrix.YearEndClosing(wrapper);
};

millitrix.YearEndClosing = class YearEndClosing {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Year End Closing"),
			single_column: false,
		});
		this.preview_data = null;
		this.make_form();
		this.load_defaults();
	}

	make_form() {
		this.fields = {};
		const field_defs = [
			{
				fieldname: "location_id",
				label: __("Location"),
				fieldtype: "Link",
				options: "Location",
				reqd: 1,
			},
			{
				fieldname: "closing_date",
				label: __("Closing Date"),
				fieldtype: "Date",
				reqd: 1,
				default: frappe.datetime.get_today(),
			},
			{
				fieldname: "opening_date",
				label: __("Opening Date"),
				fieldtype: "Date",
			},
			{
				fieldname: "fy_from_date",
				label: __("Fiscal Year From"),
				fieldtype: "Date",
			},
			{
				fieldname: "capital_acc",
				label: __("Capital Account"),
				fieldtype: "Link",
				options: "Chart of Accounting",
			},
		];

		this.form_area = $(`<div class="year-end-closing-form"></div>`).appendTo(this.page.main);
		field_defs.forEach((def) => {
			const field = frappe.ui.form.make_control({
				df: def,
				parent: this.form_area,
				render_input: true,
			});
			field.refresh();
			this.fields[def.fieldname] = field;
		});

		this.preview_area = $(`<div class="preview-area mt-4"></div>`).appendTo(this.page.main);

		this.page.set_primary_action(__("Preview"), () => this.run_preview());
		this.page.set_secondary_action(__("Execute Closing"), () => this.run_execute());
	}

	load_defaults() {
		frappe
			.xcall("millitrix.millitrix_erp.page.year_end_closing.year_end_closing.get_defaults")
			.then((data) => {
				if (data?.location_id) {
					this.fields.location_id.set_value(data.location_id);
				}
			});
	}

	get_values() {
		const values = {};
		for (const [key, field] of Object.entries(this.fields)) {
			values[key] = field.get_value();
		}
		return values;
	}

	run_preview() {
		const values = this.get_values();
		if (!values.location_id || !values.closing_date) {
			frappe.msgprint(__("Location and Closing Date are required"));
			return;
		}

		frappe.call({
			method: "millitrix.api.year_end_closing.preview",
			args: values,
			freeze: true,
			freeze_message: __("Building preview..."),
			error: millitrix.api.default_error(__("Year-end preview failed")),
			callback: (r) => {
				this.preview_data = r.message;
				this.render_preview(r.message);
			},
		});
	}

	run_execute() {
		if (!this.preview_data?.can_execute) {
			frappe.msgprint(__("Run Preview first and resolve all blockers and warnings"));
			return;
		}

		frappe.confirm(
			__(
				"This will submit P&L closing, stock closing/opening, and GL opening vouchers. Continue?"
			),
			() => {
				frappe.call({
					method: "millitrix.api.year_end_closing.execute",
					args: this.get_values(),
					freeze: true,
					freeze_message: __("Running year-end closing..."),
					error: millitrix.api.default_error(__("Year-end closing failed")),
					callback: (r) => {
						this.render_result(r.message);
					},
				});
			}
		);
	}

	format_amount(value) {
		return frappe.format(value || 0, { fieldtype: "Currency" });
	}

	render_preview(data) {
		const tb = data.trial_balance || {};
		const pnl = data.pnl_summary || {};
		let html = `<div class="alert ${data.can_execute ? "alert-success" : "alert-warning"}">`;

		if (data.blockers?.length) {
			html += `<p><strong>${__("Blockers")}:</strong> ${data.blockers.join("; ")}</p>`;
		}
		if (data.warnings?.length) {
			html += `<p><strong>${__("Warnings")}:</strong> ${data.warnings.join("; ")}</p>`;
		}
		if (data.can_execute) {
			html += `<p>${__("Ready to execute year-end closing.")}</p>`;
		}
		html += `</div>`;

		html += `<table class="table table-bordered table-sm">
			<tr><td>${__("Closing Date")}</td><td>${data.closing_date}</td></tr>
			<tr><td>${__("Opening Date")}</td><td>${data.opening_date}</td></tr>
			<tr><td>${__("Fiscal Year From")}</td><td>${data.fy_from_date}</td></tr>
			<tr><td>${__("Capital Account")}</td><td>${data.capital_acc}</td></tr>
			<tr><td>${__("Trial Balance Balanced")}</td><td>${tb.balanced ? __("Yes") : __("No")}</td></tr>
			<tr><td>${__("Closing Debit")}</td><td>${this.format_amount(tb.total_closing_debit)}</td></tr>
			<tr><td>${__("Closing Credit")}</td><td>${this.format_amount(tb.total_closing_credit)}</td></tr>
			<tr><td>${__("Total Revenue")}</td><td>${this.format_amount(pnl.total_revenue)}</td></tr>
			<tr><td>${__("Total Expense")}</td><td>${this.format_amount(pnl.total_expense)}</td></tr>
			<tr><td>${__("Net Profit")}</td><td>${this.format_amount(pnl.net_profit)}</td></tr>
			<tr><td>${__("Stock Lines")}</td><td>${data.stock_line_count || 0}</td></tr>
			<tr><td>${__("GL Opening Lines")}</td><td>${data.gl_line_count || 0}</td></tr>
		</table>`;

		this.preview_area.html(html);
	}

	render_result(data) {
		const created = data.created || {};
		let rows = "";
		for (const [key, value] of Object.entries(created)) {
			if (value?.skipped) {
				rows += `<tr><td>${key}</td><td colspan="2">${value.reason}</td></tr>`;
			} else if (value?.doctype) {
				rows += `<tr><td>${key}</td><td>${value.doctype}</td><td><a href="/app/${frappe.router.slug(
					value.doctype
				)}/${value.name}">${value.name}</a></td></tr>`;
			}
		}

		this.preview_area.html(`
			<div class="alert alert-success">${__("Year-end closing completed.")}</div>
			<table class="table table-bordered table-sm">
				<thead><tr><th>${__("Step")}</th><th>${__("DocType")}</th><th>${__("Document")}</th></tr></thead>
				<tbody>${rows}</tbody>
			</table>
		`);
		this.preview_data = null;
	}
};
