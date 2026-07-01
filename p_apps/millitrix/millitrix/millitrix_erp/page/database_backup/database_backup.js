// Oracle BACKUP.fmb — database backup button (exp.exe equivalent).

frappe.pages["database-backup"].on_page_load = function (wrapper) {
	new millitrix.DatabaseBackup(wrapper);
};

frappe.provide("millitrix");

millitrix.DatabaseBackup = class DatabaseBackup {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Database Backup"),
			single_column: false,
		});
		this.make_form();
		this.load_recent();
	}

	make_form() {
		const fields = [
			{
				fieldname: "include_files",
				label: __("Include public/private files"),
				fieldtype: "Check",
				default: 0,
				description: __("Oracle form backed up database only; leave unchecked for faster backup."),
			},
			{
				fieldname: "help",
				fieldtype: "HTML",
				options: `<p class="text-muted">${__(
					"Backup files are stored under the site private/backups folder."
				)}</p>`,
			},
		];

		this.form = new frappe.ui.FieldGroup({ fields, body: this.page.main });
		this.form.make();

		this.page.set_primary_action(__("Backup"), () => this.run_backup(), "database");
		this.page.add_inner_button(__("Refresh List"), () => this.load_recent());
		this.recent_section = $('<div class="mt-4"></div>').appendTo(this.page.main);
	}

	run_backup() {
		const include_files = this.form.get_value("include_files") ? 1 : 0;
		this.page.set_primary_action(__("Backing up…"), null, "spinner");
		frappe.call({
			method: "millitrix.api.database_backup.run_database_backup",
			args: { include_files },
			freeze: true,
			freeze_message: __("Creating database backup…"),
			error: millitrix.api.default_error(__("Backup failed")),
			callback: (r) => {
				this.page.set_primary_action(__("Backup"), () => this.run_backup(), "database");
				const msg = r.message || {};
				frappe.show_alert({
					message: __("Backup created: {0}", [msg.database_name || ""]),
					indicator: "green",
				});
				this.load_recent();
			},
		});
	}

	load_recent() {
		frappe.call({
			method: "millitrix.api.database_backup.list_recent_backups",
			args: { limit: 15 },
			callback: (r) => {
				const rows = r.message || [];
				let html = `<h5>${__("Recent Backups")}</h5>`;
				if (!rows.length) {
					html += `<p class="text-muted">${__("No backup files found yet.")}</p>`;
				} else {
					html += '<table class="table table-bordered table-sm"><thead><tr>';
					html += `<th>${__("File")}</th><th>${__("Size")}</th><th>${__("Modified")}</th>`;
					html += "</tr></thead><tbody>";
					rows.forEach((row) => {
						const size_kb = Math.round((row.size || 0) / 1024);
						const modified = frappe.datetime.convert_to_user_tz(
							frappe.datetime.timestamp_to_datetime(row.modified)
						);
						html += `<tr><td>${frappe.utils.escape_html(row.name)}</td>`;
						html += `<td>${size_kb} KB</td>`;
						html += `<td>${frappe.datetime.str_to_user(modified)}</td></tr>`;
					});
					html += "</tbody></table>";
				}
				this.recent_section.html(html);
			},
		});
	}
};
