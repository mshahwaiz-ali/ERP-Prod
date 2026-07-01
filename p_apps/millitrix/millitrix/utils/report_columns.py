# Copyright (c) 2026, Millitrix and contributors
# Shared column builders + standards for Millitrix script reports.

from __future__ import annotations

from frappe import _

# Report column fieldname → (fieldtype, options, min_width)
COLUMN_STANDARDS: dict[str, tuple[str, str | None, int]] = {
	"ponumber": ("Link", "Purchase Order", 130),
	"sonumber": ("Link", "Sales Order", 130),
	"purchinvno": ("Link", "Purchase Invoice", 130),
	"salesinvno": ("Link", "Sales Invoice", 130),
	"location_id": ("Link", "Location", 130),
	"supplierid": ("Link", "Party", 160),
	"customerid": ("Link", "Party", 160),
	"brokerid": ("Link", "Party", 140),
	"partyid": ("Link", "Party", 140),
	"itemcode": ("Link", "Item Setup", 130),
	"storeid": ("Link", "Store Setup", 130),
	"tostoreid": ("Link", "Store Setup", 130),
	"accid": ("Link", "Chart of Accounting", 120),
	"podate": ("Date", None, 110),
	"sodate": ("Date", None, 110),
	"invdate": ("Date", None, 110),
	"tdate": ("Date", None, 110),
	"vouchdate": ("Date", None, 110),
	"status": ("Data", None, 100),
	"posted": ("Data", None, 90),
	"vouchmode": ("Data", None, 110),
	"narration": ("Data", None, 220),
	"detail": ("Data", None, 200),
	"account_name": ("Data", None, 200),
}


def _col(label: str, fieldname: str, fieldtype: str, width: int, options: str | None = None) -> dict:
	col: dict = {"label": label, "fieldname": fieldname, "fieldtype": fieldtype, "width": width}
	if options:
		col["options"] = options
	return col


def normalize_columns(columns: list[dict]) -> list[dict]:
	"""Apply shared fieldtypes/widths so reports render and link correctly."""
	out: list[dict] = []
	for col in columns:
		c = dict(col)
		std = COLUMN_STANDARDS.get(c.get("fieldname") or "")
		if std:
			ftype, options, min_w = std
			c["fieldtype"] = ftype
			if options:
				c["options"] = options
			elif "options" in c and ftype not in ("Link", "Dynamic Link"):
				c.pop("options", None)
			c["width"] = max(int(c.get("width") or 0), min_w)
		out.append(c)
	return out


def po_number_column(*, width: int = 130) -> dict:
	return _col(_("PO No"), "ponumber", "Link", width, "Purchase Order")


def so_number_column(*, width: int = 130) -> dict:
	return _col(_("SO No"), "sonumber", "Link", width, "Sales Order")


def purchase_invoice_no_column(*, width: int = 130) -> dict:
	return _col(_("Invoice No"), "purchinvno", "Link", width, "Purchase Invoice")


def sales_invoice_no_column(*, width: int = 130) -> dict:
	return _col(_("Invoice No"), "salesinvno", "Link", width, "Sales Invoice")


def location_column(*, width: int = 130) -> dict:
	return _col(_("Location"), "location_id", "Link", width, "Location")


def supplier_column(*, width: int = 160) -> dict:
	return _col(_("Supplier"), "supplierid", "Link", width, "Party")


def customer_column(*, width: int = 160) -> dict:
	return _col(_("Customer"), "customerid", "Link", width, "Party")


def item_column(*, width: int = 130) -> dict:
	return _col(_("Item"), "itemcode", "Link", width, "Item Setup")


def party_column(*, label: str | None = None, width: int = 140) -> dict:
	return _col(label or _("Party"), "partyid", "Link", width, "Party")


def date_column(fieldname: str, label: str, *, width: int = 110) -> dict:
	return _col(label, fieldname, "Date", width)


def status_column(*, width: int = 100) -> dict:
	return _col(_("Status"), "status", "Data", width)


def currency_column(fieldname: str, label: str, *, width: int = 120) -> dict:
	return _col(label, fieldname, "Currency", width)


def float_column(fieldname: str, label: str, *, width: int = 100) -> dict:
	return _col(label, fieldname, "Float", width)


def int_column(fieldname: str, label: str, *, width: int = 90) -> dict:
	return _col(label, fieldname, "Int", width)


def po_register_columns() -> list[dict]:
	return normalize_columns(
		[
			po_number_column(),
			date_column("podate", _("Date")),
			location_column(),
			supplier_column(),
			_col(_("Supplier Name"), "supplier_name", "Data", 180),
			_col(_("City"), "city_name", "Data", 120),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			float_column("truckqty", _("Truck Qty")),
			float_column("weight", _("Weight"), width=100),
			currency_column("rate", _("Rate"), width=90),
			currency_column("amount", _("Amount")),
			status_column(),
			_col(_("Remarks"), "remarks", "Data", 200),
		]
	)


def po_pending_columns() -> list[dict]:
	return normalize_columns(
		[
			po_number_column(),
			date_column("podate", _("Date")),
			location_column(),
			supplier_column(),
			_col(_("Supplier Name"), "supplier_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			status_column(),
			float_column("truckqty", _("Order Qty"), width=100),
			float_column("weight", _("Order Wgt"), width=100),
			float_column("truckreceived", _("Received")),
			float_column("truckqtycancel", _("Cancelled")),
			float_column("open_trucks", _("Open Trucks"), width=110),
			float_column("open_weight", _("Open Wgt"), width=100),
			currency_column("rate", _("Rate"), width=110),
			currency_column("amount", _("Order Amount")),
			currency_column("open_amount", _("Open Amount"), width=110),
		]
	)


def po_summary_columns() -> list[dict]:
	return normalize_columns(
		[
			location_column(),
			supplier_column(width=140),
			_col(_("Supplier Name"), "supplier_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Broker"), "brokerid", "Link", 140, "Party"),
			_col(_("Broker Name"), "broker_name", "Data", 160),
			int_column("order_count", _("Order Count"), width=110),
			float_column("total_trucks", _("Total Trucks"), width=110),
			float_column("total_weight", _("Total Weight"), width=110),
			currency_column("total_amount", _("Total Amount")),
		]
	)


def so_summary_columns() -> list[dict]:
	return normalize_columns(
		[
			location_column(),
			customer_column(width=140),
			_col(_("Customer Name"), "customer_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Broker"), "brokerid", "Link", 140, "Party"),
			_col(_("Broker Name"), "broker_name", "Data", 160),
			int_column("order_count", _("Order Count"), width=110),
			float_column("total_trucks", _("Total Trucks"), width=110),
			float_column("total_weight", _("Total Weight"), width=110),
			currency_column("total_amount", _("Total Amount")),
		]
	)


def stk_rece_summary_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("tdate", _("Date")),
			location_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			float_column("total_qty", _("Total Qty"), width=100),
			int_column("movement_count", _("Movements"), width=90),
		]
	)


def supp_inv_and_pay_columns() -> list[dict]:
	return normalize_columns(
		[
			sales_invoice_no_column(),
			date_column("invdate", _("Date")),
			location_column(),
			customer_column(),
			_col(_("Customer Name"), "customer_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			_col(_("Truck No"), "truckno", "Data", 100),
			float_column("netweight", _("Net Weight"), width=100),
			float_column("lessweight", _("Less Weight"), width=100),
			currency_column("line_amount", _("Line Amount"), width=110),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("applied", _("Applied"), width=110),
			currency_column("docbalamnt", _("Balance"), width=110),
		]
	)


def daily_item_purch_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("tdate", _("Date")),
			location_column(),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 180),
			float_column("total_weight", _("Total Weight"), width=120),
			currency_column("total_amount", _("Total Amount")),
			currency_column("avg_rate", _("Avg Rate"), width=110),
			int_column("invoice_count", _("Invoice Count"), width=110),
		]
	)


def daily_item_sales_columns() -> list[dict]:
	return daily_item_purch_columns()


def so_inv_detail_columns() -> list[dict]:
	return normalize_columns(
		[
			so_number_column(),
			date_column("sodate", _("SO Date")),
			location_column(),
			customer_column(),
			_col(_("Customer Name"), "party_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			float_column("truckqty", _("SO Trucks"), width=100),
			currency_column("so_amount", _("SO Amount"), width=110),
			_col(_("Invoice No"), "salesinvno", "Link", 130, "Sales Invoice"),
			date_column("invdate", _("Invoice Date")),
			_col(_("Truck No"), "truckno", "Data", 100),
			float_column("bagqty", _("Bag Qty"), width=90),
			float_column("bagweight", _("Bag Weight"), width=100),
			float_column("kanta_weight", _("Kanta Weight"), width=110),
			float_column("netweight", _("Net Weight"), width=100),
			currency_column("line_amount", _("Line Amount"), width=120),
		]
	)


def so_register_columns() -> list[dict]:
	return normalize_columns(
		[
			so_number_column(),
			date_column("sodate", _("Date")),
			location_column(),
			customer_column(),
			_col(_("Customer Name"), "customer_name", "Data", 180),
			_col(_("Cust City"), "cust_city", "Data", 120),
			_col(_("Broker"), "brokerid", "Link", 140, "Party"),
			_col(_("Broker Name"), "broker_name", "Data", 160),
			_col(_("Broker City"), "broker_city", "Data", 120),
			_col(_("Deli City"), "deli_city", "Data", 120),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			float_column("truckqty", _("Truck Qty")),
			float_column("weight", _("Weight"), width=100),
			currency_column("rate", _("Rate"), width=90),
			currency_column("amount", _("Amount")),
			status_column(),
			_col(_("Remarks"), "remarks", "Data", 200),
		]
	)


def so_pending_columns() -> list[dict]:
	return normalize_columns(
		[
			so_number_column(),
			date_column("sodate", _("Date")),
			location_column(),
			customer_column(),
			_col(_("Customer Name"), "customer_name", "Data", 180),
			_col(_("City"), "city_name", "Data", 120),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			status_column(),
			float_column("truckqty", _("Order Qty"), width=100),
			float_column("weight", _("Order Wgt"), width=100),
			float_column("truckissued", _("Issued")),
			float_column("truckqtycancel", _("Cancelled")),
			float_column("open_trucks", _("Open Trucks"), width=110),
			float_column("open_weight", _("Open Wgt"), width=100),
			currency_column("rate", _("Rate"), width=110),
			currency_column("amount", _("Order Amount")),
			currency_column("open_amount", _("Open Amount"), width=110),
		]
	)


def purchase_invoice_register_columns() -> list[dict]:
	return normalize_columns(
		[
			purchase_invoice_no_column(),
			date_column("invdate", _("Date")),
			location_column(),
			supplier_column(),
			_col(_("Supplier Name"), "supplier_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Borrow"), "borrow", "Data", 100),
			po_number_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			_col(_("Truck No"), "truckno", "Data", 100),
			float_column("bagqty", _("Bag Qty"), width=90),
			float_column("bagweight", _("Bag Weight"), width=90),
			float_column("netweight", _("Net Weight"), width=100),
			currency_column("rate", _("Rate"), width=90),
			currency_column("line_amount", _("Line Amount"), width=110),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("payable", _("Payable"), width=110),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Remarks"), "remarks", "Data", 200),
		]
	)


def sales_invoice_register_columns() -> list[dict]:
	return normalize_columns(
		[
			sales_invoice_no_column(),
			date_column("invdate", _("Date")),
			location_column(),
			customer_column(),
			_col(_("Customer Name"), "customer_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Borrow"), "borrow", "Data", 100),
			so_number_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			_col(_("Truck No"), "truckno", "Data", 100),
			float_column("bagqty", _("Bag Qty"), width=90),
			float_column("bagweight", _("Bag Weight"), width=90),
			float_column("netweight", _("Net Weight"), width=100),
			currency_column("rate", _("Rate"), width=90),
			currency_column("line_amount", _("Line Amount"), width=110),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("receivable", _("Receivable"), width=110),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Remarks"), "remarks", "Data", 200),
		]
	)


def po_inv_detail_columns() -> list[dict]:
	return normalize_columns(
		[
			po_number_column(),
			date_column("podate", _("PO Date")),
			location_column(),
			supplier_column(),
			_col(_("Supplier Name"), "supplier_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			float_column("truckqty", _("PO Trucks"), width=100),
			currency_column("po_amount", _("PO Amount"), width=110),
			purchase_invoice_no_column(),
			date_column("invdate", _("Invoice Date")),
			_col(_("Truck No"), "truckno", "Data", 100),
			float_column("netweight", _("Net Weight")),
			currency_column("line_amount", _("Line Amount"), width=120),
		]
	)


def pnl_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("Statement Line"), "statement_line", "Data", 180),
			_col(_("Account"), "accid", "Link", 120, "Chart of Accounting"),
			_col(_("Account Name"), "account_name", "Data", 220),
			_col(_("Nature"), "nature", "Data", 90),
			currency_column("opening_balance", _("Opening"), width=110),
			currency_column("debit", _("Debit"), width=110),
			currency_column("credit", _("Credit"), width=110),
			currency_column("balance", _("Balance"), width=110),
			_col(_("Dr/Cr"), "balance_side", "Data", 70),
		]
	)


def voucher_no_column(*, width: int = 110) -> dict:
	return _col(_("Voucher No"), "voucherno", "Data", width)


def document_id_column(*, label: str | None = None, width: int = 110) -> dict:
	return _col(label or _("Document ID"), "documentid", "Data", width)


def gl_voucher_line_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("vouchdate", _("Date")),
			voucher_no_column(),
			_col(_("Voucher Type"), "vouchertype_id", "Data", 100),
			_col(_("Doc Type"), "doctypeid", "Data", 160),
			document_id_column(),
			location_column(),
			_col(_("Account"), "accid", "Link", 120, "Chart of Accounting"),
			_col(_("Description"), "description", "Data", 200),
			_col(_("Nature"), "nature", "Data", 90),
			currency_column("debit", _("Debit"), width=110),
			currency_column("credit", _("Credit"), width=110),
			_col(_("Detail"), "detail", "Data", 180),
			_col(_("Reference"), "reference", "Data", 120),
			_col(_("Narration"), "narration", "Data", 200),
		]
	)


def gj_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("vouchdate", _("Date")),
			voucher_no_column(),
			location_column(),
			_col(_("Account"), "accid", "Link", 120, "Chart of Accounting"),
			_col(_("Description"), "description", "Data", 200),
			currency_column("debit", _("Debit"), width=110),
			currency_column("credit", _("Credit"), width=110),
			_col(_("Detail"), "detail", "Data", 180),
			_col(_("Reference"), "reference", "Data", 120),
			_col(_("Narration"), "narration", "Data", 200),
		]
	)


def item_bincard_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("tdate", _("Date")),
			location_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Movement"), "movement", "Data", 80),
			float_column("qty", _("Qty"), width=90),
			float_column("balance", _("Balance"), width=90),
			_col(_("Source"), "source", "Data", 120),
			document_id_column(label=_("Document")),
		]
	)


def item_ledger_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("tdate", _("Date")),
			location_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 160),
			_col(_("Movement"), "movement", "Data", 80),
			float_column("qty", _("Qty"), width=90),
			float_column("balance", _("Balance"), width=90),
			_col(_("Doc Type"), "doctypeid", "Data", 140),
			_col(_("Source"), "source", "Data", 120),
			document_id_column(label=_("Document")),
		]
	)


def item_daily_stock_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("tdate", _("Date")),
			location_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			float_column("opening_balance", _("Opening"), width=100),
			float_column("stock_in", _("Stock In"), width=90),
			float_column("stock_out", _("Stock Out"), width=90),
			float_column("net_movement", _("Net"), width=90),
			float_column("closing_balance", _("Closing"), width=100),
		]
	)


def item_stock_columns() -> list[dict]:
	return normalize_columns(
		[
			location_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Bag Item"), "bagitemcode", "Link", 120, "Item Setup"),
			_col(_("Bag Name"), "bag_item_name", "Data", 140),
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 160),
			_col(_("Bags Are"), "bags_are", "Data", 90),
			float_column("opening_stock", _("Opening Stock"), width=110),
			float_column("stock_in_hand", _("Stock In Hand"), width=110),
			float_column("bagweight", _("Per Bag"), width=90),
			currency_column("movingrate", _("Rate"), width=100),
			currency_column("amount", _("Amount"), width=110),
			date_column("ltdate", _("Last Trans Date")),
		]
	)


def monthly_item_purch_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("Month"), "month", "Data", 90),
			location_column(),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 180),
			float_column("total_weight", _("Total Weight"), width=120),
			currency_column("total_amount", _("Total Amount")),
			currency_column("avg_rate", _("Avg Rate"), width=110),
			int_column("invoice_count", _("Invoice Count"), width=110),
		]
	)


def monthly_item_sales_columns() -> list[dict]:
	return monthly_item_purch_columns()


def party_balance_columns() -> list[dict]:
	return normalize_columns(
		[
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 180),
			_col(_("Category"), "party_status", "Data", 120),
			currency_column("opening_balance", _("Opening"), width=110),
			currency_column("total_debit", _("Debit"), width=110),
			currency_column("total_credit", _("Credit"), width=110),
			currency_column("balance", _("Balance"), width=110),
			_col(_("Dr/Cr"), "balance_side", "Data", 70),
		]
	)


def party_bal_paid_columns() -> list[dict]:
	return normalize_columns(
		[
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 180),
			_col(_("Category"), "party_status", "Data", 120),
			currency_column("opening_balance", _("Opening"), width=110),
			currency_column("payable", _("Payable"), width=110),
			currency_column("payment_total", _("Payments"), width=110),
			currency_column("payment_balance", _("Balance"), width=110),
			currency_column("total_debit", _("Debit"), width=110),
			currency_column("total_credit", _("Credit"), width=110),
		]
	)


def party_bardana_columns() -> list[dict]:
	return normalize_columns(
		[
			location_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Bag Item"), "bagitemcode", "Link", 120, "Item Setup"),
			_col(_("Bag Name"), "bag_item_name", "Data", 140),
			_col(_("Bags Are"), "bags_are", "Data", 90),
			float_column("opening_stock", _("Opening Stock"), width=110),
			float_column("stock_in_hand", _("Stock In Hand"), width=110),
			float_column("bagweight", _("Per Bag"), width=90),
			date_column("ltdate", _("Last Date")),
		]
	)


def party_bardana_bincard_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("tdate", _("Date")),
			location_column(),
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 180),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Movement"), "movement", "Data", 80),
			float_column("qty", _("Qty"), width=90),
			float_column("balance", _("Balance"), width=90),
			_col(_("Source"), "source", "Data", 120),
			document_id_column(label=_("Document")),
			_col(_("Detail"), "detail", "Data", 160),
		]
	)


def party_ledger_summary_columns() -> list[dict]:
	return normalize_columns(
		[
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 180),
			currency_column("opening_balance", _("Opening"), width=110),
			currency_column("total_debit", _("Debit"), width=110),
			currency_column("total_credit", _("Credit"), width=110),
			currency_column("balance", _("Balance"), width=110),
		]
	)


def party_p_register_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("CNB No"), "cnbvno", "Data", 120),
			date_column("vouchdate", _("Date")),
			location_column(),
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 180),
			_col(_("Voucher Mode"), "vouchmode", "Data", 110),
			currency_column("amount", _("Amount")),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Refer No"), "referno", "Data", 110),
			date_column("referdate", _("Refer Date")),
			_col(_("Narration"), "narration", "Data", 220),
		]
	)


def item_wise_stock_columns() -> list[dict]:
	return normalize_columns(
		[
			item_column(width=140),
			_col(_("Item Name"), "item_name", "Data", 180),
			_col(_("Item Class"), "iclassid", "Link", 120, "Item Class"),
			location_column(),
			int_column("store_count", _("Store Count"), width=100),
			float_column("opening_stock", _("Opening Stock"), width=110),
			float_column("stock_in_hand", _("Stock In Hand"), width=120),
			currency_column("amount", _("Amount"), width=110),
		]
	)


def ledger_line_columns(*, include_balance: bool = False, include_doc_type: bool = False) -> list[dict]:
	columns = [
		date_column("vouchdate", _("Date")),
		voucher_no_column(),
	]
	if include_doc_type:
		columns.extend(
			[
				_col(_("Doc Type"), "doctypeid", "Data", 160),
				document_id_column(),
			]
		)
	columns.extend(
		[
			_col(_("Account"), "accid", "Link", 120, "Chart of Accounting"),
			_col(_("Account Name"), "account_name", "Data", 200),
			party_column(width=140),
			currency_column("debit", _("Debit"), width=110),
			currency_column("credit", _("Credit"), width=110),
		]
	)
	if include_balance:
		columns.append(currency_column("balance", _("Balance"), width=110))
	columns.extend(
		[
			_col(_("Detail"), "detail", "Data", 200),
			_col(_("Narration"), "narration", "Data", 220),
		]
	)
	return normalize_columns(columns)


def trial_style_columns(*, include_nature: bool = False) -> list[dict]:
	columns = [
		_col(_("Account"), "accid", "Link", 120, "Chart of Accounting"),
		_col(_("Account Name"), "account_name", "Data", 220),
	]
	if include_nature:
		columns.append(_col(_("Nature"), "nature", "Data", 90))
	columns.extend(
		[
			currency_column("opening_debit", _("Opening Debit")),
			currency_column("opening_credit", _("Opening Credit")),
			currency_column("debit", _("Debit")),
			currency_column("credit", _("Credit")),
			currency_column("closing_debit", _("Closing Debit")),
			currency_column("closing_credit", _("Closing Credit")),
		]
	)
	return normalize_columns(columns)


def cnb_register_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("CNB No"), "cnbvno", "Data", 120),
			date_column("vouchdate", _("Date")),
			location_column(),
			_col(_("Voucher Mode"), "vouchmode", "Data", 110),
			currency_column("amount", _("Amount")),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Narration"), "narration", "Data", 220),
		]
	)


def pnr_register_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("PNR No"), "pnrno", "Data", 120),
			date_column("pnrdate", _("PNR Date")),
			location_column(),
			party_column(width=160),
			currency_column("amount", _("Amount")),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Narration"), "narration", "Data", 220),
		]
	)


def discount_pnr_register_columns(*, payment: bool = True) -> list[dict]:
	party_label = _("Supplier") if payment else _("Customer")
	return normalize_columns(
		[
			_col(_("PNR No"), "pnrno", "Data", 120),
			date_column("pnrdate", _("Date")),
			location_column(),
			_col(party_label, "partyid", "Link", 140, "Party"),
			_col(_("Party Name"), "party_name", "Data", 180),
			_col(_("Invoice No"), "invoice_no", "Data", 120),
			_col(_("Item Name"), "item_name", "Data", 160),
			currency_column("docbalamnt", _("Invoice Balance"), width=120),
			currency_column("amount", _("Discount"), width=110),
			currency_column("doc_amount", _("PNR Amount"), width=110),
			_col(_("Refer No"), "referno", "Data", 110),
			date_column("referdate", _("Refer Date")),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Narration"), "narration", "Data", 220),
		]
	)


def payment_register_detail_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("CNB No"), "cnbvno", "Data", 120),
			date_column("vouchdate", _("Date")),
			location_column(),
			_col(_("Cash/Bank"), "paymode_desc", "Data", 120),
			_col(_("Refer No"), "referno", "Data", 110),
			date_column("referdate", _("Refer Date")),
			currency_column("doc_amount", _("Doc Amount"), width=110),
			_col(_("Account"), "accid", "Link", 120, "Chart of Accounting"),
			_col(_("Account Name"), "account_name", "Data", 180),
			currency_column("amount", _("Line Amount"), width=110),
			_col(_("Detail"), "detail", "Data", 200),
			_col(_("Narration"), "narration", "Data", 220),
			_col(_("Posted"), "posted", "Data", 90),
		]
	)


def invoice_outstanding_columns(*, party_label: str | None = None) -> list[dict]:
	label = party_label or _("Party")
	return normalize_columns(
		[
			_col(_("Doc Type"), "doctypeid", "Data", 160),
			document_id_column(label=_("Invoice No")),
			date_column("invdate", _("Date")),
			location_column(),
			_col(label, "partyid", "Link", 140, "Party"),
			_col(_("Party Name"), "party_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("applied", _("Applied"), width=110),
			currency_column("docbalamnt", _("Outstanding"), width=110),
			_col(_("Remarks"), "remarks", "Data", 200),
		]
	)


def pi_summary_columns() -> list[dict]:
	return normalize_columns(
		[
			location_column(),
			supplier_column(width=140),
			_col(_("Supplier Name"), "supplier_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Invoice Count"), "invoice_count", "Int", 100),
			currency_column("total_amount", _("Inv Amount"), width=110),
			currency_column("total_payable", _("Payable"), width=110),
		]
	)


def si_summary_columns() -> list[dict]:
	return normalize_columns(
		[
			location_column(),
			customer_column(width=140),
			_col(_("Customer Name"), "customer_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			int_column("invoice_count", _("Invoice Count"), width=100),
			float_column("bagweight", _("Bag Weight"), width=100),
			float_column("netweight", _("Net Weight"), width=110),
			currency_column("broker_amnt", _("Broker Amount"), width=110),
			currency_column("total_amount", _("Inv Amount"), width=110),
			currency_column("total_receivable", _("Receivable"), width=110),
		]
	)


def sip_outstanding_columns() -> list[dict]:
	return normalize_columns(
		[
			location_column(),
			customer_column(width=140),
			_col(_("Customer Name"), "party_name", "Data", 180),
			int_column("invoice_count", _("Invoice Count"), width=100),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("applied", _("Applied"), width=110),
			currency_column("docbalamnt", _("Outstanding"), width=110),
		]
	)


def purch_invoice_columns() -> list[dict]:
	return normalize_columns(
		[
			purchase_invoice_no_column(),
			date_column("invdate", _("Date")),
			location_column(),
			supplier_column(),
			_col(_("Supplier Name"), "supplier_name", "Data", 180),
			_col(_("Sub Party"), "sub_partyid", "Link", 140, "Party"),
			_col(_("Sub Party Name"), "sub_party_name", "Data", 160),
			_col(_("Broker"), "brokerid", "Link", 140, "Party"),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			po_number_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			_col(_("Truck No"), "truckno", "Data", 100),
			float_column("truckqty", _("Truck Qty"), width=90),
			float_column("bagqty", _("Bag Qty"), width=90),
			float_column("lessweight", _("Less Weight"), width=100),
			float_column("dust", _("Dust"), width=90),
			float_column("netweight", _("Net Weight"), width=100),
			currency_column("bardana", _("Bardana"), width=90),
			currency_column("bagamnt", _("Bag Amount"), width=100),
			currency_column("rate", _("Rate"), width=90),
			currency_column("totalamnt", _("Line Amount"), width=110),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("payable", _("Payable"), width=110),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Remarks"), "remarks", "Data", 200),
		]
	)


def purch_inv_payment_detail_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("Voucher No"), "voucherno", "Data", 110),
			date_column("vouchdate", _("Date")),
			_col(_("Source"), "source", "Data", 120),
			_col(_("Mode"), "vouchmode", "Data", 90),
			_col(_("Refer No"), "referno", "Data", 110),
			location_column(),
			_col(_("Supplier"), "partyid", "Link", 140, "Party"),
			_col(_("Party Name"), "party_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Doc Type"), "doctypeid", "Data", 160),
			document_id_column(label=_("Invoice No")),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("docbalamnt", _("Doc Balance"), width=110),
			currency_column("amount", _("Payment"), width=110),
		]
	)


def purch_inv_payment_register_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("Voucher No"), "voucherno", "Data", 110),
			date_column("vouchdate", _("Date")),
			_col(_("Source"), "source", "Data", 120),
			_col(_("Mode"), "vouchmode", "Data", 90),
			_col(_("Refer No"), "referno", "Data", 110),
			location_column(),
			_col(_("Supplier"), "partyid", "Link", 140, "Party"),
			_col(_("Party Name"), "party_name", "Data", 180),
			int_column("line_count", _("Lines"), width=70),
			currency_column("amount", _("Payment"), width=110),
		]
	)


def purch_item_summary_columns() -> list[dict]:
	return normalize_columns(
		[
			location_column(),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			supplier_column(width=140),
			_col(_("Supplier Name"), "supplier_name", "Data", 180),
			_col(_("City"), "city_name", "Data", 120),
			int_column("invoice_count", _("Invoice Count"), width=100),
			float_column("total_weight", _("Net Weight"), width=110),
			float_column("lessweight", _("Less Weight"), width=100),
			float_column("dust", _("Dust"), width=90),
			currency_column("line_amount", _("Line Amount"), width=110),
			currency_column("avg_rate", _("Avg Rate"), width=90),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("payable", _("Payable"), width=110),
		]
	)


def sales_invoice_columns() -> list[dict]:
	return normalize_columns(
		[
			sales_invoice_no_column(),
			date_column("invdate", _("Date")),
			location_column(),
			customer_column(),
			_col(_("Customer Name"), "customer_name", "Data", 180),
			_col(_("Sub Party"), "sub_partyid", "Link", 140, "Party"),
			_col(_("Sub Party Name"), "sub_party_name", "Data", 160),
			_col(_("Broker"), "brokerid", "Link", 140, "Party"),
			_col(_("Broker Name"), "broker_name", "Data", 160),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Borrow"), "borrow", "Data", 100),
			_col(_("Kanta Type"), "kantatype", "Data", 120),
			so_number_column(),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			_col(_("Truck No"), "truckno", "Data", 100),
			float_column("truckqty", _("Truck Qty"), width=90),
			float_column("bagqty", _("Bag Qty"), width=90),
			float_column("bagweight", _("Bag Weight"), width=90),
			float_column("delikanta", _("Deli Kanta"), width=100),
			float_column("lessweight", _("Less Weight"), width=100),
			float_column("netweight", _("Net Weight"), width=100),
			currency_column("bardana", _("Bardana"), width=90),
			currency_column("bagamnt", _("Bag Amount"), width=100),
			currency_column("rate", _("Rate"), width=90),
			currency_column("labouramnt", _("Labour"), width=90),
			currency_column("brokeramnt", _("Broker Amount"), width=100),
			currency_column("totalamnt", _("Line Amount"), width=110),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("receivable", _("Receivable"), width=110),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Remarks"), "remarks", "Data", 200),
		]
	)


def sales_inv_receipt_detail_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("Voucher No"), "voucherno", "Data", 110),
			date_column("vouchdate", _("Date")),
			_col(_("Source"), "source", "Data", 120),
			_col(_("Mode"), "vouchmode", "Data", 90),
			_col(_("Refer No"), "referno", "Data", 110),
			location_column(),
			_col(_("Customer"), "partyid", "Link", 140, "Party"),
			_col(_("Party Name"), "party_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Doc Type"), "doctypeid", "Data", 160),
			document_id_column(label=_("Invoice No")),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("docbalamnt", _("Doc Balance"), width=110),
			currency_column("amount", _("Receipt"), width=110),
		]
	)


def sales_inv_receipt_register_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("Voucher No"), "voucherno", "Data", 110),
			date_column("vouchdate", _("Date")),
			_col(_("Source"), "source", "Data", 120),
			_col(_("Mode"), "vouchmode", "Data", 90),
			_col(_("Refer No"), "referno", "Data", 110),
			location_column(),
			_col(_("Customer"), "partyid", "Link", 140, "Party"),
			_col(_("Party Name"), "party_name", "Data", 180),
			int_column("line_count", _("Lines"), width=70),
			currency_column("amount", _("Receipt"), width=110),
		]
	)


def sales_item_summary_columns() -> list[dict]:
	return normalize_columns(
		[
			location_column(),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			customer_column(width=140),
			_col(_("Customer Name"), "customer_name", "Data", 180),
			_col(_("City"), "city_name", "Data", 120),
			int_column("invoice_count", _("Invoice Count"), width=100),
			float_column("total_weight", _("Net Weight"), width=110),
			float_column("lessweight", _("Less Weight"), width=100),
			currency_column("line_amount", _("Line Amount"), width=110),
			currency_column("avg_rate", _("Avg Rate"), width=90),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("receivable", _("Receivable"), width=110),
		]
	)


def advance_pnr_register_columns(*, payment: bool = True) -> list[dict]:
	party_label = _("Supplier") if payment else _("Customer")
	return normalize_columns(
		[
			_col(_("PNR No"), "pnrno", "Data", 120),
			date_column("pnrdate", _("Doc Date")),
			date_column("referdate", _("Refer Date")),
			_col(_("Refer No"), "referno", "Data", 120),
			location_column(),
			_col(party_label, "partyid", "Link", 160, "Party"),
			_col(_("Party Name"), "party_name", "Data", 180),
			_col(_("Mode"), "pnrmode", "Data", 110),
			currency_column("amount", _("Amount")),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Narration"), "narration", "Data", 220),
		]
	)


def advance_adjustment_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("Adj No"), "adjid", "Data", 120),
			date_column("adjdate", _("Date")),
			location_column(),
			party_column(width=160),
			currency_column("amount", _("Amount")),
			_col(_("Posted"), "posted", "Data", 90),
			_col(_("Narration"), "narration", "Data", 220),
		]
	)


def advance_adjustment_register_columns(*, payment: bool = True) -> list[dict]:
	party_label = _("Supplier") if payment else _("Customer")
	return normalize_columns(
		[
			_col(_("Adj No"), "adjid", "Data", 110),
			date_column("adjdate", _("Doc Date")),
			location_column(width=120),
			_col(party_label, "partyid", "Link", 150, "Party"),
			_col(_("Party Name"), "party_name", "Data", 180),
			_col(_("Item"), "item_name", "Data", 140),
			currency_column("doc_amount", _("Doc Amount"), width=110),
			_col(_("Invoice No"), "invoice_no", "Data", 120),
			currency_column("inv_amount", _("Inv Amount"), width=110),
			_col(_("PNR No"), "sub_doc_id", "Data", 110),
			currency_column("sub_doc_amount", _("PNR Amount"), width=110),
			currency_column("line_amount", _("Amount"), width=110),
			_col(_("Narration"), "narration", "Data", 200),
		]
	)


def trial_balance_columns(*, include_location: bool = False) -> list[dict]:
	cols = []
	if include_location:
		cols.append(location_column())
	cols.extend(
		[
			_col(_("Account"), "accid", "Link", 120, "Chart of Accounting"),
			_col(_("Account Name"), "account_name", "Data", 220),
			currency_column("opening_debit", _("Opening Debit"), width=120),
			currency_column("opening_credit", _("Opening Credit"), width=120),
			currency_column("debit", _("Debit"), width=120),
			currency_column("credit", _("Credit"), width=120),
			currency_column("closing_debit", _("Closing Debit"), width=120),
			currency_column("closing_credit", _("Closing Credit"), width=120),
		]
	)
	return normalize_columns(cols)


def voucher_register_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("vouchdate", _("Date")),
			voucher_no_column(),
			_col(_("Voucher Type"), "vouchertype_id", "Data", 100),
			_col(_("Doc Type"), "doctypeid", "Data", 160),
			document_id_column(),
			location_column(),
			_col(_("Account"), "accid", "Link", 120, "Chart of Accounting"),
			_col(_("Account Description"), "description", "Data", 220),
			currency_column("debit", _("Debit"), width=110),
			currency_column("credit", _("Credit"), width=110),
			currency_column("day_balance", _("Day Balance"), width=110),
			_col(_("Detail"), "detail", "Data", 180),
			_col(_("Reference"), "reference", "Data", 120),
			_col(_("Narration"), "narration", "Data", 200),
		]
	)


def supp_pay_and_inv_columns() -> list[dict]:
	return normalize_columns(
		[
			purchase_invoice_no_column(),
			date_column("invdate", _("Date")),
			location_column(),
			supplier_column(),
			_col(_("Supplier Name"), "supplier_name", "Data", 180),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			_col(_("Truck No"), "truckno", "Data", 100),
			float_column("netweight", _("Net Weight"), width=100),
			float_column("lessweight", _("Less Weight"), width=100),
			currency_column("line_amount", _("Line Amount"), width=110),
			currency_column("invoice_amount", _("Inv Amount"), width=110),
			currency_column("applied", _("Applied"), width=110),
			currency_column("docbalamnt", _("Balance"), width=110),
		]
	)


def tstk_summary_columns() -> list[dict]:
	return normalize_columns(
		[
			_col(_("Transfer No"), "transferno", "Int", 90),
			date_column("tdate", _("Date")),
			location_column(),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("From Store"), "fromstoreid", "Link", 130, "Store Setup"),
			_col(_("From Store Name"), "from_store_name", "Data", 160),
			_col(_("To Store"), "tostoreid", "Link", 130, "Store Setup"),
			_col(_("To Store Name"), "to_store_name", "Data", 160),
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 160),
			float_column("bagqty", _("Bag Qty"), width=90),
			float_column("bagweight", _("Bag Weight"), width=100),
			float_column("total_wgt", _("Total Wgt"), width=100),
			float_column("delikanta", _("Deli Kanta"), width=100),
			float_column("netweight", _("Net Weight"), width=100),
			_col(_("Transporter"), "transporter", "Data", 140),
		]
	)


def unsubmit_stock_columns() -> list[dict]:
	return normalize_columns(
		[
			date_column("tdate", _("Date")),
			location_column(),
			_col(_("Doc Type"), "doctype", "Data", 160),
			document_id_column(label=_("Document")),
			item_column(),
			_col(_("Item Name"), "item_name", "Data", 160),
			_col(_("Store"), "storeid", "Link", 130, "Store Setup"),
			_col(_("Store Name"), "store_name", "Data", 160),
			party_column(width=140),
			_col(_("Party Name"), "party_name", "Data", 160),
			float_column("qty", _("Qty"), width=90),
			_col(_("Posted"), "posted", "Data", 90),
		]
	)
