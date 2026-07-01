// Oracle Change_User_Pwd.fmb — change password for current user (managers may pick another user).

frappe.pages["change-user-password"].on_page_load = function (wrapper) {
	new millitrix.ChangeUserPassword(wrapper);
};

frappe.provide("millitrix");

millitrix.ChangeUserPassword = class ChangeUserPassword {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.can_pick_user = frappe.user.has_role("System Manager")
			|| frappe.user.has_role("Millitrix ERP Manager");
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Change User Password"),
			single_column: false,
		});
		this.make_form();
	}

	make_form() {
		const fields = [
			{
				fieldname: "user",
				label: __("User Id"),
				fieldtype: "Link",
				options: "User",
				default: frappe.session.user,
				read_only: this.can_pick_user ? 0 : 1,
				reqd: 1,
				change: () => this.load_user_display(),
			},
			{
				fieldname: "user_name",
				label: __("User Name"),
				fieldtype: "Data",
				read_only: 1,
			},
			{
				fieldname: "empno",
				label: __("Employee"),
				fieldtype: "Link",
				options: "Employee Setup",
				read_only: 1,
			},
			{
				fieldname: "employee_name",
				label: __("Employee"),
				fieldtype: "Data",
				read_only: 1,
			},
			{
				fieldname: "old_password",
				label: __("Current Password"),
				fieldtype: "Password",
			},
			{
				fieldname: "new_password",
				label: __("Password"),
				fieldtype: "Password",
				reqd: 1,
			},
			{
				fieldname: "confirm_password",
				label: __("Confirm Password"),
				fieldtype: "Password",
				reqd: 1,
			},
			{
				fieldname: "logout_all_sessions",
				label: __("Logout All Other Sessions"),
				fieldtype: "Check",
				default: 1,
			},
		];

		this.form = new frappe.ui.FieldGroup({
			fields,
			body: this.page.main,
		});
		this.form.make();
		this.load_user_display();
		this.toggle_old_password();

		this.form.fields_dict.user?.$input?.on("change", () => this.toggle_old_password());

		this.page.set_primary_action(__("Update Password"), () => this.update_password());
	}

	toggle_old_password() {
		const user = this.form.get_value("user") || frappe.session.user;
		const is_self = user === frappe.session.user;
		const field = this.form.fields_dict.old_password;
		if (!field) {
			return;
		}
		field.df.reqd = is_self ? 1 : 0;
		field.toggle(is_self);
		if (!is_self) {
			this.form.set_value("old_password", "");
		}
	}

	load_user_display() {
		const user = this.form.get_value("user");
		if (!user) {
			return;
		}
		frappe.db.get_value("User", user, ["full_name", "username"]).then((r) => {
			this.form.set_value("user_name", r?.message?.full_name || r?.message?.username || "");
		}).catch(() => {});
		const rights_filters = { userid: user };
		frappe.db.get_value("User Rights", rights_filters, "empno").then((r) => {
			const empno = r?.message?.empno;
			this.form.set_value("empno", empno || "");
			if (!empno) {
				this.form.set_value("employee_name", "");
				return;
			}
			frappe.db.get_value("Employee Setup", empno, "ename").then((er) => {
				this.form.set_value("employee_name", er?.message?.ename || "");
			}).catch(() => {});
		}).catch(() => {});
	}

	update_password() {
		const values = this.form.get_values();
		if (!values) {
			return;
		}
		if (values.new_password !== values.confirm_password) {
			frappe.msgprint(__("Password and confirmation do not match"));
			return;
		}

		const target_user = values.user || frappe.session.user;
		const is_self = target_user === frappe.session.user;

		if (is_self && !values.old_password) {
			frappe.msgprint(__("Current Password is required"));
			return;
		}

		if (is_self) {
			frappe.call({
				method: "frappe.core.doctype.user.user.update_password",
				args: {
					new_password: values.new_password,
					old_password: values.old_password,
					logout_all_sessions: values.logout_all_sessions ? 1 : 0,
				},
				error: millitrix.api.default_error(__("Password update failed")),
				callback: () => {
					frappe.show_alert({ message: __("Password updated"), indicator: "green" });
					this.form.set_value("new_password", "");
					this.form.set_value("confirm_password", "");
					if (values.old_password !== undefined) {
						this.form.set_value("old_password", "");
					}
				},
			});
			return;
		}

		frappe.call({
			method: "millitrix.api.change_password.set_user_password",
			args: {
				user: target_user,
				new_password: values.new_password,
				logout_all_sessions: values.logout_all_sessions ? 1 : 0,
			},
			error: millitrix.api.default_error(__("Password update failed")),
			callback: () => {
				frappe.show_alert({ message: __("Password updated"), indicator: "green" });
				this.form.set_value("new_password", "");
				this.form.set_value("confirm_password", "");
			},
		});
	}
};
