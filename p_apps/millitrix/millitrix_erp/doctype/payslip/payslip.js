// Copyright (c) 2026, Millitrix and contributors
// Oracle Pay_PaySlip.fmb — Generate Salary + employee grid.

frappe.provide("millitrix.payslip");

millitrix.payslip.apply_employee_grid = function (frm) {
	const grid = frm.fields_dict.employees?.grid;
	if (!grid?.update_docfields_property) {
		return;
	}
	["psdetlid"].forEach((field) => {
		grid.update_docfields_property(field, "hidden", 1);
	});
	grid.refresh();
};

millitrix.payslip.setup_queries = function (frm) {
	frm.set_query("empno", "employees", () => ({
		query: "millitrix.api.payslip.empno_query",
		filters: { location_id: frm.doc.location_id || "" },
	}));
};

millitrix.payslip.apply_default_location = function (frm) {
	if (frm.doc.location_id || !frm.is_new()) {
		return;
	}
	frappe.call({
		method: "millitrix.api.user_context.get_user_scope",
		callback(r) {
			const loc = r.message?.location_id;
			if (loc && !frm.doc.location_id) {
				frm.set_value("location_id", loc);
			}
		},
	});
};

millitrix.payslip.setup = function (frm) {
	if (!frm.doc.doctypeid) {
		frm.set_value("doctypeid", "PaySlip");
	}
	millitrix.payslip.setup_queries(frm);
	millitrix.payslip.apply_employee_grid(frm);
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}

	if (frm.doc.docstatus === 0) {
		frm.add_custom_button(__("Generate Salary"), () => {
			frappe.call({
				method: "millitrix.api.payslip.generate_salary_lines",
				args: { location_id: frm.doc.location_id },
				freeze: true,
				freeze_message: __("Generating salary lines..."),
				error: millitrix.api.default_error(__("Could not generate salary lines")),
				callback(r) {
					const rows = r.message || [];
					if (!rows.length) {
						frappe.msgprint(__("No eligible employees found for this location"));
						return;
					}
					frm.clear_table("employees");
					rows.forEach((row) => {
						const line = frm.add_child("employees");
						line.empno = row.empno;
						line.amount = row.amount;
						line.balance = row.balance || 0;
					});
					frm.refresh_field("employees");
					millitrix.payslip.apply_employee_grid(frm);
				},
			});
		});
	}

	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, {
			document_id_field: "pslipid",
			method: "millitrix.api.payslip.get_payslip_accounting_lines",
		});
	}
};

frappe.ui.form.on("PaySlip", {
	onload(frm) {
		if (!frm.doc.doctypeid) {
			frm.set_value("doctypeid", "PaySlip");
		}
		if (frm.is_new()) {
			if (!frm.doc.pdate) {
				frm.set_value("pdate", frappe.datetime.get_today());
			}
			if (!frm.doc.paymonth) {
				frm.set_value("paymonth", frappe.datetime.month_start());
			}
		}
		millitrix.payslip.apply_default_location(frm);
	},

	refresh(frm) {
		millitrix.payslip.setup(frm);
	},

	employees_add(frm) {
		setTimeout(() => millitrix.payslip.apply_employee_grid(frm), 100);
	},
});
