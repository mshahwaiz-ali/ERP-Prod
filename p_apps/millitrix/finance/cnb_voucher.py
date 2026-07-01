# Copyright (c) 2026, Millitrix and contributors
# Blueprint — CNBVoucher.fmx / CNBPartyVoucher.fmx

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from millitrix.utils.doc_transaction import DocTranBatch, persist_doc_transactions
from millitrix.utils.child_table_helpers import strip_blank_rows_for_doc
from millitrix.utils.cnb_voucher_mode import is_cnb_receipt, resolve_vouchmode
from millitrix.utils.doctype_ids import CNB_VOUCHER
from millitrix.utils.fiscal import check_posted, validate_fiscal_period
from millitrix.utils.generate_gl import delete_voucher_for_document, generate_gl
from millitrix.utils.mill_setting import get_setting_account
from millitrix.utils.naming import resolve_document_key
from millitrix.utils.party_gl import get_party_accid
from millitrix.utils.stock import mark_posted, mark_unposted


def validate(doc, method=None):
	strip_blank_rows_for_doc(doc)
	check_posted(doc)
	if not doc.doctypeid:
		doc.doctypeid = CNB_VOUCHER
	validate_fiscal_period(doc.vouchdate)
	if not doc.details and not doc.documents:
		frappe.throw(_("Add at least one CNB detail or document line"))
	mode = resolve_vouchmode(doc).upper()
	if mode not in ("R", "RECEIPT", "P", "PAYMENT"):
		frappe.throw(_("Voucher mode must be Receipt (R) or Payment (P)"))

	line_total = sum(flt(line.amount) for line in doc.details or [])
	knockoff_total = sum(flt(line.amount) for line in doc.documents or [])
	combined = line_total + knockoff_total
	doc_total = flt(doc.amount) or combined
	if combined > 0 and abs(combined - doc_total) > 0.01:
		frappe.throw(_("Line total {0} must equal voucher amount {1}").format(combined, doc_total))
	doc.amount = doc_total


def on_submit(doc, method=None):
	doc_key = _voucher_document_id(doc)
	batch = _build_cnb_transactions(doc)
	persist_doc_transactions(batch)
	generate_gl(
		location_id=doc.location_id,
		doctypeid=doc.doctypeid,
		documentid=doc_key,
		vouchdate=doc.vouchdate,
		narration=doc.narration or f"Cash and Bank Voucher {doc.cnbvno}",
	)
	mark_posted(doc)


def on_cancel(doc, method=None):
    # Delegate shared posting cleanup to the unsubmit engine
    from millitrix.finance.unsubmit import on_cancel as unified_cancel
    return unified_cancel(doc, method)
def _resolve_bank_acc(doc) -> str:
	if doc.bankaccid:
		acc = str(doc.bankaccid)
		if frappe.db.exists("Chart of Accounting", acc):
			return acc
	return get_setting_account("Cash")


def _is_receipt(doc) -> bool:
	return is_cnb_receipt(doc)


def _voucher_document_id(doc) -> str:
	for field in ("cnbvno", "empvno"):
		val = getattr(doc, field, None)
		if val not in (None, ""):
			return resolve_document_key(doc, field)
	frappe.throw(_("Voucher number missing"))


def _build_cnb_transactions(doc) -> DocTranBatch:
	batch = DocTranBatch(doc.location_id, doc.doctypeid, _voucher_document_id(doc))
	bank_acc = _resolve_bank_acc(doc)
	receipt = _is_receipt(doc)
	bank_total = flt(doc.amount)

	if receipt:
		batch.dr(bank_acc, bank_total, detail=doc.narration or "CNB Receipt", bnkcash_gl=1)
	else:
		batch.cr(bank_acc, bank_total, detail=doc.narration or "CNB Payment", bnkcash_gl=1)

	for line in doc.details or []:
		amt = flt(line.amount)
		if amt <= 0:
			continue
		if not line.accid:
			frappe.throw(_("Account is missing on CNB detail line"))
		detail = line.detail or f"CNB line {line.accid}"
		if receipt:
			batch.cr(line.accid, amt, detail=detail, trans_id=line.trans_id)
		else:
			batch.dr(line.accid, amt, detail=detail, trans_id=line.trans_id)

	for kn in doc.documents or []:
		amt = flt(kn.amount)
		if amt <= 0:
			continue
		empno = kn.empno
		if empno and frappe.db.exists("Employee Setup", str(empno)):
			from millitrix.utils.employee_gl import get_employee_category_accid

			emp_acc = kn.accid or get_employee_category_accid(empno)
			detail = f"Employee Setup {empno}"
			if receipt:
				batch.cr(emp_acc, amt, detail=detail, trans_id=int(empno))
			else:
				batch.dr(emp_acc, amt, detail=detail, trans_id=int(empno))
			continue
		if not kn.partyid:
			continue
		party_acc = kn.accid or get_party_accid(kn.partyid)
		detail = f"Knockoff {kn.doctypeid} {kn.documentid}"
		if receipt:
			batch.cr(party_acc, amt, partyid=kn.partyid, detail=detail)
		else:
			batch.dr(party_acc, amt, partyid=kn.partyid, detail=detail)

	return batch


def preview_cnb_accounting_lines(doc) -> list[dict]:
	batch = _build_cnb_transactions(doc)
	lines: list[dict] = []
	for row in batch.rows:
		lines.append(
			{
				"accid": row.accid,
				"account": frappe.db.get_value("Chart of Accounting", row.accid, "description")
				or row.accid,
				"debit": round(flt(row.debit), 2),
				"credit": round(flt(row.credit), 2),
				"detail": row.detail or "",
				"partyid": row.partyid,
			}
		)
	return lines


def get_posted_cnb_accounting_lines(doc, *, document_id_field: str) -> list[dict]:
	documentid = resolve_document_key(doc, document_id_field)
	rows = frappe.db.sql(
		"""
		SELECT
			vd.accid,
			COALESCE(coa.description, vd.accid) AS account,
			vd.partyid,
			COALESCE(vd.debit, 0) AS debit,
			COALESCE(vd.credit, 0) AS credit,
			vd.detail
		FROM `tabVoucher Transaction` vt
		INNER JOIN `tabVoucher Transaction Detail` vd ON vd.parent = vt.name
		LEFT JOIN `tabChart of Accounting` coa ON coa.name = vd.accid
		WHERE vt.location_id = %(location_id)s
			AND vt.doctypeid = %(doctypeid)s
			AND vt.documentid = %(documentid)s
			AND vt.docstatus = 1
		ORDER BY vd.idx
		""",
		{
			"location_id": doc.location_id,
			"doctypeid": doc.doctypeid,
			"documentid": documentid,
		},
		as_dict=True,
	)
	return rows
