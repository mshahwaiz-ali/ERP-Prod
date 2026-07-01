# Copyright (c) 2026, Millitrix and contributors
# Blueprint — Closing_Transaction.fmx (year-end wizard)

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate

from millitrix.utils.doctype_ids import (
	CLOSING_ADJUSTMENT_ENTRY,
	GL_OPENING,
	STOCK_CLOSING,
	STOCK_OPENING,
)
from millitrix.utils.finance_reports import get_balance_sheet_rows, get_income_statement_rows
from millitrix.utils.gl_reports import get_trial_balance_rows
from millitrix.utils.stock_reports import get_item_stock_rows
from millitrix.utils.voucher_balance import validate_dr_cr_balance


def resolve_capital_account(capital_acc: str | None = None) -> str:
	if capital_acc:
		if not frappe.db.exists("Chart of Accounting", capital_acc):
			frappe.throw(_("Capital account {0} not found").format(capital_acc))
		return capital_acc
	rows = frappe.get_all(
		"Chart of Accounting",
		filters={"nature": "C", "transflag": "Y"},
		fields=["name"],
		order_by="accid",
		limit=1,
	)
	if not rows:
		frappe.throw(_("No transactional capital account found in Chart of Accounting"))
	return rows[0].name


def resolve_year_end_dates(
	closing_date: str,
	*,
	opening_date: str | None = None,
	fy_from_date: str | None = None,
) -> dict[str, str]:
	closing = getdate(closing_date)
	fy_from = getdate(fy_from_date) if fy_from_date else getdate(f"{closing.year}-01-01")
	opening = getdate(opening_date) if opening_date else add_days(closing, 1)
	if opening <= closing:
		frappe.throw(_("Opening date must be after closing date"))
	if fy_from > closing:
		frappe.throw(_("Fiscal year start must be on or before closing date"))
	return {
		"closing_date": str(closing),
		"opening_date": str(opening),
		"fy_from_date": str(fy_from),
	}


def report_filters(location_id: str, fy_from_date: str, closing_date: str) -> dict:
	return {
		"location_id": location_id,
		"from_date": fy_from_date,
		"to_date": closing_date,
	}


def trial_balance_summary(filters: dict) -> dict:
	rows = get_trial_balance_rows(filters)
	total_dr = sum(flt(r.get("closing_debit")) for r in rows)
	total_cr = sum(flt(r.get("closing_credit")) for r in rows)
	return {
		"total_closing_debit": total_dr,
		"total_closing_credit": total_cr,
		"balanced": abs(total_dr - total_cr) <= 0.01,
		"account_count": len(rows),
	}


def build_pnl_closing_voucher_lines(filters: dict, capital_acc: str) -> tuple[list[dict], dict]:
	rows = get_income_statement_rows(filters)
	voucher_lines: list[dict] = []
	total_revenue = 0.0
	total_expense = 0.0

	for row in rows:
		acc = row["accid"]
		nature = row.get("nature")
		dr_close = flt(row.get("closing_debit"))
		cr_close = flt(row.get("closing_credit"))
		if dr_close <= 0 and cr_close <= 0:
			continue
		if dr_close > 0:
			voucher_lines.append(
				{"accid": acc, "debit": 0, "credit": dr_close, "detail": "Year-end close"}
			)
			if nature == "E":
				total_expense += dr_close
		if cr_close > 0:
			voucher_lines.append(
				{"accid": acc, "debit": cr_close, "credit": 0, "detail": "Year-end close"}
			)
			if nature == "R":
				total_revenue += cr_close

	net_profit = total_revenue - total_expense
	if net_profit > 0.01:
		voucher_lines.append(
			{
				"accid": capital_acc,
				"debit": 0,
				"credit": net_profit,
				"detail": "Net profit transfer",
			}
		)
	elif net_profit < -0.01:
		voucher_lines.append(
			{
				"accid": capital_acc,
				"debit": -net_profit,
				"credit": 0,
				"detail": "Net loss transfer",
			}
		)

	if voucher_lines:
		validate_dr_cr_balance(voucher_lines)

	summary = {
		"total_revenue": total_revenue,
		"total_expense": total_expense,
		"net_profit": net_profit,
		"line_count": len(voucher_lines),
	}
	return voucher_lines, summary


def build_gl_opening_lines(filters: dict) -> list[dict]:
	rows = get_balance_sheet_rows(filters)
	lines: list[dict] = []
	for row in rows:
		dr = flt(row.get("closing_debit"))
		cr = flt(row.get("closing_credit"))
		if dr > 0:
			lines.append({"accid": row["accid"], "debit": dr, "credit": 0})
		elif cr > 0:
			lines.append({"accid": row["accid"], "debit": 0, "credit": cr})
	return lines


def project_gl_opening_after_pnl(
	filters: dict,
	net_profit: float,
	capital_acc: str,
) -> list[dict]:
	"""Preview GL opening balances after P&L close (before documents are posted)."""
	lines = build_gl_opening_lines(filters)
	if abs(net_profit) <= 0.01:
		return lines

	for line in lines:
		if line["accid"] == capital_acc:
			if net_profit > 0:
				line["credit"] = flt(line.get("credit")) + net_profit
			else:
				line["debit"] = flt(line.get("debit")) + (-net_profit)
			return lines

	if net_profit > 0:
		lines.append({"accid": capital_acc, "debit": 0, "credit": net_profit})
	else:
		lines.append({"accid": capital_acc, "debit": -net_profit, "credit": 0})
	return lines


def build_stock_roll_forward_lines(location_id: str) -> list[dict]:
	rows = get_item_stock_rows({"location_id": location_id})
	lines: list[dict] = []
	for row in rows:
		qty = flt(row.get("stock_in_hand"))
		if qty == 0:
			continue
		lines.append(
			{
				"storeid": row["storeid"],
				"itemcode": row["itemcode"],
				"bagitemcode": row.get("bagitemcode") or None,
				"partyid": row.get("partyid") or None,
				"bags_are": row.get("bags_are") or None,
				"bagweight": flt(row.get("bagweight")),
				"opening_stock": qty,
				"closing_stock": qty,
				"movingrate": flt(row.get("movingrate")),
			}
		)
	return lines


def stock_opening_lines_from_closing(closing_lines: list[dict]) -> list[dict]:
	return [
		{
			"storeid": line["storeid"],
			"itemcode": line["itemcode"],
			"bagitemcode": line.get("bagitemcode"),
			"partyid": line.get("partyid"),
			"bags_are": line.get("bags_are"),
			"bagweight": line.get("bagweight"),
			"opening_stock": line["closing_stock"],
			"movingrate": line.get("movingrate"),
		}
		for line in closing_lines
	]


def check_existing_year_end(location_id: str, closing_date: str, opening_date: str) -> list[str]:
	warnings: list[str] = []
	marker = f"Year-end closing {closing_date}"
	if frappe.db.exists(
		"Closing and Adjustment Entries",
		{"location_id": location_id, "vouchdate": closing_date, "docstatus": 1, "narration": ["like", f"%{marker}%"]},
	):
		warnings.append(_("P&L closing voucher already exists for {0}").format(closing_date))
	if frappe.db.exists(
		"Closing Stock",
		{"location_id": location_id, "opendate": closing_date, "docstatus": 1},
	):
		warnings.append(_("Closing Stock already exists for {0}").format(closing_date))
	if frappe.db.exists(
		"Opening Stock",
		{"location_id": location_id, "opendate": opening_date, "docstatus": 1},
	):
		warnings.append(_("Opening Stock already exists for {0}").format(opening_date))
	if frappe.db.exists(
		"Accounts Opening",
		{"location_id": location_id, "opening_date": opening_date, "docstatus": 1},
	):
		warnings.append(_("Accounts Opening already exists for {0}").format(opening_date))
	return warnings


def preview_year_end_closing(
	location_id: str,
	closing_date: str,
	*,
	opening_date: str | None = None,
	fy_from_date: str | None = None,
	capital_acc: str | None = None,
) -> dict:
	dates = resolve_year_end_dates(closing_date, opening_date=opening_date, fy_from_date=fy_from_date)
	capital = resolve_capital_account(capital_acc)
	filters = report_filters(location_id, dates["fy_from_date"], dates["closing_date"])

	tb = trial_balance_summary(filters)
	pnl_lines, pnl_summary = build_pnl_closing_voucher_lines(filters, capital)
	stock_lines = build_stock_roll_forward_lines(location_id)
	gl_lines = project_gl_opening_after_pnl(filters, pnl_summary["net_profit"], capital)
	warnings = check_existing_year_end(location_id, dates["closing_date"], dates["opening_date"])

	blockers: list[str] = []
	if not tb["balanced"]:
		blockers.append(
			_("Trial balance is out of balance (Debit {0}, Credit {1})").format(
				tb["total_closing_debit"], tb["total_closing_credit"]
			)
		)
	if pnl_lines and abs(pnl_summary["net_profit"]) <= 0.01 and not pnl_lines:
		pass  # no P&L activity is OK

	return {
		**dates,
		"location_id": location_id,
		"capital_acc": capital,
		"trial_balance": tb,
		"pnl_summary": pnl_summary,
		"pnl_lines": pnl_lines,
		"stock_line_count": len(stock_lines),
		"stock_lines": stock_lines[:50],
		"gl_line_count": len(gl_lines),
		"gl_lines": gl_lines[:50],
		"warnings": warnings,
		"blockers": blockers,
		"can_execute": not blockers and not warnings,
	}


def _create_pnl_closing(
	location_id: str,
	closing_date: str,
	pnl_lines: list[dict],
	*,
	fy_label: str,
) -> dict:
	if not pnl_lines:
		return {"skipped": True, "reason": "No P&L accounts to close"}

	doc = frappe.get_doc(
		{
			"doctype": "Closing and Adjustment Entries",
			"location_id": location_id,
			"vouchertype_id": "1",
			"vouchdate": closing_date,
			"narration": f"Year-end closing {closing_date} ({fy_label})",
			"doctypeid": CLOSING_ADJUSTMENT_ENTRY,
			"posted": "N",
			"details": pnl_lines,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return {"doctype": doc.doctype, "name": doc.name, "voucherno": doc.voucherno}


def _create_stock_closing(location_id: str, closing_date: str, stock_lines: list[dict], *, fy_label: str) -> dict:
	if not stock_lines:
		return {"skipped": True, "reason": "No stock lines"}

	doc = frappe.get_doc(
		{
			"doctype": "Closing Stock",
			"location_id": location_id,
			"opendate": closing_date,
			"remarks": f"Year-end stock closing {closing_date} ({fy_label})",
			"doctypeid": STOCK_CLOSING,
			"posted": "N",
			"details": stock_lines,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return {"doctype": doc.doctype, "name": doc.name, "sopenid": doc.sopenid}


def _create_stock_opening(
	location_id: str,
	opening_date: str,
	opening_lines: list[dict],
	*,
	fy_label: str,
) -> dict:
	if not opening_lines:
		return {"skipped": True, "reason": "No stock lines"}

	doc = frappe.get_doc(
		{
			"doctype": "Opening Stock",
			"location_id": location_id,
			"opendate": opening_date,
			"remarks": f"Year-end stock opening {opening_date} ({fy_label})",
			"doctypeid": STOCK_OPENING,
			"posted": "N",
			"details": opening_lines,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return {"doctype": doc.doctype, "name": doc.name, "sopenid": doc.sopenid}


def _create_gl_opening(location_id: str, opening_date: str, gl_lines: list[dict], *, fy_label: str) -> dict:
	if not gl_lines:
		return {"skipped": True, "reason": "No GL opening lines"}

	doc = frappe.get_doc(
		{
			"doctype": "Accounts Opening",
			"location_id": location_id,
			"opening_date": opening_date,
			"entry_mode": "Account",
			"doctypeid": GL_OPENING,
			"posted": "N",
			"details": gl_lines,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return {"doctype": doc.doctype, "name": doc.name, "glopenid": doc.glopenid}


def _rollback_year_end_created(created: dict) -> None:
	"""Cancel submitted year-end documents in reverse creation order."""
	for key in ("gl_opening", "stock_opening", "stock_closing", "pnl_closing"):
		info = created.get(key) or {}
		if info.get("skipped"):
			continue
		name = info.get("name")
		doctype = info.get("doctype")
		if not name or not doctype or not frappe.db.exists(doctype, name):
			continue
		doc = frappe.get_doc(doctype, name)
		if doc.docstatus == 1:
			doc.cancel()


def execute_year_end_closing(
	location_id: str,
	closing_date: str,
	*,
	opening_date: str | None = None,
	fy_from_date: str | None = None,
	capital_acc: str | None = None,
) -> dict:
	preview = preview_year_end_closing(
		location_id,
		closing_date,
		opening_date=opening_date,
		fy_from_date=fy_from_date,
		capital_acc=capital_acc,
	)
	if preview["blockers"]:
		frappe.throw("; ".join(preview["blockers"]))
	if preview["warnings"]:
		frappe.throw(_("Year-end closing already partially completed: {0}").format("; ".join(preview["warnings"])))

	dates = {
		"closing_date": preview["closing_date"],
		"opening_date": preview["opening_date"],
		"fy_from_date": preview["fy_from_date"],
	}
	capital = preview["capital_acc"]
	filters = report_filters(location_id, dates["fy_from_date"], dates["closing_date"])
	fy_label = f"FY {dates['fy_from_date']} – {dates['closing_date']}"

	created: dict = {}

	try:
		pnl_lines = preview["pnl_lines"]
		created["pnl_closing"] = _create_pnl_closing(
			location_id, dates["closing_date"], pnl_lines, fy_label=fy_label
		)

		gl_lines = build_gl_opening_lines(filters)
		if gl_lines:
			validate_dr_cr_balance(gl_lines)

		stock_lines = build_stock_roll_forward_lines(location_id)
		created["stock_closing"] = _create_stock_closing(
			location_id, dates["closing_date"], stock_lines, fy_label=fy_label
		)

		opening_stock_lines = stock_opening_lines_from_closing(stock_lines)
		created["stock_opening"] = _create_stock_opening(
			location_id, dates["opening_date"], opening_stock_lines, fy_label=fy_label
		)

		created["gl_opening"] = _create_gl_opening(
			location_id, dates["opening_date"], gl_lines, fy_label=fy_label
		)
	except Exception:
		_rollback_year_end_created(created)
		raise

	return {
		**dates,
		"location_id": location_id,
		"capital_acc": capital,
		"created": created,
		"pnl_summary": preview["pnl_summary"],
	}
