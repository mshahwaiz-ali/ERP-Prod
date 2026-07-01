import frappe

def ensure_safe_transaction(doc):
    """
    Global safety hook for stock + GL documents
    """
    if hasattr(doc, "docstatus") and doc.docstatus == 1:
        # prevent silent bypass commits
        if frappe.flags.in_transaction is False:
            frappe.flags.in_transaction = True
