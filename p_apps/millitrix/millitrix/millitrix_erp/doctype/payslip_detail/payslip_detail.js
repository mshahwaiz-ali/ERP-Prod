// Oracle Pay_PaySlip.fmb — auto-fill salary + advance on employee select.

frappe.ui.form.on("PaySlip Detail", {
	empno(frm, cdt, cdn) {
		const parent = frm.doctype === "PaySlip" ? frm : cur_frm;
		if (!parent || parent.doctype !== "PaySlip") {
			return;
		}
		const row = locals[cdt][cdn];
		if (!row.empno || parent.doc.docstatus !== 0) {
			return;
		}
		frappe.call({
			method: "millitrix.api.payslip.fetch_employee_line_defaults",
			args: {
				empno: row.empno,
				location_id: parent.doc.location_id,
			},
			callback(r) {
				const d = r.message || {};
				if (flt(d.amount)) {
					frappe.model.set_value(cdt, cdn, "amount", d.amount);
				}
				frappe.model.set_value(cdt, cdn, "balance", flt(d.balance));
			},
			error: millitrix.api.default_error(__("Could not load employee details")),
		});
	},
});
