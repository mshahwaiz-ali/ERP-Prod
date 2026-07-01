# Copyright (c) 2026, Millitrix and contributors
"""Read Oracle expdp .dmp via strings — dev/UAT seed extraction only."""

from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

from millitrix.utils.mill_setting import SETTING_FIELDS

DEFAULT_DUMP = Path(
	"/home/alishahwaiz/sample/old_client_erp_details/mill_data/backups/ROM_0306263556.dmp"
)

_NATURE_MAP = {
	"A": "Assets",
	"L": "Liabilities",
	"C": "Capital",
	"R": "Revenue",
	"E": "Expenses",
}


def resolve_dump_path(path: str | Path | None = None) -> Path:
	candidate = Path(path) if path else DEFAULT_DUMP
	if not candidate.is_file():
		raise FileNotFoundError(f"Oracle dump not found: {candidate}")
	return candidate


@lru_cache(maxsize=2)
def _strings_lines(path: str) -> tuple[str, ...]:
	raw = subprocess.check_output(
		["strings", "-n", "2", path],
		text=True,
		errors="replace",
	)
	return tuple(raw.splitlines())


def _section_lines(table: str, path: Path) -> list[str]:
	lines = _strings_lines(str(path))
	start = None
	for idx, line in enumerate(lines):
		if line == f'TABLE "{table}"':
			start = idx
			break
	if start is None:
		return []
	out: list[str] = []
	for line in lines[start + 1 : start + 8000]:
		if line.startswith('TABLE "') and line != f'TABLE "{table}"':
			break
		out.append(line)
	return out


def extract_project_para(path: str | Path | None = None) -> dict[str, str]:
	"""DESCRIPTION → PARACODE (Chart of Accounting accid)."""
	dump = resolve_dump_path(path)
	lines = _section_lines("PROJECT_PARA", dump)
	tokens = lines[2:] if len(lines) > 2 else []
	known = set(SETTING_FIELDS) | {"Financial Year", "Custom UI URL"}
	result: dict[str, str] = {}

	for idx, token in enumerate(tokens):
		text = token.strip()
		if text not in known:
			continue
		for nxt in tokens[idx + 1 : idx + 12]:
			candidate = nxt.strip()
			if re.fullmatch(r"\d{4,6}", candidate):
				result[text] = candidate
				break

	# Fallback scan whole dump for any missing keys.
	if len(result) < len(SETTING_FIELDS) - 3:
		all_lines = _strings_lines(str(dump))
		for key in SETTING_FIELDS:
			if key in result:
				continue
			for idx, line in enumerate(all_lines):
				if line.strip() != key:
					continue
				for nxt in all_lines[idx + 1 : idx + 20]:
					if re.fullmatch(r"\d{4,6}", nxt.strip()):
						result[key] = nxt.strip()
						break
				break
	return result


def extract_menu_descriptions(path: str | Path | None = None) -> list[str]:
	dump = resolve_dump_path(path)
	lines = _section_lines("PROJECTMENU", dump)
	if len(lines) <= 2:
		return []
	seen: set[str] = set()
	ordered: list[str] = []
	for token in lines[2:]:
		text = token.strip()
		if not text or len(text) > 50:
			continue
		if text.startswith("CREATE ") or text.startswith("INSERT "):
			continue
		if text in seen:
			continue
		seen.add(text)
		ordered.append(text)
	return ordered


def extract_gl_parameter_accounts(path: str | Path | None = None) -> dict[str, str]:
	return extract_project_para(path)


def minimum_coa_skeleton() -> list[dict]:
	"""Level 1–4 tree + GL Parameter posting accounts (level 5)."""
	rows: list[dict] = [
		{"accid": 1, "description": "Assets", "nature": "Assets", "chartlevel": 1, "parentid": None, "transflag": "No"},
		{"accid": 2, "description": "Liabilities", "nature": "Liabilities", "chartlevel": 1, "parentid": None, "transflag": "No"},
		{"accid": 3, "description": "Capital", "nature": "Capital", "chartlevel": 1, "parentid": None, "transflag": "No"},
		{"accid": 4, "description": "Revenue", "nature": "Revenue", "chartlevel": 1, "parentid": None, "transflag": "No"},
		{"accid": 5, "description": "Expenses", "nature": "Expenses", "chartlevel": 1, "parentid": None, "transflag": "No"},
		{"accid": 11, "description": "Current Assets", "nature": "Assets", "chartlevel": 2, "parentid": 1, "transflag": "No"},
		{"accid": 12, "description": "Fixed Assets", "nature": "Assets", "chartlevel": 2, "parentid": 1, "transflag": "No"},
		{"accid": 21, "description": "Long Term Liabilities", "nature": "Liabilities", "chartlevel": 2, "parentid": 2, "transflag": "No"},
		{"accid": 31, "description": "Direct Expenses", "nature": "Expenses", "chartlevel": 2, "parentid": 5, "transflag": "No"},
		{"accid": 32, "description": "Indirect Expenses", "nature": "Expenses", "chartlevel": 2, "parentid": 5, "transflag": "No"},
		{"accid": 41, "description": "Operating Revenue", "nature": "Revenue", "chartlevel": 2, "parentid": 4, "transflag": "No"},
		{"accid": 33, "description": "Equity", "nature": "Capital", "chartlevel": 2, "parentid": 3, "transflag": "No"},
		{"accid": 331, "description": "Share Capital", "nature": "Capital", "chartlevel": 3, "parentid": 33, "transflag": "No"},
		{"accid": 411, "description": "Sales Revenue", "nature": "Revenue", "chartlevel": 3, "parentid": 41, "transflag": "No"},
		{"accid": 111, "description": "Trade Receivables", "nature": "Assets", "chartlevel": 3, "parentid": 11, "transflag": "No"},
		{"accid": 112, "description": "Cash and Bank", "nature": "Assets", "chartlevel": 3, "parentid": 11, "transflag": "No"},
		{"accid": 113, "description": "Trade Payables", "nature": "Liabilities", "chartlevel": 3, "parentid": 21, "transflag": "No"},
		{"accid": 114, "description": "Trade Purchases", "nature": "Expenses", "chartlevel": 3, "parentid": 31, "transflag": "No"},
		{"accid": 115, "description": "Trade Sales", "nature": "Revenue", "chartlevel": 3, "parentid": 41, "transflag": "No"},
		{"accid": 311, "description": "Direct Expense Detail", "nature": "Expenses", "chartlevel": 3, "parentid": 31, "transflag": "No"},
		{"accid": 321, "description": "Indirect Expense Detail", "nature": "Expenses", "chartlevel": 3, "parentid": 32, "transflag": "No"},
		{"accid": 3311, "description": "Capital Reserves", "nature": "Capital", "chartlevel": 4, "parentid": 331, "transflag": "No"},
		{"accid": 4111, "description": "Income Summary Group", "nature": "Revenue", "chartlevel": 4, "parentid": 411, "transflag": "No"},
		{"accid": 1111, "description": "Receivable Accounts", "nature": "Assets", "chartlevel": 4, "parentid": 111, "transflag": "No"},
		{"accid": 1121, "description": "Cash Accounts", "nature": "Assets", "chartlevel": 4, "parentid": 112, "transflag": "No"},
		{"accid": 1131, "description": "Payable Accounts", "nature": "Liabilities", "chartlevel": 4, "parentid": 113, "transflag": "No"},
		{"accid": 1141, "description": "Purchase Accounts", "nature": "Expenses", "chartlevel": 4, "parentid": 114, "transflag": "No"},
		{"accid": 1151, "description": "Sales Accounts", "nature": "Revenue", "chartlevel": 4, "parentid": 115, "transflag": "No"},
		{"accid": 3111, "description": "Direct Expense Accounts", "nature": "Expenses", "chartlevel": 4, "parentid": 311, "transflag": "No"},
		{"accid": 3211, "description": "Indirect Expense Accounts", "nature": "Expenses", "chartlevel": 4, "parentid": 321, "transflag": "No"},
	]
	return rows


def coa_rows_for_gl_parameter(para: dict[str, str]) -> list[dict]:
	"""Ensure every GL Parameter account exists as level-5 posting account."""
	parent_by_setting = {
		"Trade Purchase": 1141,
		"Trade Sales": 1151,
		"Cash": 1121,
		"Party Brokery": 1111,
		"Brokery Exp": 3111,
		"Receivable Discount": 1111,
		"Payable Discount": 1131,
		"Salary Exp": 3211,
		"Capital": 3311,
		"Income Summary": 4111,
		"Employee": 3211,
	}
	nature_by_label = {
		"Capital": "Capital",
		"Income Summary": "Revenue",
		"Trade Sales": "Revenue",
	}
	rows: list[dict] = []
	for label, accid in sorted(para.items(), key=lambda item: int(item[1])):
		if not re.fullmatch(r"\d{4,6}", str(accid)):
			continue
		parent = parent_by_setting.get(label, 1111)
		rows.append(
			{
				"accid": int(accid),
				"description": label,
				"nature": nature_by_label.get(label, "Expenses" if label.endswith("Exp") else "Assets"),
				"chartlevel": 5,
				"parentid": parent,
				"transflag": "Yes",
			}
		)
	return rows
