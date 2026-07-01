# Copyright (c) 2026, Millitrix and contributors
# Blueprint J.2/J.3 — auto In Out Gate Pass from invoice (audit link; stock via invoice submit)

from __future__ import annotations

import frappe
from frappe.utils import flt

from millitrix.utils.doctype_ids import PURCHASE_INVOICE, SALES_INVOICE
from millitrix.utils.field_normalizers import bags_are_label, gate_pass_type_label
from millitrix.utils.naming import assign_numeric_id, resolve_document_key


def ensure_gate_pass_from_invoice(
	doc,
	*,
	gptype: str,
	party_field: str,
	is_purchase: bool,
) -> None:
	"""Create or refresh linked In Out Gate Pass without double stock posting."""
	doctypeid = doc.doctypeid or (PURCHASE_INVOICE if is_purchase else SALES_INVOICE)
	inv_field = "purchinvno" if is_purchase else "salesinvno"
	documentid = resolve_document_key(doc, inv_field)

	existing = frappe.db.get_value(
		"In Out Gate Pass",
		{"documentid": documentid, "doctypeid": doctypeid},
		"name",
	)

	if existing:
		gp = frappe.get_doc("In Out Gate Pass", existing)
		gp.gpdate = doc.invdate
		gp.details = []
	else:
		gp = frappe.new_doc("In Out Gate Pass")
		gp.location_id = doc.location_id
		gp.gptype = gate_pass_type_label(gptype)
		gp.gpdate = doc.invdate
		gp.documentid = documentid
		gp.doctypeid = doctypeid
		gp.kantatype = doc.kantatype
		gp.mundtype = doc.mundtype or frappe.db.get_value("Item Setup", doc.itemcode, "mundtype")
		gp.amount_by = doc.amntby
		assign_numeric_id(gp, "gatepassno", date_field="gpdate")

	gp.partyid = doc.get(party_field)
	gp.brokerid = doc.brokerid
	gp.itemcode = doc.itemcode

	for line in doc.details or []:
		gp.append(
			"details",
			{
				"storeid": line.storeid,
				"bagid": line.bagid,
				"biltyno": line.biltyno,
				"truckno": line.truckno,
				"truckadv": flt(line.truckadv),
				"truckqty": flt(line.truckqty),
				"cartage": flt(line.cartage),
				"bagqty": flt(line.bagqty),
				"bagweight": flt(line.bagweight),
				"total_weight": flt(line.total_weight),
				"bagrate": flt(line.bagrate),
				"bags_are": bags_are_label(line.bags_are, is_purchase=is_purchase),
				"emptybags": getattr(line, "emptybags", None),
				"delikanta": flt(line.delikanta),
				"lessweight": flt(line.lessweight),
				"netweight": flt(line.netweight),
				"rate": flt(line.rate),
				"discount": flt(line.discount),
				"totalamnt": flt(line.totalamnt),
				"labouramnt": flt(line.labouramnt),
				"brokeramnt": flt(line.brokeramnt),
				"transporter": line.transporter,
				"gprefeno": line.gprefeno,
			},
		)

	gp.posted = "Submitted"
	frappe.flags.mill_audit_gate_pass = True
	try:
		if existing:
			gp.save(ignore_permissions=True)
		else:
			gp.insert(ignore_permissions=True)
		if gp.docstatus == 0:
			gp.submit()
	finally:
		frappe.flags.mill_audit_gate_pass = False


def remove_gate_pass_for_invoice(doc, *, is_purchase: bool) -> None:
	"""Delete audit-linked gate pass when invoice is unsubmitted/cancelled."""
	doctypeid = doc.doctypeid or (PURCHASE_INVOICE if is_purchase else SALES_INVOICE)
	inv_field = "purchinvno" if is_purchase else "salesinvno"
	documentid = resolve_document_key(doc, inv_field)

	for name in frappe.get_all(
		"In Out Gate Pass",
		filters={"documentid": documentid, "doctypeid": doctypeid},
		pluck="name",
	):
		gp = frappe.get_doc("In Out Gate Pass", name)
		frappe.flags.mill_audit_gate_pass = True
		try:
			if gp.docstatus == 1:
				gp.cancel()
			elif frappe.db.exists("In Out Gate Pass", name):
				frappe.delete_doc("In Out Gate Pass", name, force=True, ignore_permissions=True)
		finally:
			frappe.flags.mill_audit_gate_pass = False
		if frappe.db.exists("In Out Gate Pass", name):
			frappe.delete_doc("In Out Gate Pass", name, force=True, ignore_permissions=True)
