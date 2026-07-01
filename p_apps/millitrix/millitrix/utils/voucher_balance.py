# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch


def _line_amount(row, field: str) -> float:
	if isinstance(row, dict):
		return flt(row.get(field))
	return flt(getattr(row, field, 0))


def validate_dr_cr_balance(details, *, debit_field="debit", credit_field="credit") -> tuple[float, float]:
	total_dr = sum(_line_amount(row, debit_field) for row in details)
	total_cr = sum(_line_amount(row, credit_field) for row in details)
	if abs(total_dr - total_cr) > 0.01:
		frappe.throw(
			_("Voucher out of balance: Debit {0}, Credit {1}").format(total_dr, total_cr)
		)
	return total_dr, total_cr


def batch_from_voucher_details(
	batch: DocTranBatch,
	details,
	*,
	debit_field="debit",
	credit_field="credit",
) -> DocTranBatch:
	for line in details or []:
		dr = flt(getattr(line, debit_field, 0))
		cr = flt(getattr(line, credit_field, 0))
		if dr > 0:
			batch.dr(
				line.accid,
				dr,
				partyid=line.get("partyid") if isinstance(line, dict) else getattr(line, "partyid", None),
				itemcode=line.get("itemcode") if isinstance(line, dict) else getattr(line, "itemcode", None),
				detail=getattr(line, "detail", "") or "",
				trans_id=getattr(line, "trans_id", None),
				bnkcash_gl=getattr(line, "bnkcash_gl", None),
			)
		if cr > 0:
			batch.cr(
				line.accid,
				cr,
				partyid=line.get("partyid") if isinstance(line, dict) else getattr(line, "partyid", None),
				itemcode=line.get("itemcode") if isinstance(line, dict) else getattr(line, "itemcode", None),
				detail=getattr(line, "detail", "") or "",
				trans_id=getattr(line, "trans_id", None),
				bnkcash_gl=getattr(line, "bnkcash_gl", None),
			)
	return batch
