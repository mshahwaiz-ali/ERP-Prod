# Copyright (c) 2026, Millitrix and contributors
# Oracle PNRAdvance — advance balance tracking for adjustment knockoff

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.doctype_ids import ADVANCE_PAYMENT, ADVANCE_PNR, ADVANCE_RECEIPT


def _advance_source_tables(flow: str) -> list[str]:
	tables = [ADVANCE_PNR, "Payment and Receipt Voucher"]
	if flow == "payment":
		tables.extend([ADVANCE_PAYMENT])
	elif flow == "receipt":
		tables.extend([ADVANCE_RECEIPT])
	else:
		tables.extend([ADVANCE_PAYMENT, ADVANCE_RECEIPT])
	return tables


def _fetch_advance_rows(
	partyid: str,
	location_id: str,
	*,
	as_of_date: str | None = None,
	flow: str | None = None,
) -> list[dict]:
	"""Read advances from unified Advance PNR + legacy tables."""
	from millitrix.utils.knockoff_flow import resolve_knockoff_flow

	rows: list[dict] = []
	tables = _advance_source_tables(flow) if flow else _advance_source_tables("")

	for table in tables:
		conditions = ["doc.docstatus = 1", "doc.partyid = %(partyid)s", "doc.location_id = %(location_id)s"]
		params: dict = {"partyid": partyid, "location_id": location_id}
		if as_of_date:
			conditions.append("doc.pnrdate <= %(as_of_date)s")
			params["as_of_date"] = as_of_date
		if table == ADVANCE_PNR and flow:
			flow_label = "Payment" if flow == "payment" else "Receipt"
			conditions.append("doc.advance_flow = %(advance_flow)s")
			params["advance_flow"] = flow_label
		if table == "Payment and Receipt Voucher":
			conditions.append("doc.pnr_type = 'Advance'")

		part = frappe.db.sql(
			f"""SELECT doc.pnrno, doc.pnrdate, doc.amount, doc.narration, doc.posted, doc.partyid,
				doc.pnrmode, doc.referno, doc.bankaccid
			FROM `tab{table}` doc
			WHERE {" AND ".join(conditions)}
			ORDER BY doc.pnrdate, doc.pnrno
			""",
			params,
			as_dict=True,
		)
		for row in part:
			row["_source"] = table
			if table == "Payment and Receipt Voucher" and flow:
				try:
					if resolve_knockoff_flow(row.partyid) != flow:
						continue
				except Exception:
					frappe.log_error(
						title=f"Advance PNR flow skip ({row.get('partyid')})",
						message=frappe.get_traceback(),
					)
					continue
			rows.append(row)
	return rows


def get_advance_applied_by_pnr(pnrnos: list[str] | None = None) -> dict[str, float]:
	"""Sum of advance applied per PNR from submitted advance adjustments."""
	conditions = ["aa.docstatus = 1", "ap.pnrno IS NOT NULL"]
	params: dict = {}
	if pnrnos:
		conditions.append("ap.pnrno IN %(pnrnos)s")
		params["pnrnos"] = [str(p) for p in pnrnos]

	out: dict[str, float] = {}
	for parent in ("Advance Adjustment", "Paid Advance Adjustment", "Received Advance Adjustment"):
		rows = frappe.db.sql(
			f"""SELECT ap.pnrno, SUM(COALESCE(ap.amount, 0)) AS applied
			FROM `tabAdjustment PNR` ap
			INNER JOIN `tab{parent}` aa ON aa.name = ap.parent
			WHERE {" AND ".join(conditions)}
			GROUP BY ap.pnrno
			""",
			params,
			as_dict=True,
		)
		for row in rows:
			if row.pnrno:
				pnrno = str(row.pnrno).strip()
				out[pnrno] = out.get(pnrno, 0) + flt(row.applied)
	return out


def get_outstanding_advance_pnr(
	partyid: str,
	location_id: str,
	*,
	as_of_date: str | None = None,
) -> list[dict]:
	"""Outstanding advance PNR balances for advance adjustment picker."""
	try:
		from millitrix.utils.knockoff_flow import resolve_knockoff_flow

		flow = resolve_knockoff_flow(partyid)
	except Exception:
		flow = None

	rows = _fetch_advance_rows(partyid, location_id, as_of_date=as_of_date, flow=flow)
	if not rows:
		return []

	applied = get_advance_applied_by_pnr([str(row.pnrno) for row in rows])
	from millitrix.utils.doctype_ids import ADVANCE_PNR
	from millitrix.utils.party_gl import get_party_accid

	party_accid = get_party_accid(partyid)
	out: list[dict] = []
	for row in rows:
		pnrno = str(row.pnrno).strip()
		docbal = flt(row.amount) - flt(applied.get(pnrno))
		if docbal <= 0.009:
			continue
		source = row.get("_source") or ADVANCE_PNR
		out.append(
			{
				"pnrno": pnrno,
				"pnrdate": row.pnrdate,
				"pnrmode": row.get("pnrmode") or "",
				"referno": row.get("referno") or "",
				"accid": row.get("bankaccid") or party_accid,
				"docbalamnt": round(flt(docbal), 2),
				"amount": round(flt(docbal), 2),
				"applied": flt(row.amount) - docbal,
				"invoice_amount": round(flt(row.amount), 2),
				"narration": row.narration,
				"doctypeid": source,
			}
		)
	return out


def advance_exists(pnrno, *, partyid: str | None = None, location_id: str | None = None) -> bool:
	"""Check advance document across unified Advance PNR and legacy forms."""
	for table in (ADVANCE_PNR, ADVANCE_PAYMENT, ADVANCE_RECEIPT, "Payment and Receipt Voucher"):
		filters = {"pnrno": str(pnrno), "docstatus": 1}
		if partyid:
			filters["partyid"] = partyid
		if location_id:
			filters["location_id"] = location_id
		if table == "Payment and Receipt Voucher":
			filters["pnr_type"] = "Advance"
		if frappe.db.exists(table, filters):
			return True
	return False
