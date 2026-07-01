# Copyright (c) 2026, Millitrix and contributors
# Strip placeholder child rows before validate (Oracle never saved empty grid lines).

from __future__ import annotations

from frappe.utils import flt

# Child DocType → fields that indicate a real line (any non-empty value counts).
BLANK_ROW_KEYS: dict[str, list[str]] = {
	"Crash Refine Input": ["critem", "storeid", "bagqty"],
	"Crash Refine Output": ["proditem"],
	"Sales Invoice Detail": ["storeid", "truckqty", "bagqty", "sonumber"],
	"Purchase Invoice Detail": ["storeid", "truckqty", "bagqty", "ponumber"],
	"Sales Return Detail": ["storeid", "truckqty", "bagqty"],
	"Purchase Return Detail": ["storeid", "truckqty", "bagqty"],
	"Gate Pass Detail": ["storeid", "truckqty", "truckno"],
	"Stock Transfer Detail": ["tostoreid", "truckqty", "delikanta"],
	"Stock Adjustment Detail": ["storeid", "itemcode"],
	"Opening Stock Detail": ["storeid", "itemcode"],
	"Purchase Other Bill Detail": ["itemcode", "quantity"],
	"Sales Other Bill Detail": ["itemcode", "quantity"],
	"Purchase Other Bill Return Detail": ["pbdetlno", "quantity"],
	"Sales Other Bill Return Detail": ["sbdetlno", "quantity"],
	"PO Cancellation Detail": ["ponumber", "itemcode", "cancelqty"],
	"SO Cancellation Detail": ["sonumber", "cancelqty"],
	"Voucher Transaction Detail": ["accid", "debit", "credit"],
	"PaySlip Detail": ["empno", "amount"],
	"Payment and Receipt Document": ["documentid", "amount"],
	"Adjustment PNR": ["pnrno", "amount"],
	"Adjustment Invoice": ["documentid", "amount"],
	"Cash and Bank Voucher Document": ["documentid", "amount"],
	"Expense Voucher Detail": ["accid", "debit", "credit"],
	"Hawala Invoice": ["documentid", "amount"],
	"Hawala Party B": ["accid", "amount"],
}


def row_has_data(row, key_fields: list[str]) -> bool:
	for field in key_fields:
		value = row.get(field) if hasattr(row, "get") else getattr(row, field, None)
		if value is None or value == "":
			continue
		if isinstance(value, (int, float)) and flt(value) == 0:
			continue
		return True
	return False


def strip_blank_child_rows(doc, table_field: str, child_doctype: str | None = None) -> int:
	"""Remove empty placeholder rows from a child table. Returns count removed."""
	rows = list(doc.get(table_field) or [])
	if not rows:
		return 0

	if not child_doctype:
		meta = doc.meta.get_field(table_field)
		child_doctype = meta.options if meta else None
	if not child_doctype:
		return 0

	key_fields = BLANK_ROW_KEYS.get(child_doctype)
	if not key_fields:
		return 0

	kept = [row for row in rows if row_has_data(row, key_fields)]
	removed = len(rows) - len(kept)
	if removed:
		doc.set(table_field, kept)
	return removed


def strip_blank_rows_for_doc(doc) -> int:
	"""Strip blank rows from all known child tables on a document."""
	total = 0
	for field in doc.meta.get_table_fields():
		total += strip_blank_child_rows(doc, field.fieldname, field.options)
	return total
