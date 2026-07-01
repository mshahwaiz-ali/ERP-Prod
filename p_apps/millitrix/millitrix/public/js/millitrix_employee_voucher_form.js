// Copyright (c) 2026, Millitrix and contributors
// Employee Payment / Receipt Voucher — Oracle CNBEmpVoucher.fmx grid (Emp No, Name, Amount).

frappe.provide("millitrix.employee_voucher");

millitrix.employee_voucher.DOCTYPES = [
	"Employee Payment Voucher",
	"Employee Receipt Voucher",
];

millitrix.employee_voucher.apply_grid = function (frm) {
	if (!this.DOCTYPES.includes(frm.doctype)) {
		return;
	}
	frm.toggle_display("details", false);
	millitrix.knockoff.apply_cnb_document_grid(
		frm,
		"documents",
		millitrix.knockoff.CNB_DOCUMENT_EMPLOYEE_GRID
	);
};

millitrix.employee_voucher.update_total = function (frm) {
	if (!this.DOCTYPES.includes(frm.doctype)) {
		return;
	}
	const rows = frm.doc.documents || [];
	const line_total = rows.reduce((sum, row) => sum + flt(row.amount), 0);
	if (frm.doc.docstatus === 0) {
		frm.set_value("amount", line_total);
	}
	const show_total = rows.length >= 1 || frm.doc.docstatus === 1;
	frm.toggle_display("amount", show_total);
};

millitrix.employee_voucher.setup = function (frm) {
	if (!this.DOCTYPES.includes(frm.doctype)) {
		return;
	}
	if (!frm.doc.doctypeid) {
		frm.set_value("doctypeid", frm.doctype);
	}
	this.apply_grid(frm);
	this.update_total(frm);
	if (!frm.is_new()) {
		millitrix.knockoff.add_accounting_button(frm, {
			document_id_field: "empvno",
			method: "millitrix.api.knockoff.get_cnb_accounting_lines",
		});
	}
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
};

millitrix.employee_voucher.DOCTYPES.forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		onload(frm) {
			if (!frm.doc.doctypeid) {
				frm.set_value("doctypeid", doctype);
			}
		},

		refresh(frm) {
			millitrix.employee_voucher.setup(frm);
		},

		documents_add(frm) {
			setTimeout(() => {
				millitrix.employee_voucher.apply_grid(frm);
				millitrix.employee_voucher.update_total(frm);
			}, 100);
		},

		documents_remove(frm) {
			millitrix.employee_voucher.update_total(frm);
		},
	});
});

frappe.ui.form.on("Cash and Bank Voucher Document", {
	amount(frm, cdt, cdn) {
		if (millitrix.employee_voucher.DOCTYPES.includes(frm.doctype)) {
			millitrix.employee_voucher.update_total(frm);
		}
	},
	empno(frm) {
		if (millitrix.employee_voucher.DOCTYPES.includes(frm.doctype)) {
			millitrix.employee_voucher.update_total(frm);
		}
	},
});
