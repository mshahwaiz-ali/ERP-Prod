frappe.ui.form.on('Stock Ledger Entry', {
        refresh(frm) {
                frm.disable_save();
        }
});
