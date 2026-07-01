# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import re

import frappe
from frappe.utils import getdate

# 12-2606-0001 (category + YYMM + sequence) or legacy 12-0001 / 120001
PARTY_ID_RE = re.compile(r"^(\d+)-(?:(\d{4})-)?(\d{4})$")


def format_party_id(party_category: int | str, sequence: int, *, period: str | None = None) -> str:
	category_no = int(float(str(party_category).strip()))
	if category_no <= 0:
		frappe.throw("Party Category must be a positive number")
	if sequence <= 0 or sequence > 9999:
		frappe.throw(f"Party sequence must be between 1 and 9999 (got {sequence})")
	period = period or getdate().strftime("%y%m")
	return f"{category_no}-{period}-{sequence:04d}"


def parse_party_id(partyid) -> tuple[int, int]:
	"""Return (category_no, sequence) for 12-2606-0001, 12-0001, or legacy 120001."""
	if partyid in (None, ""):
		frappe.throw("Party Number is required")

	raw = str(partyid).strip()
	match = PARTY_ID_RE.match(raw)
	if match:
		return int(match.group(1)), int(match.group(3))

	if raw.isdigit():
		value = int(raw)
		if value <= 0:
			frappe.throw(f"Invalid Party Number {partyid}")
		category_no = value // 10000
		sequence = value % 10000
		if category_no <= 0 or sequence <= 0:
			frappe.throw(
				f"Party Number {partyid} must use {{category}}-{{YYMM}}-{{0001}} format (example: 12-2606-0001)"
			)
		return category_no, sequence

	frappe.throw(
		f"Party Number {partyid} must use {{category}}-{{YYMM}}-{{0001}} format (example: 12-2606-0001)"
	)


def get_next_party_id(party_category: str) -> str:
	"""Party Number = {category}-{YYMM}-{0001}, e.g. 12-2606-0001."""
	if not party_category:
		frappe.throw("Party Category is required to generate Party Number")

	category_no = int(float(str(party_category).strip()))
	period = getdate().strftime("%y%m")
	head = f"{category_no}-{period}-"

	all_rows = frappe.db.sql(
		"""SELECT partyid FROM `tabParty` WHERE pcat_id = %s""",
		(party_category,),
		as_list=True,
	)

	max_seq = 0
	for (partyid,) in all_rows:
		raw = str(partyid).strip()
		if not raw.startswith(head):
			continue
		try:
			max_seq = max(max_seq, int(raw.split("-")[-1]))
		except ValueError:
			continue

	next_seq = max_seq + 1
	if next_seq > 9999:
		frappe.throw(f"Party Number range exhausted for Party Category {category_no}")
	return format_party_id(category_no, next_seq, period=period)


def validate_party_id_for_category(partyid, party_category: str) -> None:
	category_no = int(float(str(party_category).strip()))
	parsed_cat, _seq = parse_party_id(partyid)
	if parsed_cat != category_no:
		frappe.throw(
			f"Party Number {partyid} must start with Party Category {category_no} "
			f"(example: {category_no}-2606-0001)"
		)
