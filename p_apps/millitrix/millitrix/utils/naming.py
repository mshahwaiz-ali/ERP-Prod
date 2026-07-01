# Copyright (c) 2026, Millitrix and contributors
# Client document numbers: {PREFIX}-{YYMM}-{seq} e.g. PI-2606-0001

from __future__ import annotations

import frappe
from frappe import _

from frappe.utils import getdate

_DATE_FIELDS = (
	"vouchdate",
	"invdate",
	"podate",
	"sodate",
	"adjdate",
	"gmdate",
	"brdate",
	"billdate",
	"pnrdate",
	"opening_date",
	"gpdate",
	"usdate",
	"paymonth",
	"opendate",
	"tdate",
	"sadate",
	"retdate",
	"candate",
	"pdate",
	"crdate",
	"ipdate",
	"incdate",
)

# DocTypes that keep Oracle-specific id rules (not PREFIX-YYMM-0001).
PREFIX_EXCLUDE: frozenset[str] = frozenset(
	{
		"Chart of Accounting",
		"Party",  # {category}-{YYMM}-0001 via party.py
		"Party Category",
		"Transaction Category",
		"Transaction List",
		"User Rights",
		"Report Parameter",
		"Item Price List",
	}
)

# Human-readable prefix per DocType (autoname field).
DOCTYPE_PREFIX: dict[str, str] = {
	# Trading
	"Purchase Order": "PO",
	"PO Cancellation": "POC",
	"Purchase Invoice": "PI",
	"Purchase Return": "PRET",
	"Purchase Other Bill": "POB",
	"Purchase Return Other Bill": "PROB",
	"Sales Order": "SO",
	"SO Cancellation": "SOC",
	"Sales Invoice": "SI",
	"Sales Return": "SRET",
	"Sales Other Bill": "SOB",
	"Sales Return Other Bill": "SROB",
	"In Out Gate Pass": "GP",
	# Stock / production
	"Opening Stock": "OS",
	"Closing Stock": "CS",
	"Stock Adjustment": "STK",
	"Stock Transfer Note": "STN",
	"Crashing Refine": "CR",
	# Finance — PNR / CNB
	"Purchase Invoice Payment": "PIP",
	"Sales Invoice Receipt": "SIR",
	"Broker Invoice Payment": "BIP",
	"Advance PNR": "AP",
	"Advance Payment": "AP",
	"Advance Receipt": "AR",
	"Payable Discount Note": "PDN",
	"Receivable Discount Note": "RDN",
	"Payment Voucher": "PV",
	"Receipt Voucher": "RV",
	"Expense Voucher": "EV",
	"Party Payment Voucher": "PPV",
	"Party Receipt Voucher": "PRV",
	"Employee Payment Voucher": "EPV",
	"Employee Receipt Voucher": "ERV",
	"Paid Advance Adjustment": "PAA",
	"Received Advance Adjustment": "RAA",
	"Payment By Hawala": "HAW",
	"Party Gross Margin": "PGM",
	"Accounts Opening": "GLO",
	"Voucher Transaction": "VT",
	"Closing and Adjustment Entries": "CAE",
	"Un-Submit Documents": "US",
	"PaySlip": "PS",
	"Advance Adjustment": "AA",
	"Payment and Receipt Voucher": "PNR",
	"Cash and Bank Voucher": "CNB",
	"Pay Salary Increment": "INC",
	"GL Statements": "GLS",
	# Masters / setup
	"Item Setup": "ITM",
	"Bank": "BNK",
	"Location": "LOC",
	"Employee Setup": "EMP",
	"Store Setup": "STR",
	"Store Types": "STT",
	"Item Class": "ICL",
	"City Setup": "CTY",
	"Designation": "DSG",
	"Departments": "DPT",
	"Employee Category": "ECA",
	"Transaction Category": "TCA",
	"Transaction List": "TRL",
	"Voucher Type": "VTY",
	"User Rights": "USR",
	"Menu": "MNU",
	"Module": "MOD",
	"Document Type": "DTP",
	"Mill Information": "MIL",
	"Other Contact Setup": "OCT",
}


def resolve_doctype_prefix(doc) -> str | None:
	if doc.doctype in PREFIX_EXCLUDE:
		return None
	prefix = DOCTYPE_PREFIX.get(doc.doctype)
	if doc.doctype == "Advance PNR":
		return "AR" if doc.get("advance_flow") == "Receipt" else "AP"
	return prefix


def get_next_numeric_id(doctype: str, fieldname: str) -> int:
	"""Fallback for unmapped DocTypes — only pure numeric legacy rows count."""
	result = frappe.db.sql(
		f"""
		SELECT COALESCE(MAX(CAST(`{fieldname}` AS UNSIGNED)), 0)
		FROM `tab{doctype}`
		WHERE `{fieldname}` REGEXP '^[0-9]+$'
		"""
	)
	return int(result[0][0]) + 1


def get_next_prefixed_no(
	doctype: str,
	fieldname: str,
	prefix: str,
	doc_date,
	*,
	location_id: str | None = None,
	seq_width: int = 4,
) -> str:
	"""Pattern: PI-2606-0001 (prefix + YYMM + monthly sequence).

	Legacy numeric ids (10001, 1001, …) are ignored — only rows matching
	``{prefix}-{yymm}-*`` advance the counter for the current month.
	"""
	period = getdate(doc_date).strftime("%y%m")
	head = f"{prefix}-{period}-"
	conditions = [f"`{fieldname}` LIKE %s"]
	params: list = [f"{head}%"]
	if location_id and frappe.get_meta(doctype).has_field("location_id"):
		conditions.append("location_id = %s")
		params.append(location_id)

	rows = frappe.db.sql(
		f"SELECT `{fieldname}` FROM `tab{doctype}` WHERE {' AND '.join(conditions)}",
		params,
	)
	max_seq = 0
	for (raw,) in rows:
		parts = str(raw).split("-")
		if len(parts) < 3:
			continue
		try:
			max_seq = max(max_seq, int(parts[-1]))
		except ValueError:
			continue
	return f"{head}{max_seq + 1:0{seq_width}d}"


def resolve_document_key(doc, fieldname: str) -> str:
	"""Posting / knockoff key — use full prefixed id string (e.g. PI-2606-0001)."""
	val = doc.get(fieldname)
	if val is None or val == "":
		frappe.throw(_("Document number missing on {0}").format(doc.doctype))
	return str(val).strip()


def get_next_legacy_document_no(
	doctype: str,
	fieldname: str,
	location_id: str,
	doc_date,
	*,
	voucher_type_id: str | None = None,
	seq_start: int = 10001,
) -> int:
	"""Legacy Oracle numeric pattern — kept for unmigrated rows only."""
	dt = getdate(doc_date)
	yy_mm = dt.strftime("%y%m")
	loc = str(int(location_id))
	middle = str(voucher_type_id) if voucher_type_id else ""
	prefix = f"{loc}{middle}{yy_mm}"

	rows = frappe.db.sql(
		f"""
		SELECT `{fieldname}`
		FROM `tab{doctype}`
		WHERE location_id = %s AND CAST(`{fieldname}` AS CHAR) LIKE %s
		""",
		(location_id, f"{prefix}%"),
	)
	max_seq = seq_start - 1
	for (raw,) in rows:
		val = str(raw)
		if val.isdigit():
			val = str(int(val))
		if val.startswith(prefix) and len(val) >= len(prefix) + 5:
			max_seq = max(max_seq, int(val[-5:]))
	return int(f"{prefix}{max_seq + 1:05d}")


def _autoname_field(doctype: str) -> str | None:
	autoname = (frappe.get_meta(doctype).autoname or "").strip()
	if autoname.startswith("field:"):
		return autoname.split(":", 1)[1]
	return None


def autoname_value_exists(doctype: str, value) -> bool:
	if value in (None, ""):
		return False
	return bool(frappe.db.exists(doctype, str(value).strip()))


def clear_duplicate_autoname(doc, fieldname: str | None = None) -> bool:
	"""Drop copied autoname/id when Duplicate leaves an existing document number."""
	if not doc.is_new() or doc.get("amended_from"):
		return False
	fieldname = fieldname or _autoname_field(doc.doctype)
	if not fieldname:
		return False
	value = doc.get(fieldname)
	if value in (None, ""):
		return False
	if not autoname_value_exists(doc.doctype, value):
		return False
	doc.set(fieldname, None)
	return True


def prepare_new_document_autoname(doc, method=None):
	"""Hook: clear copied ids before insert (Duplicate menu)."""
	clear_duplicate_autoname(doc)


def assign_numeric_id(doc, fieldname: str, *, date_field: str | None = None):
	"""Assign next document number on insert (PREFIX-YYMM-0001 when mapped)."""
	clear_duplicate_autoname(doc, fieldname)
	if doc.get(fieldname):
		return

	if doc.doctype in PREFIX_EXCLUDE:
		return

	date_field = date_field or _guess_date_field(doc)
	doc_date = getdate(doc.get(date_field)) if doc.get(date_field) else getdate()
	prefix = resolve_doctype_prefix(doc)

	if prefix:
		doc.set(
			fieldname,
			get_next_prefixed_no(
				doc.doctype,
				fieldname,
				prefix,
				doc_date,
				location_id=doc.get("location_id"),
			),
		)
		return

	doc.set(fieldname, get_next_numeric_id(doc.doctype, fieldname))


def _guess_date_field(doc) -> str | None:
	for field in _DATE_FIELDS:
		if doc.get(field):
			return field
	return None


def sync_gate_pass_gptype(doc) -> None:
	"""Oracle GatePass.fmb — sync GPTYPE when GatePassNo starts with I or O."""
	gpno = str(doc.get("gatepassno") or "").strip()
	if not gpno:
		return
	first = gpno[0].upper()
	if first == "I":
		doc.gptype = "In"
	elif first == "O":
		doc.gptype = "Out"
