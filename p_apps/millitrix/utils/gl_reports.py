# Copyright (c) 2026, Millitrix and contributors
# GL queries from submitted Voucher Transaction lines.

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate

from millitrix.utils.doctype_ids import MILL_VOUCHER
from millitrix.utils.report_filters import normalize_report_dates


def _voucher_conditions(filters: dict, *, alias: str = "mv", include_dates: bool = True) -> tuple[list[str], dict]:
	conditions = [f"{alias}.docstatus = 1"]
	params: dict = {}

	voucher_range = filters.get("from_voucherno") not in (None, "") or filters.get("to_voucherno") not in (
		None,
		"",
	)
	use_dates = include_dates and not voucher_range

	if use_dates and filters.get("from_date"):
		conditions.append(f"{alias}.vouchdate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if use_dates and filters.get("to_date"):
		conditions.append(f"{alias}.vouchdate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append(f"{alias}.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("from_voucherno") not in (None, ""):
		conditions.append(f"{alias}.voucherno >= %(from_voucherno)s")
		params["from_voucherno"] = str(filters["from_voucherno"]).strip()
	if filters.get("to_voucherno") not in (None, ""):
		conditions.append(f"{alias}.voucherno <= %(to_voucherno)s")
		params["to_voucherno"] = str(filters["to_voucherno"]).strip()

	return conditions, params


def get_voucher_gl_lines(filters: dict | None = None) -> list[dict]:
	filters = normalize_report_dates(filters)
	conditions, params = _voucher_conditions(filters, alias="mv")

	if filters.get("accid"):
		conditions.append("vd.accid = %(accid)s")
		params["accid"] = filters["accid"]
	if filters.get("partyid"):
		conditions.append("vd.partyid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	if filters.get("doctypeid"):
		conditions.append("mv.doctypeid = %(doctypeid)s")
		params["doctypeid"] = filters["doctypeid"]
	if filters.get("documentid") not in (None, ""):
		conditions.append("mv.documentid = %(documentid)s")
		params["documentid"] = str(filters["documentid"]).strip()

	return frappe.db.sql(
		f"""SELECT
			mv.vouchdate,
			mv.voucherno,
			mv.name AS voucher_name,
			mv.vouchertype_id,
			mv.doctypeid,
			mv.documentid,
			mv.narration,
			mv.reference,
			mv.location_id,
			vd.accid,
			coa.description AS account_name,
			coa.nature,
			vd.partyid,
			vd.itemcode,
			vd.empno,
			vd.debit,
			vd.credit,
			vd.detail
		FROM `tabVoucher Transaction` mv
		INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = mv.name
		LEFT JOIN `tabChart of Accounting` coa ON coa.name = vd.accid
		WHERE {" AND ".join(conditions)}
		ORDER BY mv.vouchdate, mv.voucherno, vd.idx
		""",
		params,
		as_dict=True,
	)


def _gl_line_description(line: dict, *, party_names: dict, item_names: dict, employee_names: dict) -> str:
	partyid = line.get("partyid")
	if partyid:
		if partyid not in party_names:
			party_names[partyid] = frappe.db.get_value("Party", partyid, "party_name") or partyid
		return party_names[partyid]
	empno = line.get("empno")
	if empno:
		if empno not in employee_names:
			employee_names[empno] = frappe.db.get_value("Employee Setup", empno, "ename") or str(empno)
		return employee_names[empno]
	itemcode = line.get("itemcode")
	if itemcode:
		if itemcode not in item_names:
			item_names[itemcode] = frappe.db.get_value("Item Setup", itemcode, "itemname") or itemcode
		return item_names[itemcode]
	if line.get("detail"):
		return line["detail"]
	return line.get("account_name") or line.get("accid") or ""


def enrich_voucher_gl_lines(rows: list[dict]) -> list[dict]:
	"""Oracle ViewGLVoucher — party/employee/item/account description on each GL line."""
	party_names: dict[str, str] = {}
	item_names: dict[str, str] = {}
	employee_names: dict[str, str] = {}
	out: list[dict] = []
	for row in rows:
		out.append(
			{
				**row,
				"description": _gl_line_description(
					row,
					party_names=party_names,
					item_names=item_names,
					employee_names=employee_names,
				),
			}
		)
	return out


def aggregate_account_balances(filters: dict, *, before_date: str | None = None) -> dict[str, dict[str, float]]:
	query_filters = dict(filters)
	if before_date:
		query_filters = {**query_filters, "to_date": before_date}
		query_filters.pop("from_date", None)

	lines = get_voucher_gl_lines(query_filters)
	totals: dict[str, dict[str, float]] = {}
	for line in lines:
		acc = line.accid
		bucket = totals.setdefault(acc, {"debit": 0.0, "credit": 0.0})
		bucket["debit"] += flt(line.debit)
		bucket["credit"] += flt(line.credit)
	return totals


def split_balance(net: float) -> tuple[float, float]:
	if net >= 0:
		return flt(net), 0.0
	return 0.0, flt(-net)


def _oracle_nature_group(nature: str | None) -> str:
	"""Oracle COA nature bucket — A (Assets/Expenses) vs E (Liabilities/Capital/Revenue)."""
	if nature in ("Assets", "Expenses"):
		return "A"
	return "E"


def format_balance_side(net: float, nature: str | None) -> str:
	"""Display Dr/Cr label (Oracle Account_Balance.rep RET_BAL formula)."""
	net = flt(net)
	if not net:
		return ""
	group = _oracle_nature_group(nature)
	if group == "A":
		return "Dr" if net > 0 else "Cr"
	return "Cr" if net > 0 else "Dr"


def get_account_ledger_rows(filters: dict | None = None) -> list[dict]:
	return get_voucher_gl_lines(filters)


def get_account_ledger_with_balance_rows(filters: dict | None = None) -> list[dict]:
	"""Account ledger with opening B/F and running balance (Oracle AccLedger.RDF)."""
	filters = normalize_report_dates(filters or {})
	if not filters.get("accid"):
		frappe.throw(_("Account is required"))

	accid = filters["accid"]
	from_date = filters["from_date"]
	opening_end = str(add_days(getdate(from_date), -1))
	opening_totals = aggregate_account_balances(filters, before_date=opening_end)
	open_dr = flt(opening_totals.get(accid, {}).get("debit"))
	open_cr = flt(opening_totals.get(accid, {}).get("credit"))
	opening_net = open_dr - open_cr
	account_name = frappe.db.get_value("Chart of Accounting", accid, "description") or accid

	rows: list[dict] = []
	balance = opening_net
	if opening_net:
		open_debit, opening_credit = split_balance(opening_net)
		rows.append(
			{
				"vouchdate": from_date,
				"voucherno": "",
				"doctypeid": "",
				"documentid": "",
				"accid": accid,
				"account_name": account_name,
				"partyid": "",
				"debit": open_debit,
				"credit": opening_credit,
				"detail": _("Balance B/F"),
				"narration": "",
				"balance": flt(opening_net),
			}
		)

	for line in get_voucher_gl_lines(filters):
		balance += flt(line.debit) - flt(line.credit)
		rows.append({**line, "balance": flt(balance)})
	return rows


def get_trial_balance_rows(filters: dict | None = None) -> list[dict]:
	filters = normalize_report_dates(filters)
	from_date = filters["from_date"]
	opening_end = str(add_days(getdate(from_date), -1))

	opening = aggregate_account_balances(filters, before_date=opening_end)
	period = aggregate_account_balances(filters)
	accounts = sorted(set(opening) | set(period))

	rows: list[dict] = []
	for accid in accounts:
		open_dr = flt(opening.get(accid, {}).get("debit"))
		open_cr = flt(opening.get(accid, {}).get("credit"))
		period_dr = flt(period.get(accid, {}).get("debit"))
		period_cr = flt(period.get(accid, {}).get("credit"))

		open_net = open_dr - open_cr
		close_net = open_net + period_dr - period_cr
		opening_debit, opening_credit = split_balance(open_net)
		closing_debit, closing_credit = split_balance(close_net)

		rows.append(
			{
				"accid": accid,
				"account_name": frappe.db.get_value("Chart of Accounting", accid, "description") or accid,
				"opening_debit": opening_debit,
				"opening_credit": opening_credit,
				"debit": period_dr,
				"credit": period_cr,
				"closing_debit": closing_debit,
				"closing_credit": closing_credit,
			}
		)
	return rows


def get_trial_balance_1_rows(filters: dict | None = None) -> list[dict]:
	"""Location-wise trial balance (Oracle Trial_Balance_1.rep)."""
	from frappe import _

	filters = normalize_report_dates(filters or {})
	if not filters.get("location_id"):
		frappe.throw(_("Location is required for Trial Balance (Location Wise)"))
	rows = get_trial_balance_rows(filters)
	if filters.get("accid"):
		rows = [row for row in rows if row.get("accid") == filters["accid"]]
	location_id = filters["location_id"]
	for row in rows:
		row["location_id"] = location_id
	return rows


def get_voucher_register_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle VoucherRegister.RDF — GL voucher lines with account description and day balance."""
	rows = get_gl_voucher_rows(filters)
	day_balance = 0.0
	current_date = None
	for row in rows:
		vdate = row.get("vouchdate")
		if vdate != current_date:
			day_balance = 0.0
			current_date = vdate
		day_balance += flt(row.get("debit")) - flt(row.get("credit"))
		row["day_balance"] = flt(day_balance, 2)
	return rows


def get_gl_voucher_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle GLVoucher.RDF — all submitted GL voucher lines with enriched descriptions."""
	filters = normalize_report_dates(filters or {})
	lines = enrich_voucher_gl_lines(get_voucher_gl_lines(filters))
	if filters.get("doctypeid"):
		lines = [row for row in lines if row.get("doctypeid") == filters["doctypeid"]]
	if filters.get("vouchertype_id"):
		lines = [row for row in lines if str(row.get("vouchertype_id") or "") == str(filters["vouchertype_id"])]
	lines.sort(
		key=lambda r: (
			r.get("vouchdate") or "",
			str(r.get("vouchertype_id") or ""),
			str(r.get("voucherno") or ""),
			-flt(r.get("debit")),
		)
	)
	return lines


def get_gj_rows(filters: dict | None = None) -> list[dict]:
	"""General journal — manual Voucher Transaction entries (Oracle GJ.RDF)."""
	filters = normalize_report_dates(filters or {})
	filters = {**filters, "doctypeid": MILL_VOUCHER}
	rows = enrich_voucher_gl_lines(get_voucher_gl_lines(filters))
	rows.sort(
		key=lambda r: (
			r.get("vouchdate") or "",
			str(r.get("voucherno") or ""),
			-flt(r.get("debit")),
		)
	)
	return rows


def get_account_balance_rows(filters: dict | None = None) -> list[dict]:
	"""Closing balances per account (Oracle Account_Balance.rep)."""
	filters = normalize_report_dates(filters or {})
	coa_level = filters.get("coa_level")
	rows = get_trial_balance_rows(filters)
	out: list[dict] = []
	for row in rows:
		if coa_level not in (None, ""):
			level = frappe.db.get_value("Chart of Accounting", row["accid"], "chartlevel")
			if level is None or int(level) != int(coa_level):
				continue

		closing_debit = flt(row.get("closing_debit"))
		closing_credit = flt(row.get("closing_credit"))
		if not filters.get("show_zero_values") and not closing_debit and not closing_credit:
			continue

		nature = frappe.db.get_value("Chart of Accounting", row["accid"], "nature")
		balance = flt(closing_debit - closing_credit)
		out.append(
			{
				"accid": row["accid"],
				"account_name": row["account_name"],
				"nature": nature,
				"closing_debit": closing_debit,
				"closing_credit": closing_credit,
				"balance": balance,
				"balance_side": format_balance_side(balance, nature),
			}
		)
	return out


def get_party_ledger_with_balance_rows(filters: dict | None = None) -> list[dict]:
	"""Party GL ledger with opening B/F and running balance (Oracle PartyLedger.RDF)."""
	filters = normalize_report_dates(filters or {})
	if not filters.get("partyid"):
		frappe.throw(_("Party is required for Party Ledger"))

	partyid = filters["partyid"]
	party_name = frappe.db.get_value("Party", partyid, "party_name") or partyid
	from_date = filters["from_date"]
	opening_end = str(add_days(getdate(from_date), -1))
	open_filters = {**filters, "partyid": partyid, "to_date": opening_end}
	open_filters.pop("from_date", None)
	open_lines = get_voucher_gl_lines(open_filters)
	open_dr = sum(flt(line.debit) for line in open_lines)
	open_cr = sum(flt(line.credit) for line in open_lines)
	opening_net = flt(open_dr - open_cr)

	rows: list[dict] = []
	balance = opening_net
	if opening_net:
		open_debit, opening_credit = split_balance(opening_net)
		rows.append(
			{
				"vouchdate": from_date,
				"voucherno": "",
				"doctypeid": "",
				"documentid": "",
				"accid": "",
				"account_name": "",
				"partyid": partyid,
				"party_name": party_name,
				"debit": open_debit,
				"credit": opening_credit,
				"detail": _("Balance B/F"),
				"narration": "",
				"balance": flt(opening_net),
			}
		)

	for line in enrich_voucher_gl_lines(get_voucher_gl_lines(filters)):
		balance += flt(line.debit) - flt(line.credit)
		rows.append({**line, "party_name": party_name, "balance": flt(balance)})
	return rows


def get_party_ledger_rows(filters: dict | None = None) -> list[dict]:
	return get_party_ledger_with_balance_rows(filters)
