# Copyright (c) 2026, Millitrix and contributors
# Jinja HTML for Millitrix standard print formats — single source of truth.

from __future__ import annotations

PRINT_CSS = """
.mill-print { font-family: Arial, Helvetica, sans-serif; font-size: 11px; color: #111; }
.mill-print h2 { margin: 0 0 8px; font-size: 16px; text-align: center; }
.mill-print .meta { width: 100%; margin-bottom: 10px; }
.mill-print .meta td { padding: 2px 6px; vertical-align: top; }
.mill-print .meta .label { font-weight: bold; width: 130px; }
.mill-print table.lines { width: 100%; border-collapse: collapse; margin-top: 8px; }
.mill-print table.lines th, .mill-print table.lines td { border: 1px solid #999; padding: 4px 5px; }
.mill-print table.lines th { background: #f0f0f0; font-weight: bold; text-align: left; }
.mill-print .text-right { text-align: right; }
.mill-print .totals { margin-top: 10px; width: 100%; }
.mill-print .totals td { padding: 3px 6px; }
.mill-print .footer { margin-top: 16px; font-size: 10px; color: #555; }
"""

PRINT_CSS_PAGE = """
@page { size: A4 portrait; margin: 12mm 10mm; }
@page landscape { size: A4 landscape; margin: 10mm 8mm; }
@media print { .mill-print-full { page: landscape; } }
.mill-print table.lines { table-layout: fixed; font-size: 10px; }
.mill-print table.lines th, .mill-print table.lines td { padding: 3px 4px; word-wrap: break-word; overflow-wrap: anywhere; }
.mill-print table.lines.lines-wide { font-size: 9px; }
.mill-print table.lines.lines-wide th, .mill-print table.lines.lines-wide td { padding: 2px 3px; }
"""

HEADER = """
{% set location_name = (doc.location_id and frappe.db.get_value("Location", doc.location_id, "description")) or "" %}
{% set company_id = (doc.location_id and frappe.db.get_value("Location", doc.location_id, "company_id")) or "" %}
{% set company_name = (company_id and frappe.db.get_value("Mill Information", company_id, "description")) or "" %}
<div class="mill-print">
<h2>{{ title }}</h2>
{% if company_name %}<div style="text-align:center;margin-bottom:6px;"><strong>{{ company_name }}</strong>{% if location_name %} &mdash; {{ location_name }}{% endif %}</div>{% endif %}
"""

FOOTER = """
<div class="footer">Printed on {{ frappe.utils.formatdate(frappe.utils.nowdate()) }} &mdash; {{ doc.doctype }} #{{ doc.name }}</div>
</div>
"""

_EMP_NAME = '{{ frappe.db.get_value("Employee Setup", {"empno": row.empno}, "ename") or row.empno }}'


def _wrap(title: str, body: str) -> str:
	return f"<style>{PRINT_CSS}</style>\n{HEADER.replace('{{ title }}', title)}\n{body}\n{FOOTER}"


def _wrap_paged(title: str, body: str, *, landscape: bool = False) -> str:
	open_tag = '<div class="mill-print mill-print-full">' if landscape else '<div class="mill-print">'
	header = HEADER.replace('{{ title }}', title).replace('<div class="mill-print">', open_tag)
	return f"<style>{PRINT_CSS}{PRINT_CSS_PAGE}</style>\n{header}\n{body}\n{FOOTER}"


def _pi_si_compact_grid(po_field: str) -> str:
	return f"""
<table class="lines">
<thead><tr>
<th>#</th><th>PO/SO</th><th>Bilty</th><th>Store</th><th>Truck</th><th>Bags</th><th>Net Wt</th><th>Mund</th><th>Rate</th><th>Disc</th><th>Amount</th><th>Broker</th><th>Labour</th>
</tr></thead>
<tbody>
{{% for row in doc.details %}}
<tr>
<td>{{{{ row.idx }}}}</td><td>{{{{ row.{po_field} or "" }}}}</td><td>{{{{ row.biltyno or "" }}}}</td>
<td>{{{{ row.storeid }}}}</td><td>{{{{ row.truckno or "" }}}}</td><td class="text-right">{{{{ row.bagqty or "" }}}}</td>
<td class="text-right">{{{{ row.get_formatted("netweight", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("mund", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("rate", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("discount", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("totalamnt", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("brokeramnt", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("labouramnt", doc) }}}}</td>
</tr>
{{% endfor %}}
</tbody>
</table>
"""


def _pi_si_full_grid(po_field: str) -> str:
	return f"""
<table class="lines">
<thead><tr>
<th>#</th><th>PO/SO</th><th>Bilty</th><th>Truck</th><th>Store</th><th>Bags</th><th>Net Wt</th><th>Mund</th><th>Rate</th><th>Disc</th><th>Amount</th><th>Broker</th><th>Labour</th><th>Cartage</th><th>Truck Adv</th><th>Transporter</th><th>Bag Amt</th>
</tr></thead>
<tbody>
{{% for row in doc.details %}}
<tr>
<td>{{{{ row.idx }}}}</td><td>{{{{ row.{po_field} or "" }}}}</td><td>{{{{ row.biltyno or "" }}}}</td>
<td>{{{{ row.truckno or "" }}}}</td><td>{{{{ row.storeid }}}}</td><td class="text-right">{{{{ row.bagqty or "" }}}}</td>
<td class="text-right">{{{{ row.get_formatted("netweight", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("mund", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("rate", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("discount", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("totalamnt", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("brokeramnt", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("labouramnt", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("cartage", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("truckadv", doc) }}}}</td>
<td>{{{{ row.transporter or "" }}}}</td>
<td class="text-right">{{{{ row.get_formatted("bagamnt", doc) }}}}</td>
</tr>
{{% endfor %}}
</tbody>
</table>
"""


def purchase_invoice_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Invoice No</td><td>{{ doc.purchinvno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("invdate") }}</td></tr>
<tr><td class="label">Supplier</td><td colspan="3">{{ frappe.db.get_value("Party", doc.supplierid, "party_name") or doc.supplierid }}</td></tr>
<tr><td class="label">Broker</td><td>{{ frappe.db.get_value("Party", doc.brokerid, "party_name") or doc.brokerid }}</td><td class="label">Item</td><td>{{ doc.itemcode }}</td></tr>
<tr><td class="label">Amount By</td><td>{{ doc.amntby }}</td><td class="label">Kanta Type</td><td>{{ doc.kantatype }}</td></tr>
</table>
""" + _pi_si_compact_grid("ponumber") + """
<table class="totals">
<tr><td class="label text-right" style="width:80%;">Amount</td><td class="text-right">{{ doc.get_formatted("amount") }}</td></tr>
<tr><td class="label text-right">Payable</td><td class="text-right">{{ doc.get_formatted("payable") }}</td></tr>
</table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Purchase Invoice", body)


def purchase_invoice_full_detail_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Invoice No</td><td>{{ doc.purchinvno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("invdate") }}</td></tr>
<tr><td class="label">Supplier</td><td colspan="3">{{ frappe.db.get_value("Party", doc.supplierid, "party_name") or doc.supplierid }}</td></tr>
<tr><td class="label">Broker</td><td>{{ frappe.db.get_value("Party", doc.brokerid, "party_name") or doc.brokerid }}</td><td class="label">Item</td><td>{{ doc.itemcode }}</td></tr>
<tr><td class="label">Amount By</td><td>{{ doc.amntby }}</td><td class="label">Kanta Type</td><td>{{ doc.kantatype }}</td></tr>
<tr><td class="label">Brokery</td><td>{{ doc.brokery }}</td><td class="label">Borrow</td><td>{{ doc.borrow or "" }}</td></tr>
</table>
""" + _pi_si_full_grid("ponumber") + """
<table class="totals">
<tr><td class="label text-right" style="width:80%;">Amount</td><td class="text-right">{{ doc.get_formatted("amount") }}</td></tr>
<tr><td class="label text-right">Payable</td><td class="text-right">{{ doc.get_formatted("payable") }}</td></tr>
</table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Purchase Invoice — Full Detail", body)


def sales_invoice_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Invoice No</td><td>{{ doc.salesinvno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("invdate") }}</td></tr>
<tr><td class="label">Customer</td><td colspan="3">{{ frappe.db.get_value("Party", doc.customerid, "party_name") or doc.customerid }}</td></tr>
<tr><td class="label">Broker</td><td>{{ frappe.db.get_value("Party", doc.brokerid, "party_name") or doc.brokerid }}</td><td class="label">Item</td><td>{{ doc.itemcode }}</td></tr>
<tr><td class="label">Amount By</td><td>{{ doc.amntby }}</td><td class="label">Kanta Type</td><td>{{ doc.kantatype }}</td></tr>
</table>
""" + _pi_si_compact_grid("sonumber") + """
<table class="totals">
<tr><td class="label text-right" style="width:80%;">Amount</td><td class="text-right">{{ doc.get_formatted("amount") }}</td></tr>
<tr><td class="label text-right">Receivable</td><td class="text-right">{{ doc.get_formatted("receivable") }}</td></tr>
</table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Sales Invoice", body)


def sales_invoice_full_detail_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Invoice No</td><td>{{ doc.salesinvno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("invdate") }}</td></tr>
<tr><td class="label">Customer</td><td colspan="3">{{ frappe.db.get_value("Party", doc.customerid, "party_name") or doc.customerid }}</td></tr>
<tr><td class="label">Broker</td><td>{{ frappe.db.get_value("Party", doc.brokerid, "party_name") or doc.brokerid }}</td><td class="label">Item</td><td>{{ doc.itemcode }}</td></tr>
<tr><td class="label">Amount By</td><td>{{ doc.amntby }}</td><td class="label">Kanta Type</td><td>{{ doc.kantatype }}</td></tr>
<tr><td class="label">Brokery</td><td>{{ doc.brokery }}</td><td class="label">Borrow</td><td>{{ doc.borrow or "" }}</td></tr>
</table>
""" + _pi_si_full_grid("sonumber") + """
<table class="totals">
<tr><td class="label text-right" style="width:80%;">Amount</td><td class="text-right">{{ doc.get_formatted("amount") }}</td></tr>
<tr><td class="label text-right">Receivable</td><td class="text-right">{{ doc.get_formatted("receivable") }}</td></tr>
</table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Sales Invoice — Full Detail", body)


def gate_pass_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Gate Pass No</td><td>{{ doc.gatepassno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("gpdate") }}</td></tr>
<tr><td class="label">Type</td><td>{{ doc.gptype }}</td><td class="label">Item</td><td>{{ doc.itemcode }}</td></tr>
<tr><td class="label">Party</td><td>{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td><td class="label">Broker</td><td>{{ frappe.db.get_value("Party", doc.brokerid, "party_name") or doc.brokerid or "" }}</td></tr>
</table>
<table class="lines">
<thead><tr>
<th>#</th><th>Bilty</th><th>Truck</th><th>Store</th><th>Net Weight</th><th>Rate</th><th>Bags</th>
</tr></thead>
<tbody>
{% for row in doc.details %}
<tr>
<td>{{ row.idx }}</td><td>{{ row.biltyno or "" }}</td><td>{{ row.truckno or "" }}</td><td>{{ row.storeid }}</td>
<td class="text-right">{{ row.get_formatted("netweight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("rate", doc) }}</td>
<td class="text-right">{{ row.bagqty or "" }}</td>
</tr>
{% endfor %}
</tbody>
</table>
"""
	return _wrap("Gate Pass", body)


def gate_pass_full_detail_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Gate Pass No</td><td>{{ doc.gatepassno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("gpdate") }}</td></tr>
<tr><td class="label">Type</td><td>{{ doc.gptype }}</td><td class="label">Item</td><td>{{ doc.itemcode }}</td></tr>
<tr><td class="label">Party</td><td>{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td><td class="label">Broker</td><td>{{ frappe.db.get_value("Party", doc.brokerid, "party_name") or doc.brokerid or "" }}</td></tr>
</table>
<table class="lines">
<thead><tr>
<th>#</th><th>Bilty</th><th>Truck</th><th>Truck Qty</th><th>Store</th><th>Empty Bags</th><th>Bag Item</th><th>Bags</th><th>Bags Are</th><th>Bag Wt</th><th>Total Wt</th><th>Net Wt</th><th>Rate</th>
</tr></thead>
<tbody>
{% for row in doc.details %}
<tr>
<td>{{ row.idx }}</td><td>{{ row.biltyno or "" }}</td><td>{{ row.truckno or "" }}</td>
<td class="text-right">{{ row.get_formatted("truckqty", doc) }}</td><td>{{ row.storeid }}</td>
<td>{{ row.emptybags or "" }}</td><td>{{ row.bagid or "" }}</td><td class="text-right">{{ row.bagqty or "" }}</td>
<td>{{ row.bags_are or "" }}</td>
<td class="text-right">{{ row.get_formatted("bagweight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("total_weight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("netweight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("rate", doc) }}</td>
</tr>
{% endfor %}
</tbody>
</table>
"""
	return _wrap("Gate Pass — Full Detail", body)


def purchase_order_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">PO No</td><td>{{ doc.ponumber }}</td><td class="label">Date</td><td>{{ doc.get_formatted("podate") }}</td></tr>
<tr><td class="label">Supplier</td><td colspan="3">{{ frappe.db.get_value("Party", doc.supplierid, "party_name") or doc.supplierid }}</td></tr>
<tr><td class="label">Item</td><td>{{ doc.itemcode }}</td><td class="label">Status</td><td>{{ doc.status }}</td></tr>
<tr><td class="label">Truck Qty</td><td>{{ doc.truckqty }}</td><td class="label">Rate</td><td>{{ doc.get_formatted("rate") }}</td></tr>
<tr><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td><td class="label">Payable</td><td>{{ doc.get_formatted("payable") }}</td></tr>
</table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Purchase Order", body)


def sales_order_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">SO No</td><td>{{ doc.sonumber }}</td><td class="label">Date</td><td>{{ doc.get_formatted("sodate") }}</td></tr>
<tr><td class="label">Customer</td><td colspan="3">{{ frappe.db.get_value("Party", doc.customerid, "party_name") or doc.customerid }}</td></tr>
<tr><td class="label">Item</td><td>{{ doc.itemcode }}</td><td class="label">Status</td><td>{{ doc.status }}</td></tr>
<tr><td class="label">Truck Qty</td><td>{{ doc.truckqty }}</td><td class="label">Rate</td><td>{{ doc.get_formatted("rate") }}</td></tr>
<tr><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td><td class="label">Receivable</td><td>{{ doc.get_formatted("receivable") }}</td></tr>
</table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Sales Order", body)


def pnr_voucher_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">PNR No</td><td>{{ doc.pnrno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("pnrdate") }}</td></tr>
<tr><td class="label">Party</td><td colspan="3">{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td></tr>
<tr><td class="label">PNR Type</td><td>{{ doc.pnr_type or doc.doctypeid or "" }}</td><td class="label">Mode</td><td>{{ doc.pnrmode or "" }}</td></tr>
<tr><td class="label">Bank</td><td>{{ doc.bankaccid or "" }}</td><td class="label">Reference</td><td>{{ doc.referno or "" }}</td></tr>
<tr><td class="label">Amount</td><td>{{ doc.get_formatted("amount") if doc.amount else "" }}</td><td class="label">Balance</td><td>{{ doc.get_formatted("balance") if doc.balance else "" }}</td></tr>
</table>
{% if doc.instruments %}
<h4>Instruments</h4>
<table class="lines"><thead><tr><th>#</th><th>Bank Account</th><th>Mode</th><th>Reference</th><th>Amount</th></tr></thead>
<tbody>{% for row in doc.instruments %}
<tr><td>{{ row.idx }}</td><td>{{ row.bankaccid or "" }}</td><td>{{ row.pnrmode or "" }}</td><td>{{ row.referno or "" }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.documents %}
<h4>Documents</h4>
<table class="lines"><thead><tr><th>#</th><th>Document ID</th><th>Party</th><th>Doc Balance</th><th>Amount</th><th>Balance</th></tr></thead>
<tbody>{% for row in doc.documents %}
<tr><td>{{ row.idx }}</td><td>{{ row.documentid }}</td><td>{{ row.party_name or row.partyid or "" }}</td>
<td class="text-right">{{ row.get_formatted("docbalamnt", doc) }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td>
<td class="text-right">{{ row.get_formatted("balance", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""
	return _wrap("{{ doc.doctype }}", body)


def advance_pnr_voucher_body() -> str:
	return """
<table class="meta">
<tr><td class="label">Document Id</td><td>{{ doc.pnrno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("pnrdate") }}</td></tr>
<tr><td class="label">Party</td><td colspan="3">{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td></tr>
<tr><td class="label">Mode</td><td>{{ doc.pnrmode or "" }}</td><td class="label">Reference</td><td>{{ doc.referno or "" }}</td></tr>
<tr><td class="label">Bank</td><td>{{ doc.bankaccid or "" }}</td><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td></tr>
</table>
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""


def advance_payment_voucher_html() -> str:
	return _wrap("Advance Payment", advance_pnr_voucher_body())


def advance_receipt_voucher_html() -> str:
	return _wrap("Advance Receipt", advance_pnr_voucher_body())


def advance_pnr_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Document Id</td><td>{{ doc.pnrno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("pnrdate") }}</td></tr>
<tr><td class="label">Type</td><td>{{ doc.advance_flow }}</td><td class="label">Mode</td><td>{{ doc.pnrmode or "" }}</td></tr>
<tr><td class="label">Party</td><td colspan="3">{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td></tr>
<tr><td class="label">Bank</td><td>{{ doc.bankaccid or "" }}</td><td class="label">Reference</td><td>{{ doc.referno or "" }}</td></tr>
<tr><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td><td class="label">Balance</td><td>{{ doc.get_formatted("balance") }}</td></tr>
</table>
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""
	title = '{% if doc.advance_flow == "Receipt" %}Advance Receipt Voucher{% else %}Advance Payment Voucher{% endif %}'
	return f"<style>{PRINT_CSS}</style>\n{HEADER.replace('{{ title }}', title)}\n{body}\n{FOOTER}"


def cnb_voucher_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Voucher No</td><td>{{ doc.cnbvno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("vouchdate") }}</td></tr>
<tr><td class="label">Mode</td><td>{{ doc.vouchmode or doc.paymode or "" }}</td><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td></tr>
<tr><td class="label">Bank</td><td>{{ doc.bankaccid or "" }}</td><td class="label">Reference</td><td>{{ doc.referno or "" }}</td></tr>
</table>
{% if doc.details %}
<h4>Details</h4>
<table class="lines"><thead><tr><th>#</th><th>Account</th><th>Amount</th><th>Detail</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.accid or "" }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td><td>{{ row.detail or "" }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.documents %}
<h4>Documents</h4>
<table class="lines"><thead><tr><th>#</th><th>Party</th><th>Document ID</th><th>Amount</th></tr></thead>
<tbody>{% for row in doc.documents %}
<tr><td>{{ row.idx }}</td><td>{{ frappe.db.get_value("Party", row.partyid, "party_name") or row.partyid or row.empno or "" }}</td><td>{{ row.documentid }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""
	return _wrap("{{ doc.doctype }}", body)


def expense_voucher_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Voucher No</td><td>{{ doc.cnbvno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("vouchdate") }}</td></tr>
<tr><td class="label">Mode</td><td>{{ doc.paymode or "" }}</td><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td></tr>
<tr><td class="label">Bank</td><td>{{ doc.bankaccid or "" }}</td><td class="label">Reference</td><td>{{ doc.referno or "" }}</td></tr>
</table>
{% if doc.details %}
<h4>Expense Details</h4>
<table class="lines"><thead><tr><th>#</th><th>Trans Id</th><th>Amount</th><th>Detail</th><th>Mill Id</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.trans_id or "" }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td><td>{{ row.detail or "" }}</td><td>{{ row.mill_id or "" }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""
	return _wrap("Expense Voucher", body)


def party_cnb_voucher_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Voucher No</td><td>{{ doc.cnbvno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("vouchdate") }}</td></tr>
<tr><td class="label">Party</td><td colspan="3">{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td></tr>
<tr><td class="label">Mode</td><td>{{ doc.paymode or "" }}</td><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td></tr>
<tr><td class="label">Bank</td><td>{{ doc.bankaccid or "" }}</td><td class="label">Reference</td><td>{{ doc.referno or "" }}</td></tr>
</table>
{% if doc.documents %}
<h4>Documents</h4>
<table class="lines"><thead><tr><th>#</th><th>Document ID</th><th>Party</th><th>Amount</th><th>Balance</th></tr></thead>
<tbody>{% for row in doc.documents %}
<tr><td>{{ row.idx }}</td><td>{{ row.documentid }}</td><td>{{ row.partyid or "" }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td><td class="text-right">{{ row.get_formatted("balance", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""
	return _wrap("{{ doc.doctype }}", body)


def mill_voucher_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Voucher No</td><td>{{ doc.voucherno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("vouchdate") }}</td></tr>
<tr><td class="label">Voucher Type</td><td>{{ doc.vouchertype_id }}</td><td class="label">Reference</td><td>{{ doc.reference or "" }}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>Account</th><th>Party</th><th>Debit</th><th>Credit</th><th>Detail</th></tr></thead>
<tbody>
{% for row in doc.details %}
<tr>
<td>{{ row.idx }}</td><td>{{ row.accid }}</td><td>{{ row.partyid or "" }}</td>
<td class="text-right">{{ row.get_formatted("debit", doc) }}</td>
<td class="text-right">{{ row.get_formatted("credit", doc) }}</td>
<td>{{ row.detail or "" }}</td>
</tr>
{% endfor %}
</tbody>
</table>
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""
	return _wrap("Journal Voucher", body)


def employee_payslip_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Pay Slip No</td><td>{{ doc.pslipid }}</td><td class="label">Pay Date</td><td>{{ doc.get_formatted("pdate") }}</td></tr>
<tr><td class="label">Pay Month</td><td colspan="3">{{ doc.paymonth }}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>Employee</th><th>Amount</th><th>Balance</th></tr></thead>
<tbody>
{% for row in doc.employees %}
<tr>
<td>{{ row.idx }}</td>
<td>{{ frappe.db.get_value("Employee Setup", {"empno": row.empno}, "ename") or row.empno }}</td>
<td class="text-right">{{ row.get_formatted("amount", doc) }}</td>
<td class="text-right">{{ row.get_formatted("balance", doc) }}</td>
</tr>
{% endfor %}
</tbody>
</table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Employee Pay Slip", body)


def _return_compact_grid() -> str:
	return """
<table class="lines">
<thead><tr><th>#</th><th>Store</th><th>Truck</th><th>Bilty</th><th>Net Weight</th><th>Rate</th><th>Amount</th><th>Bags</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.storeid }}</td><td>{{ row.truckno or "" }}</td><td>{{ row.biltyno or "" }}</td>
<td class="text-right">{{ row.get_formatted("netweight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("rate", doc) }}</td>
<td class="text-right">{{ row.get_formatted("totalamnt", doc) }}</td>
<td class="text-right">{{ row.bagqty or "" }}</td></tr>
{% endfor %}</tbody></table>
"""


def purchase_return_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Return No</td><td>{{ doc.purchretno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("retdate") }}</td></tr>
<tr><td class="label">Purchase Invoice</td><td>{{ frappe.db.get_value("Purchase Invoice", doc.purchinvno, "purchinvno") or doc.purchinvno }}</td><td class="label">Supplier</td><td>{{ frappe.db.get_value("Party", frappe.db.get_value("Purchase Invoice", doc.purchinvno, "supplierid"), "party_name") or "" }}</td></tr>
<tr><td class="label">Amount By</td><td>{{ doc.amntby }}</td><td class="label">Kanta Type</td><td>{{ doc.kantatype }}</td></tr>
</table>
""" + _return_compact_grid() + """
<table class="totals">
<tr><td class="label text-right" style="width:80%;">Amount</td><td class="text-right">{{ doc.get_formatted("amount") }}</td></tr>
<tr><td class="label text-right">Receivable</td><td class="text-right">{{ doc.get_formatted("receivable") }}</td></tr>
</table>
"""
	return _wrap("Purchase Return", body)


def sales_return_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Return No</td><td>{{ doc.salesretno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("retdate") }}</td></tr>
<tr><td class="label">Sales Invoice</td><td>{{ frappe.db.get_value("Sales Invoice", doc.salesinvno, "salesinvno") or doc.salesinvno }}</td><td class="label">Customer</td><td>{{ frappe.db.get_value("Party", frappe.db.get_value("Sales Invoice", doc.salesinvno, "customerid"), "party_name") or "" }}</td></tr>
<tr><td class="label">Amount By</td><td>{{ doc.amntby }}</td><td class="label">Kanta Type</td><td>{{ doc.kantatype }}</td></tr>
</table>
""" + _return_compact_grid() + """
<table class="totals">
<tr><td class="label text-right" style="width:80%;">Amount</td><td class="text-right">{{ doc.get_formatted("amount") }}</td></tr>
<tr><td class="label text-right">Payable</td><td class="text-right">{{ doc.get_formatted("payable") }}</td></tr>
</table>
"""
	return _wrap("Sales Return", body)


def stock_transfer_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Transfer No</td><td>{{ doc.transferno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("tdate") }}</td></tr>
<tr><td class="label">From Store</td><td>{{ doc.fromstoreid }}</td><td class="label">Item</td><td>{{ doc.itemcode }}</td></tr>
<tr><td class="label">Party</td><td>{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid or "" }}</td><td class="label">Kanta Type</td><td>{{ doc.kantatype or "" }}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>To Store</th><th>Truck</th><th>Net Weight</th><th>Rate</th><th>Bags</th><th>Transporter</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.tostoreid }}</td><td>{{ row.truckno or "" }}</td>
<td class="text-right">{{ row.get_formatted("netweight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("rate", doc) }}</td>
<td class="text-right">{{ row.bagqty or "" }}</td><td>{{ row.transporter or "" }}</td></tr>
{% endfor %}</tbody></table>
"""
	return _wrap("Stock Transfer", body)


def stock_transfer_full_detail_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Transfer No</td><td>{{ doc.transferno }}</td><td class="label">Date</td><td>{{ doc.get_formatted("tdate") }}</td></tr>
<tr><td class="label">From Store</td><td>{{ doc.fromstoreid }}</td><td class="label">Item</td><td>{{ doc.itemcode }}</td></tr>
<tr><td class="label">Party</td><td>{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid or "" }}</td><td class="label">Kanta Type</td><td>{{ doc.kantatype or "" }}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>Truck</th><th>Truck Qty</th><th>Cartage</th><th>To Store</th><th>Empty Bags</th><th>Bag Item</th><th>Bags</th><th>Bag Wt</th><th>Total Wt</th><th>Deli Kanta</th><th>Net Wt</th><th>Rate</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.truckno or "" }}</td>
<td class="text-right">{{ row.get_formatted("truckqty", doc) }}</td>
<td class="text-right">{{ row.get_formatted("cartage", doc) }}</td>
<td>{{ row.tostoreid }}</td><td>{{ row.emptybags or "" }}</td><td>{{ row.bagid or "" }}</td>
<td class="text-right">{{ row.bagqty or "" }}</td>
<td class="text-right">{{ row.get_formatted("bagweight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("total_weight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("delikanta", doc) }}</td>
<td class="text-right">{{ row.get_formatted("netweight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("rate", doc) }}</td></tr>
{% endfor %}</tbody></table>
"""
	return _wrap("Stock Transfer — Full Detail", body)


def advance_adjustment_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Adjustment No</td><td>{{ doc.adjid }}</td><td class="label">Date</td><td>{{ doc.get_formatted("adjdate") }}</td></tr>
<tr><td class="label">Party</td><td colspan="3">{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td></tr>
<tr><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td><td class="label">Type</td><td>{{ doc.doctypeid }}</td></tr>
</table>
{% if doc.pnr_lines %}
<h4>PNR Lines</h4>
<table class="lines"><thead><tr><th>#</th><th>PNR No</th><th>Amount</th></tr></thead>
<tbody>{% for row in doc.pnr_lines %}
<tr><td>{{ row.idx }}</td><td>{{ row.pnrno }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.invoice_lines %}
<h4>Invoice Lines</h4>
<table class="lines"><thead><tr><th>#</th><th>Doc Type</th><th>Document ID</th><th>Amount</th></tr></thead>
<tbody>{% for row in doc.invoice_lines %}
<tr><td>{{ row.idx }}</td><td>{{ row.doctypeid }}</td><td>{{ row.documentid }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""
	return _wrap("Advance Adjustment", body)


def party_gross_margin_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">PGM No</td><td>{{ doc.pgmid }}</td><td class="label">Date</td><td>{{ doc.get_formatted("pgdate") }}</td></tr>
<tr><td class="label">Party</td><td>{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid or "" }}</td><td class="label">Item</td><td>{{ doc.itemcode or "" }}</td></tr>
<tr><td class="label">Account</td><td>{{ doc.accid }}</td><td class="label">Mode</td><td>{{ doc.pgmode }}</td></tr>
<tr><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td><td class="label">Reference</td><td>{{ doc.referno or "" }}</td></tr>
</table>
{% if doc.party_b_lines %}
<h4>Party B Lines</h4>
<table class="lines"><thead><tr><th>#</th><th>Party</th><th>Account</th><th>Mode</th><th>Amount</th></tr></thead>
<tbody>{% for row in doc.party_b_lines %}
<tr><td>{{ row.idx }}</td><td>{{ row.partyid or "" }}</td><td>{{ row.accid }}</td><td>{{ row.pgmode }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.invoices %}
<h4>Invoices</h4>
<table class="lines"><thead><tr><th>#</th><th>Doc Type</th><th>Document ID</th><th>Doc Balance</th><th>Amount</th></tr></thead>
<tbody>{% for row in doc.invoices %}
<tr><td>{{ row.idx }}</td><td>{{ row.doctypeid }}</td><td>{{ row.documentid }}</td><td class="text-right">{{ row.get_formatted("docbalamnt", doc) }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""
	return _wrap("Party Gross Margin", body)


def _employee_voucher_body(label_mode: str) -> str:
	return f"""
<table class="meta">
<tr><td class="label">Voucher No</td><td>{{{{ doc.empvno }}}}</td><td class="label">Date</td><td>{{{{ doc.get_formatted("vouchdate") }}}}</td></tr>
<tr><td class="label">{label_mode}</td><td>{{{{ doc.paymode or doc.vouchmode }}}}</td><td class="label">Amount</td><td>{{{{ doc.get_formatted("amount") }}}}</td></tr>
<tr><td class="label">Bank</td><td>{{{{ doc.bankaccid or "" }}}}</td><td class="label">Reference</td><td>{{{{ doc.referno or "" }}}}</td></tr>
</table>
{{% if doc.documents %}}
<h4>Employees</h4>
<table class="lines"><thead><tr><th>#</th><th>Emp No.</th><th>Employee Name</th><th>Amount</th></tr></thead>
<tbody>{{% for row in doc.documents %}}
<tr><td>{{{{ row.idx }}}}</td><td>{{{{ row.empno or "" }}}}</td><td>{_EMP_NAME}</td><td class="text-right">{{{{ row.get_formatted("amount", doc) }}}}</td></tr>
{{% endfor %}}</tbody></table>
{{% endif %}}
{{% if doc.narration %}}<p><strong>Narration:</strong> {{{{ doc.narration }}}}</p>{{% endif %}}
"""


def employee_payment_voucher_html() -> str:
	return _wrap("Employee Payment Voucher", _employee_voucher_body("Payment Mode"))


def employee_receipt_voucher_html() -> str:
	return _wrap("Employee Receipt Voucher", _employee_voucher_body("Receipt Mode"))


def opening_stock_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Closing No</td><td>{{ doc.sopenid }}</td><td class="label">Date</td><td>{{ doc.get_formatted("opendate") }}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>Store</th><th>Item</th><th>Filled Item</th><th>Party</th><th>Stock Qty</th><th>Avg Rate</th><th>Stock Value</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.storeid }}</td><td>{{ row.itemcode }}</td><td>{{ row.bagitemcode or "" }}</td>
<td>{{ row.partyid or "" }}</td>
<td class="text-right">{{ row.get_formatted("opening_stock", doc) }}</td>
<td class="text-right">{{ row.get_formatted("movingrate", doc) }}</td>
<td class="text-right">{{ row.get_formatted("stock_value", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Opening Stock", body)


def stock_adjustment_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Adjustment No</td><td>{{ doc.stkadjid }}</td><td class="label">Date</td><td>{{ doc.get_formatted("sadate") }}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>Store</th><th>Item</th><th>Filled Item</th><th>Party</th><th>Current</th><th>Inc</th><th>Dec</th><th>Adjusted</th><th>Rate</th><th>Amount</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.storeid }}</td><td>{{ row.itemcode }}</td><td>{{ row.bagitemcode or "" }}</td>
<td>{{ row.partyid or "" }}</td>
<td class="text-right">{{ row.get_formatted("current_stock", doc) }}</td>
<td class="text-right">{{ row.get_formatted("inc_stock", doc) }}</td>
<td class="text-right">{{ row.get_formatted("dec_stock", doc) }}</td>
<td class="text-right">{{ row.get_formatted("adjusted_stock", doc) }}</td>
<td class="text-right">{{ row.get_formatted("rate", doc) }}</td>
<td class="text-right">{{ row.get_formatted("amount", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Stock Adjustment", body)


def closing_stock_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Closing No</td><td>{{ doc.sopenid }}</td><td class="label">Date</td><td>{{ doc.get_formatted("opendate") }}</td></tr>
<tr><td class="label">Total Stock</td><td colspan="3">{{ doc.get_formatted("total_stock") }}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>Store</th><th>Item</th><th>Filled Item</th><th>Party</th><th>Closing Qty</th><th>Avg Rate</th><th>Stock Value</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.storeid }}</td><td>{{ row.itemcode }}</td><td>{{ row.bagitemcode or "" }}</td>
<td>{{ row.partyid or "" }}</td>
<td class="text-right">{{ row.get_formatted("closing_stock", doc) or row.get_formatted("opening_stock", doc) }}</td>
<td class="text-right">{{ row.get_formatted("movingrate", doc) }}</td>
<td class="text-right">{{ row.get_formatted("stock_value", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap("Closing Stock", body)


def _other_bill_return_html(title: str, return_field: str, bill_field: str) -> str:
	body = f"""
<table class="meta">
<tr><td class="label">Return No</td><td>{{{{ doc.{return_field} }}}}</td><td class="label">Date</td><td>{{{{ doc.get_formatted("brdate") }}}}</td></tr>
<tr><td class="label">Bill No</td><td>{{{{ doc.{bill_field} }}}}</td><td class="label">Party</td><td>{{{{ doc.party_name or "" }}}}</td></tr>
<tr><td class="label">Reference</td><td colspan="3">{{{{ doc.referno or "" }}}}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>Item</th><th>Qty</th><th>Rate</th><th>Amount</th><th>Store</th></tr></thead>
<tbody>{{% for row in doc.details %}}
<tr><td>{{{{ row.idx }}}}</td><td>{{{{ row.item_name or "" }}}}</td>
<td class="text-right">{{{{ row.get_formatted("quantity", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("rate", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("amount", doc) }}}}</td>
<td>{{{{ row.storeid or "" }}}}</td></tr>
{{% endfor %}}</tbody></table>
{{% if doc.remarks %}}<p><strong>Remarks:</strong> {{{{ doc.remarks }}}}</p>{{% endif %}}
"""
	return _wrap(title, body)


def purchase_return_other_bill_html() -> str:
	return _other_bill_return_html("Purchase Return Other Bill", "prbillno", "pbillno")


def sales_return_other_bill_html() -> str:
	return _other_bill_return_html("Sales Return Other Bill", "srbillno", "sbillno")


def _other_bill_html(title: str, bill_field: str, party_field: str) -> str:
	body = f"""
<table class="meta">
<tr><td class="label">Bill No</td><td>{{{{ doc.{bill_field} }}}}</td><td class="label">Date</td><td>{{{{ doc.get_formatted("billdate") }}}}</td></tr>
<tr><td class="label">Party</td><td colspan="3">{{{{ frappe.db.get_value("Party", doc.{party_field}, "party_name") or doc.{party_field} }}}}</td></tr>
<tr><td class="label">Reference</td><td>{{{{ doc.referno or "" }}}}</td><td class="label">Amount</td><td>{{{{ doc.get_formatted("amount") }}}}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>Item</th><th>Qty</th><th>Rate</th><th>Amount</th><th>Store</th></tr></thead>
<tbody>{{% for row in doc.details %}}
<tr><td>{{{{ row.idx }}}}</td><td>{{{{ row.itemcode }}}}</td>
<td class="text-right">{{{{ row.get_formatted("quantity", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("rate", doc) }}}}</td>
<td class="text-right">{{{{ row.get_formatted("amount", doc) }}}}</td>
<td>{{{{ row.storeid or "" }}}}</td></tr>
{{% endfor %}}</tbody></table>
{{% if doc.remarks %}}<p><strong>Remarks:</strong> {{{{ doc.remarks }}}}</p>{{% endif %}}
"""
	return _wrap(title, body)


def purchase_other_bill_html() -> str:
	return _other_bill_html("Purchase Other Bill", "pbillno", "partyid")


def sales_other_bill_html() -> str:
	return _other_bill_html("Sales Other Bill", "sbillno", "partyid")


def po_cancellation_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Cancellation No</td><td>{{ doc.pocid }}</td><td class="label">Date</td><td>{{ doc.get_formatted("candate") }}</td></tr>
<tr><td class="label">Party</td><td colspan="3">{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>PO No</th><th>Balance Qty</th><th>Cancel Qty</th><th>Rate</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.ponumber }}</td>
<td class="text-right">{{ row.get_formatted("truckqty", doc) }}</td>
<td class="text-right">{{ row.get_formatted("cancelqty", doc) }}</td>
<td class="text-right">{{ row.get_formatted("rate", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap_paged("PO Cancellation", body)


def so_cancellation_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Cancellation No</td><td>{{ doc.socid }}</td><td class="label">Date</td><td>{{ doc.get_formatted("candate") }}</td></tr>
<tr><td class="label">Party</td><td colspan="3">{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td></tr>
</table>
<table class="lines">
<thead><tr><th>#</th><th>SO No</th><th>Balance Qty</th><th>Cancel Qty</th><th>Rate</th></tr></thead>
<tbody>{% for row in doc.details %}
<tr><td>{{ row.idx }}</td><td>{{ row.sonumber }}</td>
<td class="text-right">{{ row.get_formatted("truckqty", doc) }}</td>
<td class="text-right">{{ row.get_formatted("cancelqty", doc) }}</td>
<td class="text-right">{{ row.get_formatted("rate", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% if doc.remarks %}<p><strong>Remarks:</strong> {{ doc.remarks }}</p>{% endif %}
"""
	return _wrap_paged("SO Cancellation", body)


def crashing_refine_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Crash ID</td><td>{{ doc.crashid }}</td><td class="label">Date</td><td>{{ doc.get_formatted("crdate") }}</td></tr>
<tr><td class="label">Mill</td><td colspan="3">{{ doc.mill_id or "" }}</td></tr>
</table>
<h4>Inputs</h4>
<table class="lines lines-wide">
<thead><tr><th>#</th><th>Store</th><th>Item</th><th>Bag</th><th>Bags</th><th>Bag Wt</th><th>Total Wt</th><th>Ref Bags</th><th>Ref Wt</th><th>Dip</th><th>Prod 1</th><th>Prod 2</th></tr></thead>
<tbody>{% for row in doc.inputs %}
<tr><td>{{ row.idx }}</td><td>{{ row.storeid }}</td><td>{{ row.critem or "" }}</td><td>{{ row.crbagid or "" }}</td>
<td class="text-right">{{ row.bagqty or "" }}</td><td class="text-right">{{ row.get_formatted("bagweight", doc) }}</td>
<td class="text-right">{{ row.get_formatted("total_weight", doc) }}</td><td class="text-right">{{ row.ref_bags or "" }}</td>
<td class="text-right">{{ row.get_formatted("ref_weight", doc) }}</td><td class="text-right">{{ row.get_formatted("dip", doc) }}</td>
<td class="text-right">{{ row.get_formatted("prod_1", doc) }}</td><td class="text-right">{{ row.get_formatted("prod_2", doc) }}</td></tr>
{% endfor %}</tbody></table>
<h4>Outputs</h4>
<table class="lines">
<thead><tr><th>#</th><th>Product</th><th>Weight</th><th>Store</th><th>Rate</th></tr></thead>
<tbody>{% for row in doc.outputs %}
<tr><td>{{ row.idx }}</td><td>{{ row.proditem }}</td><td class="text-right">{{ row.get_formatted("weight", doc) }}</td>
<td>{{ row.storeid }}</td><td class="text-right">{{ row.get_formatted("rate", doc) }}</td></tr>
{% endfor %}</tbody></table>
"""
	return _wrap_paged("Crashing Refine", body, landscape=True)


def payment_by_hawala_html() -> str:
	body = """
<table class="meta">
<tr><td class="label">Hawala No</td><td>{{ doc.gmid }}</td><td class="label">Date</td><td>{{ doc.get_formatted("gmdate") }}</td></tr>
<tr><td class="label">Party A</td><td>{{ frappe.db.get_value("Party", doc.partyid, "party_name") or doc.partyid }}</td><td class="label">Mode</td><td>{{ doc.gmmode }}</td></tr>
<tr><td class="label">Amount</td><td>{{ doc.get_formatted("amount") }}</td><td class="label">Account</td><td>{{ doc.accid or "" }}</td></tr>
<tr><td class="label">Party B</td><td>{{ frappe.db.get_value("Party", doc.b_partyid, "party_name") or doc.b_partyid or "" }}</td><td class="label">B Amount</td><td>{{ doc.get_formatted("b_amount") }}</td></tr>
</table>
{% if doc.invoices %}
<h4>Invoices</h4>
<table class="lines"><thead><tr><th>#</th><th>Doc Type</th><th>Document ID</th><th>Amount</th></tr></thead>
<tbody>{% for row in doc.invoices %}
<tr><td>{{ row.idx }}</td><td>{{ row.doctypeid }}</td><td>{{ row.documentid }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.party_b_lines %}
<h4>Party B Lines</h4>
<table class="lines"><thead><tr><th>#</th><th>Party</th><th>Account</th><th>Mode</th><th>Amount</th></tr></thead>
<tbody>{% for row in doc.party_b_lines %}
<tr><td>{{ row.idx }}</td><td>{{ row.partyid or "" }}</td><td>{{ row.accid }}</td><td>{{ row.gmmode }}</td><td class="text-right">{{ row.get_formatted("amount", doc) }}</td></tr>
{% endfor %}</tbody></table>
{% endif %}
{% if doc.narration %}<p><strong>Narration:</strong> {{ doc.narration }}</p>{% endif %}
"""
	return _wrap("Payment By Hawala", body)


# (folder, Print Format name, DocType, html_fn)
PRINT_FORMATS: list[tuple[str, str, str, object]] = [
	("millitrix_purchase_invoice", "Purchase Invoice", "Purchase Invoice", purchase_invoice_html),
	("millitrix_purchase_invoice_full", "Purchase Invoice Full Detail", "Purchase Invoice", purchase_invoice_full_detail_html),
	("millitrix_sales_invoice", "Sales Invoice", "Sales Invoice", sales_invoice_html),
	("millitrix_sales_invoice_full", "Sales Invoice Full Detail", "Sales Invoice", sales_invoice_full_detail_html),
	("millitrix_gate_pass", "In Out Gate Pass", "In Out Gate Pass", gate_pass_html),
	("millitrix_gate_pass_full", "In Out Gate Pass Full Detail", "In Out Gate Pass", gate_pass_full_detail_html),
	("millitrix_purchase_order", "Purchase Order", "Purchase Order", purchase_order_html),
	("millitrix_sales_order", "Sales Order", "Sales Order", sales_order_html),
	("millitrix_pnr_voucher", "Payment and Receipt Voucher", "Payment and Receipt Voucher", pnr_voucher_html),
	("millitrix_advance_payment_voucher", "Advance Payment Voucher", "Advance PNR", advance_payment_voucher_html),
	("millitrix_advance_receipt_voucher", "Advance Receipt Voucher", "Advance PNR", advance_receipt_voucher_html),
	("millitrix_advance_payment", "Advance Payment", "Advance Payment", advance_payment_voucher_html),
	("millitrix_advance_receipt", "Advance Receipt", "Advance Receipt", advance_receipt_voucher_html),
	("millitrix_advance_pnr", "Advance PNR", "Advance PNR", advance_pnr_html),
	("millitrix_cnb_voucher", "Cash and Bank Voucher", "Cash and Bank Voucher", cnb_voucher_html),
	("millitrix_expense_voucher", "Expense Voucher", "Expense Voucher", expense_voucher_html),
	("millitrix_party_payment_voucher", "Party Payment Voucher", "Party Payment Voucher", party_cnb_voucher_html),
	("millitrix_party_receipt_voucher", "Party Receipt Voucher", "Party Receipt Voucher", party_cnb_voucher_html),
	("millitrix_voucher", "Voucher Transaction", "Voucher Transaction", mill_voucher_html),
	("millitrix_employee_payslip", "PaySlip", "PaySlip", employee_payslip_html),
	("millitrix_purchase_return", "Purchase Return", "Purchase Return", purchase_return_html),
	("millitrix_sales_return", "Sales Return", "Sales Return", sales_return_html),
	("millitrix_stock_transfer", "Stock Transfer Note", "Stock Transfer Note", stock_transfer_html),
	("millitrix_stock_transfer_full", "Stock Transfer Note Full Detail", "Stock Transfer Note", stock_transfer_full_detail_html),
	("millitrix_advance_adjustment", "Advance Adjustment", "Advance Adjustment", advance_adjustment_html),
	("millitrix_party_gross_margin", "Party Gross Margin", "Party Gross Margin", party_gross_margin_html),
	("millitrix_employee_payment_voucher", "Employee Payment Voucher", "Employee Payment Voucher", employee_payment_voucher_html),
	("millitrix_employee_receipt_voucher", "Employee Receipt Voucher", "Employee Receipt Voucher", employee_receipt_voucher_html),
	("millitrix_opening_stock", "Opening Stock", "Opening Stock", opening_stock_html),
	("millitrix_closing_stock", "Closing Stock", "Closing Stock", closing_stock_html),
	("millitrix_stock_adjustment", "Stock Adjustment", "Stock Adjustment", stock_adjustment_html),
	("millitrix_purchase_return_other_bill", "Purchase Return Other Bill", "Purchase Return Other Bill", purchase_return_other_bill_html),
	("millitrix_sales_return_other_bill", "Sales Return Other Bill", "Sales Return Other Bill", sales_return_other_bill_html),
	("millitrix_purchase_other_bill", "Purchase Other Bill", "Purchase Other Bill", purchase_other_bill_html),
	("millitrix_sales_other_bill", "Sales Other Bill", "Sales Other Bill", sales_other_bill_html),
	("millitrix_payment_by_hawala", "Payment By Hawala", "Payment By Hawala", payment_by_hawala_html),
	("millitrix_po_cancellation", "PO Cancellation", "PO Cancellation", po_cancellation_html),
	("millitrix_so_cancellation", "SO Cancellation", "SO Cancellation", so_cancellation_html),
	("millitrix_crashing_refine", "Crashing Refine", "Crashing Refine", crashing_refine_html),
]
