# Copyright (c) 2026, Millitrix and contributors
# For license information, see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


def _document_transaction_update_allowed(doc=None) -> bool:
        """Allow Document Transaction mutation only from trusted posting code."""
        if getattr(frappe.flags, "allow_document_transaction_update", False):
                return True
        if doc is not None and getattr(getattr(doc, "flags", None), "allow_document_transaction_update", False):
                return True
        return False


def _block_direct_document_transaction_update(doc=None) -> None:
        if _document_transaction_update_allowed(doc):
                return
        frappe.throw(
                _(
                        "Document Transaction is system-generated. Use the source voucher/document "
                        "submit/cancel flow or an approved adjustment document."
                ),
                title=_("Direct Posting Row Update Blocked"),
        )


class DocumentTransaction(Document):
        def before_insert(self):
                _block_direct_document_transaction_update(self)

        def before_save(self):
                _block_direct_document_transaction_update(self)

        def before_delete(self):
                _block_direct_document_transaction_update(self)
