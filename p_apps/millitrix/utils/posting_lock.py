
# P0-09 Atomic Posting Layer (FIXED)

import frappe
from contextlib import contextmanager

@contextmanager
def atomic_posting():
    """
    Frappe-native safe transaction boundary.
    Ensures stock + accounting + doctransaction atomicity.
    """
    with frappe.db.transaction():
        yield
