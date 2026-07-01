# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.5 — GENERATE_GL

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate

from millitrix.utils.doc_transaction import aggregate_doc_transactions
from millitrix.utils.naming import assign_numeric_id


def delete_voucher_for_document(location_id: str, doctypeid: str, documentid: str) -> None:
	names = frappe.get_all(
		"Voucher Transaction",
		filters={
			"location_id": location_id,
			"doctypeid": doctypeid,
			"documentid": documentid,
		},
		pluck="name",
	)
	for name in names:
		voucher = frappe.get_doc("Voucher Transaction", name)
		if voucher.docstatus == 1:
			voucher.cancel()
		else:
			frappe.delete_doc("Voucher Transaction", name, force=True, ignore_permissions=True)


def generate_gl(
	*,
	location_id: str,
	doctypeid: str,
	documentid: str,
	vouchdate,
	narration: str,
	vouchertype_id: str = "1",
	submit_voucher: bool = True,
) -> str:
	"""Read Document Transaction staging rows and create Voucher Transaction."""
	delete_voucher_for_document(location_id, doctypeid, documentid)

	rows = aggregate_doc_transactions(location_id, doctypeid, str(documentid))
	if not rows:
		frappe.throw(_("No Document Transaction rows to post for document {0}").format(documentid))

	total_dr = sum(flt(r.debit) for r in rows)
	total_cr = sum(flt(r.credit) for r in rows)
	if abs(total_dr - total_cr) > 0.01:
		frappe.throw(
			_("GL out of balance for document {0}: Debit {1}, Credit {2}").format(
				documentid, total_dr, total_cr
			)
		)

	voucher = frappe.new_doc("Voucher Transaction")
	voucher.location_id = location_id
	voucher.vouchertype_id = vouchertype_id
	voucher.vouchdate = getdate(vouchdate)
	voucher.documentid = documentid
	voucher.doctypeid = doctypeid
	voucher.narration = narration
	assign_numeric_id(voucher, "voucherno", date_field="vouchdate")
	from millitrix.utils.field_normalizers import normalize_posted

	voucher.posted = "Draft"

	for row in rows:
		voucher.append(
			"details",
			{
				"accid": row.accid,
				"partyid": row.partyid,
				"itemcode": row.itemcode,
				"empno": row.empno,
				"debit": row.debit,
				"credit": row.credit,
				"detail": row.detail,
				"trans_id": row.trans_id,
				"bnkcash_gl": row.bnkcash_gl,
			},
		)

	voucher.insert(ignore_permissions=True)
	if submit_voucher:
		voucher.submit()
		voucher.db_set("posted", normalize_posted("Submitted"))
		if frappe.get_meta("Voucher Transaction").has_field("posted_by"):
			voucher.db_set("posted_by", frappe.session.user)

	return voucher.name
