# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate

from millitrix.utils.report_filters import normalize_report_dates
from millitrix.utils.user_permissions import apply_user_store_filters

_QTY_EXPR = "COALESCE(NULLIF(d.netweight, 0), d.truckqty, d.bagqty, 0)"


def _stock_ledger_key(row: dict) -> tuple[str, str]:
	return (row.get("storeid") or "", row.get("itemcode") or "")


def _compute_stock_opening(filters: dict) -> dict[tuple[str, str], float]:
	from_date = filters.get("from_date")
	if not from_date:
		return {}
	opening_end = str(add_days(getdate(from_date), -1))
	open_filters = {**filters, "to_date": opening_end}
	open_filters.pop("from_date", None)
	opening: dict[tuple[str, str], float] = {}
	for row in get_item_ledger_rows(open_filters):
		key = _stock_ledger_key(row)
		qty = flt(row.get("qty"))
		if row.get("movement") == "IN":
			opening[key] = opening.get(key, 0.0) + qty
		else:
			opening[key] = opening.get(key, 0.0) - qty
	return opening


def _stock_name_maps() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
	store_names = {
		row.name: row.description
		for row in frappe.get_all("Store Setup", fields=["name", "description"])
	}
	item_names = {
		row.name: row.itemname
		for row in frappe.get_all("Item Setup", fields=["name", "itemname"])
	}
	party_names = {
		row.name: row.party_name
		for row in frappe.get_all("Party", fields=["name", "party_name"])
	}
	return store_names, item_names, party_names


def _attach_stock_row_names(
	row: dict,
	*,
	store_names: dict[str, str],
	item_names: dict[str, str],
	party_names: dict[str, str],
) -> dict:
	storeid = row.get("storeid") or ""
	itemcode = row.get("itemcode") or ""
	partyid = row.get("partyid") or ""
	bagitemcode = row.get("bagitemcode") or ""
	return {
		**row,
		"store_name": store_names.get(storeid) or storeid,
		"item_name": item_names.get(itemcode) or itemcode,
		"bag_item_name": item_names.get(bagitemcode) or bagitemcode,
		"party_name": party_names.get(partyid) or partyid,
	}


def get_item_stock_rows(filters: dict | None = None) -> list[dict]:
	from millitrix.utils.report_filters import normalize_report_filters

	filters = normalize_report_filters(filters)
	conditions = []
	params: dict = {}

	if not filters.get("show_zero_stock"):
		conditions.append("isi.stock_in_hand != 0")

	if filters.get("location_id"):
		conditions.append("ms.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("storeid"):
		conditions.append("isi.storeid = %(storeid)s")
		params["storeid"] = filters["storeid"]
	elif filters.get("_allowed_stores"):
		conditions.append("isi.storeid IN %(allowed_stores)s")
		params["allowed_stores"] = tuple(filters["_allowed_stores"])
	if filters.get("itemcode"):
		conditions.append("isi.itemcode = %(itemcode)s")
		params["itemcode"] = filters["itemcode"]
	if filters.get("partyid"):
		conditions.append("isi.partyid = %(partyid)s")
		params["partyid"] = filters["partyid"]
	if filters.get("iclassid"):
		conditions.append("item.iclassid = %(iclassid)s")
		params["iclassid"] = filters["iclassid"]

	rows = frappe.db.sql(
		f"""SELECT
			ms.location_id,
			ms.description AS store_name,
			isi.storeid,
			isi.itemcode,
			item.itemname AS item_name,
			item.iclassid,
			isi.bagitemcode,
			bag.itemname AS bag_item_name,
			isi.partyid,
			party.party_name,
			isi.bags_are,
			isi.stock_in_hand,
			isi.opening_stock,
			isi.bagweight,
			isi.movingrate,
			(isi.stock_in_hand * isi.movingrate) AS amount,
			isi.ltdate
		FROM `tabStock In Hand` isi
		INNER JOIN `tabStore Setup` ms ON ms.name = isi.storeid
		LEFT JOIN `tabItem Setup` item ON item.name = isi.itemcode
		LEFT JOIN `tabItem Setup` bag ON bag.name = isi.bagitemcode
		LEFT JOIN `tabParty` party ON party.name = isi.partyid
		{"WHERE " + " AND ".join(conditions) if conditions else ""}
		ORDER BY ms.location_id, isi.storeid, isi.itemcode
		""",
		params,
		as_dict=True,
	)
	for row in rows:
		row["amount"] = flt(row.get("amount"))
	return rows


def get_item_wise_stock_rows(filters: dict | None = None) -> list[dict]:
	filters = apply_user_store_filters(dict(filters or {}))
	rows = get_item_stock_rows(filters)
	agg: dict[str, dict] = {}
	for row in rows:
		key = row["itemcode"]
		bucket = agg.setdefault(
			key,
			{
				"itemcode": key,
				"item_name": row.get("item_name") or key,
				"iclassid": row.get("iclassid"),
				"stock_in_hand": 0.0,
				"opening_stock": 0.0,
				"amount": 0.0,
				"store_count": 0,
				"location_id": row.get("location_id"),
			},
		)
		bucket["stock_in_hand"] += flt(row.get("stock_in_hand"))
		bucket["opening_stock"] += flt(row.get("opening_stock"))
		bucket["amount"] += flt(row.get("amount"))
		bucket["store_count"] += 1
	return sorted(agg.values(), key=lambda row: row["itemcode"])


def _ledger_date_filters(filters: dict, alias: str, date_field: str) -> tuple[list[str], dict]:
	conditions: list[str] = []
	params: dict = {}
	if filters.get("from_date"):
		conditions.append(f"{alias}.{date_field} >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append(f"{alias}.{date_field} <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append(f"{alias}.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	return conditions, params


def get_item_ledger_rows(filters: dict | None = None) -> list[dict]:
	"""Stock movement ledger from submitted stock documents (Oracle ItemLedger.rep)."""
	filters = apply_user_store_filters(normalize_report_dates(filters or {}))
	params: dict = {}
	clauses: list[str] = []

	if filters.get("itemcode"):
		params["itemcode"] = filters["itemcode"]
	if filters.get("storeid"):
		params["storeid"] = filters["storeid"]
	elif filters.get("_allowed_stores"):
		params["allowed_stores"] = tuple(filters["_allowed_stores"])

	item_filter = " AND itemcode = %(itemcode)s" if filters.get("itemcode") else ""
	store_filter = " AND storeid = %(storeid)s" if filters.get("storeid") else ""
	store_in_filter = " AND storeid IN %(allowed_stores)s" if filters.get("_allowed_stores") else ""

	def _append(source_sql: str, date_alias: str, date_field: str) -> None:
		date_conds, date_params = _ledger_date_filters(filters, date_alias, date_field)
		params.update(date_params)
		where = " AND ".join(date_conds) if date_conds else "1=1"
		clauses.append(f"({source_sql} AND {where}{item_filter}{store_filter}{store_in_filter})")

	_append(
		f"""
		SELECT pi.invdate AS tdate, pi.location_id, d.storeid, pi.itemcode, pi.supplierid AS partyid,
			'IN' AS movement, {_QTY_EXPR} AS qty, pi.purchinvno AS documentid, pi.doctypeid,
			'Purchase Invoice' AS source
		FROM `tabPurchase Invoice Detail` d
		INNER JOIN `tabPurchase Invoice` pi ON pi.name = d.parent
		WHERE pi.docstatus = 1
		""",
		"pi",
		"invdate",
	)
	_append(
		f"""
		SELECT si.invdate AS tdate, si.location_id, d.storeid, si.itemcode, si.customerid AS partyid,
			'OUT' AS movement, {_QTY_EXPR} AS qty, si.salesinvno AS documentid, si.doctypeid,
			'Sales Invoice' AS source
		FROM `tabSales Invoice Detail` d
		INNER JOIN `tabSales Invoice` si ON si.name = d.parent
		WHERE si.docstatus = 1
		""",
		"si",
		"invdate",
	)
	_append(
		f"""
		SELECT gp.gpdate AS tdate, gp.location_id, d.storeid, gp.itemcode, gp.partyid,
			CASE WHEN UPPER(gp.gptype) IN ('IN', 'PURCHASE', 'P') THEN 'IN' ELSE 'OUT' END AS movement,
			{_QTY_EXPR} AS qty, gp.gatepassno AS documentid, gp.doctypeid,
			'Gate Pass' AS source
		FROM `tabGate Pass Detail` d
		INNER JOIN `tabIn Out Gate Pass` gp ON gp.name = d.parent
		WHERE gp.docstatus = 1
		""",
		"gp",
		"gpdate",
	)
	_append(
		f"""
		SELECT st.tdate AS tdate, st.location_id, st.fromstoreid AS storeid, st.itemcode, st.partyid,
			'OUT' AS movement, {_QTY_EXPR} AS qty, st.transferno AS documentid, st.doctypeid,
			'Stock Transfer' AS source
		FROM `tabStock Transfer Detail` d
		INNER JOIN `tabStock Transfer Note` st ON st.name = d.parent
		WHERE st.docstatus = 1
		""",
		"st",
		"tdate",
	)
	_append(
		f"""
		SELECT st.tdate AS tdate, st.location_id, d.tostoreid AS storeid, st.itemcode, st.partyid,
			'IN' AS movement, {_QTY_EXPR} AS qty, st.transferno AS documentid, st.doctypeid,
			'Stock Transfer' AS source
		FROM `tabStock Transfer Detail` d
		INNER JOIN `tabStock Transfer Note` st ON st.name = d.parent
		WHERE st.docstatus = 1
		""",
		"st",
		"tdate",
	)
	_append(
		f"""
		SELECT sa.sadate AS tdate, sa.location_id, d.storeid, d.itemcode, d.partyid,
			'IN' AS movement, COALESCE(d.inc_stock, 0) AS qty, sa.stkadjid AS documentid, sa.doctypeid,
			'Stock Adjustment' AS source
		FROM `tabStock Adjustment Detail` d
		INNER JOIN `tabStock Adjustment` sa ON sa.name = d.parent
		WHERE sa.docstatus = 1 AND COALESCE(d.inc_stock, 0) > 0
		""",
		"sa",
		"sadate",
	)
	_append(
		f"""
		SELECT sa.sadate AS tdate, sa.location_id, d.storeid, d.itemcode, d.partyid,
			'OUT' AS movement, COALESCE(d.dec_stock, 0) AS qty, sa.stkadjid AS documentid, sa.doctypeid,
			'Stock Adjustment' AS source
		FROM `tabStock Adjustment Detail` d
		INNER JOIN `tabStock Adjustment` sa ON sa.name = d.parent
		WHERE sa.docstatus = 1 AND COALESCE(d.dec_stock, 0) > 0
		""",
		"sa",
		"sadate",
	)
	_append(
		f"""
		SELECT so.opendate AS tdate, so.location_id, d.storeid, d.itemcode, d.partyid,
			'IN' AS movement, COALESCE(d.opening_stock, 0) AS qty, so.sopenid AS documentid, so.doctypeid,
			'Stock Opening' AS source
		FROM `tabOpening Stock Detail` d
		INNER JOIN `tabOpening Stock` so ON so.name = d.parent
		WHERE so.docstatus = 1 AND COALESCE(d.opening_stock, 0) != 0
		""",
		"so",
		"opendate",
	)

	if not clauses:
		return []

	return frappe.db.sql(
		" UNION ALL ".join(clauses) + " ORDER BY tdate, documentid, movement",
		params,
		as_dict=True,
	)


def get_item_ledger_report_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle ItemLedger.RDF — stock movements with opening B/F and running balance."""
	filters = apply_user_store_filters(normalize_report_dates(filters or {}))
	store_names, item_names, party_names = _stock_name_maps()
	opening = _compute_stock_opening(filters)
	balances: dict[tuple[str, str], float] = dict(opening)
	out: list[dict] = []
	from_date = filters.get("from_date")

	def _append_opening(key: tuple[str, str], balance: float, tdate) -> None:
		if abs(balance) <= 0.0001:
			return
		storeid, itemcode = key
		out.append(
			_attach_stock_row_names(
				{
					"tdate": tdate,
					"location_id": filters.get("location_id") or "",
					"storeid": storeid,
					"itemcode": itemcode,
					"partyid": "",
					"movement": "",
					"qty": 0.0,
					"balance": flt(balance),
					"documentid": "",
					"doctypeid": "",
					"source": "",
					"detail": _("Opening Balance"),
				},
				store_names=store_names,
				item_names=item_names,
				party_names=party_names,
			)
		)

	seen_keys: set[tuple[str, str]] = set(opening.keys())
	if filters.get("itemcode") and filters.get("storeid"):
		key = (filters["storeid"], filters["itemcode"])
		_append_opening(key, balances.get(key, 0.0), from_date)
		seen_keys.add(key)
	elif filters.get("itemcode"):
		for key, balance in sorted(opening.items()):
			if key[1] == filters["itemcode"]:
				_append_opening(key, balance, from_date)
				seen_keys.add(key)

	period_rows = sorted(
		get_item_ledger_rows(filters),
		key=lambda r: (r.get("tdate") or "", r.get("storeid") or "", r.get("itemcode") or "", r.get("documentid") or ""),
	)
	for row in period_rows:
		key = _stock_ledger_key(row)
		if key not in seen_keys:
			seen_keys.add(key)
			_append_opening(key, balances.get(key, 0.0), row.get("tdate") or from_date)
		qty = flt(row.get("qty"))
		if row.get("movement") == "IN":
			balances[key] = balances.get(key, 0.0) + qty
		else:
			balances[key] = balances.get(key, 0.0) - qty
		out.append(
			_attach_stock_row_names(
				{**row, "balance": flt(balances.get(key, 0.0))},
				store_names=store_names,
				item_names=item_names,
				party_names=party_names,
			)
		)
	return out


def get_crash_refine_report_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle CrashRefine.RDF — submitted crashing/refine input and output lines."""
	filters = normalize_report_dates(filters or {})
	conditions = ["cr.docstatus = 1"]
	params: dict = {}
	if filters.get("from_date"):
		conditions.append("cr.crdate >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("cr.crdate <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("location_id"):
		conditions.append("cr.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("mill_id"):
		conditions.append("cr.mill_id = %(mill_id)s")
		params["mill_id"] = filters["mill_id"]
	where = " AND ".join(conditions)
	return frappe.db.sql(
		f"""
		SELECT cr.crashid, cr.crdate, cr.mill_id, cr.location_id,
			'INPUT' AS line_type, inp.storeid, inp.critem AS itemcode,
			cr_item.itemname AS item_name, inp.crbagid, cr_bag.itemname AS bag_name,
			inp.bagqty, inp.bagweight, inp.total_weight AS weight, inp.bagdust,
			inp.ref_weight, inp.dip, inp.prod_1, inp.prod_2, inp.rate, NULL AS proditem,
			NULL AS proditem_name
		FROM `tabCrash Refine Input` inp
		INNER JOIN `tabCrashing Refine` cr ON cr.name = inp.parent
		LEFT JOIN `tabItem Setup` cr_item ON cr_item.name = inp.critem
		LEFT JOIN `tabItem Setup` cr_bag ON cr_bag.name = inp.crbagid
		WHERE {where}
		UNION ALL
		SELECT cr.crashid, cr.crdate, cr.mill_id, cr.location_id,
			'OUTPUT' AS line_type, outl.storeid, outl.proditem AS itemcode,
			pr_item.itemname AS item_name, NULL AS crbagid, NULL AS bag_name,
			NULL AS bagqty, NULL AS bagweight, outl.weight, NULL AS bagdust,
			NULL AS ref_weight, NULL AS dip, NULL AS prod_1, NULL AS prod_2,
			outl.rate, outl.proditem, pr_item.itemname AS proditem_name
		FROM `tabCrash Refine Output` outl
		INNER JOIN `tabCrashing Refine` cr ON cr.name = outl.parent
		LEFT JOIN `tabItem Setup` pr_item ON pr_item.name = outl.proditem
		WHERE {where}
		ORDER BY crdate, crashid, line_type, itemcode
		""",
		params,
		as_dict=True,
	)


_UNSUBMIT_STOCK_SOURCES = (
	("In Out Gate Pass", "gatepassno", "gpdate"),
	("Opening Stock", "sopenid", "opendate"),
	("Closing Stock", "sopenid", "opendate"),
	("Stock Adjustment", "stkadjid", "sadate"),
	("Stock Transfer Note", "transferno", "tdate"),
	("Crashing Refine", "crashid", "crdate"),
)


def _unsubmit_doc_conditions(filters: dict, alias: str, date_field: str) -> tuple[list[str], dict]:
	conditions = [f"{alias}.docstatus = 0"]
	params: dict = {}
	if filters.get("location_id"):
		conditions.append(f"{alias}.location_id = %(location_id)s")
		params["location_id"] = filters["location_id"]
	if filters.get("from_date"):
		conditions.append(f"{alias}.{date_field} >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append(f"{alias}.{date_field} <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	return conditions, params


def get_unsubmit_stock_rows(filters: dict | None = None) -> list[dict]:
	"""Oracle UnSubmit_Stock.rep — draft stock documents item-wise."""
	filters = normalize_report_dates(filters or {})
	clauses: list[str] = []
	params: dict = {}

	def _append(sql: str, alias: str, date_field: str) -> None:
		conditions, part_params = _unsubmit_doc_conditions(filters, alias, date_field)
		clauses.append(sql.format(where=" AND ".join(conditions)))
		params.update(part_params)

	_append(
		"""
		SELECT gp.gpdate AS tdate, gp.location_id, gp.doctypeid AS doctype,
			CAST(gp.gatepassno AS CHAR) AS documentid, gp.itemcode, item.itemname AS item_name,
			d.storeid, store.description AS store_name, gp.partyid, party.party_name,
			COALESCE(d.netweight, d.truckqty, 0) AS qty, gp.posted
		FROM `tabIn Out Gate Pass` gp
		INNER JOIN `tabGate Pass Detail` d ON d.parent = gp.name
		LEFT JOIN `tabItem Setup` item ON item.name = gp.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		LEFT JOIN `tabParty` party ON party.name = gp.partyid
		WHERE {where}
		""",
		"gp",
		"gpdate",
	)
	_append(
		"""
		SELECT os.opendate AS tdate, os.location_id, os.doctypeid AS doctype,
			CAST(os.sopenid AS CHAR) AS documentid, d.itemcode, item.itemname AS item_name,
			d.storeid, store.description AS store_name, d.partyid, party.party_name,
			COALESCE(d.opening_stock, 0) AS qty, os.posted
		FROM `tabOpening Stock` os
		INNER JOIN `tabOpening Stock Detail` d ON d.parent = os.name
		LEFT JOIN `tabItem Setup` item ON item.name = d.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		LEFT JOIN `tabParty` party ON party.name = d.partyid
		WHERE {where}
		""",
		"os",
		"opendate",
	)
	_append(
		"""
		SELECT cs.opendate AS tdate, cs.location_id, cs.doctypeid AS doctype,
			CAST(cs.sopenid AS CHAR) AS documentid, d.itemcode, item.itemname AS item_name,
			d.storeid, store.description AS store_name, d.partyid, party.party_name,
			COALESCE(d.closing_stock, 0) AS qty, cs.posted
		FROM `tabClosing Stock` cs
		INNER JOIN `tabOpening Stock Detail` d ON d.parent = cs.name
		LEFT JOIN `tabItem Setup` item ON item.name = d.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		LEFT JOIN `tabParty` party ON party.name = d.partyid
		WHERE {where}
		""",
		"cs",
		"opendate",
	)
	_append(
		"""
		SELECT sa.sadate AS tdate, sa.location_id, sa.doctypeid AS doctype,
			CAST(sa.stkadjid AS CHAR) AS documentid, d.itemcode, item.itemname AS item_name,
			d.storeid, store.description AS store_name, d.partyid, party.party_name,
			COALESCE(d.inc_stock, d.dec_stock, 0) AS qty, sa.posted
		FROM `tabStock Adjustment` sa
		INNER JOIN `tabStock Adjustment Detail` d ON d.parent = sa.name
		LEFT JOIN `tabItem Setup` item ON item.name = d.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = d.storeid
		LEFT JOIN `tabParty` party ON party.name = d.partyid
		WHERE {where}
		""",
		"sa",
		"sadate",
	)
	_append(
		"""
		SELECT st.tdate AS tdate, st.location_id, st.doctypeid AS doctype,
			CAST(st.transferno AS CHAR) AS documentid, st.itemcode, item.itemname AS item_name,
			st.fromstoreid AS storeid, store.description AS store_name, st.partyid, party.party_name,
			COALESCE(d.netweight, d.truckqty, 0) AS qty, st.posted
		FROM `tabStock Transfer Note` st
		INNER JOIN `tabStock Transfer Detail` d ON d.parent = st.name
		LEFT JOIN `tabItem Setup` item ON item.name = st.itemcode
		LEFT JOIN `tabStore Setup` store ON store.name = st.fromstoreid
		LEFT JOIN `tabParty` party ON party.name = st.partyid
		WHERE {where}
		""",
		"st",
		"tdate",
	)
	_append(
		"""
		SELECT cr.crdate AS tdate, cr.location_id, cr.doctypeid AS doctype,
			CAST(cr.crashid AS CHAR) AS documentid, ci.critem AS itemcode, item.itemname AS item_name,
			ci.storeid, store.description AS store_name, NULL AS partyid, NULL AS party_name,
			COALESCE(ci.total_weight, 0) AS qty, cr.posted
		FROM `tabCrashing Refine` cr
		INNER JOIN `tabCrash Refine Input` ci ON ci.parent = cr.name
		LEFT JOIN `tabItem Setup` item ON item.name = ci.critem
		LEFT JOIN `tabStore Setup` store ON store.name = ci.storeid
		WHERE {where}
		""",
		"cr",
		"crdate",
	)
	_append(
		"""
		SELECT cr.crdate AS tdate, cr.location_id, cr.doctypeid AS doctype,
			CAST(cr.crashid AS CHAR) AS documentid, co.proditem AS itemcode, item.itemname AS item_name,
			co.storeid, store.description AS store_name, NULL AS partyid, NULL AS party_name,
			COALESCE(co.weight, 0) AS qty, cr.posted
		FROM `tabCrashing Refine` cr
		INNER JOIN `tabCrash Refine Output` co ON co.parent = cr.name
		LEFT JOIN `tabItem Setup` item ON item.name = co.proditem
		LEFT JOIN `tabStore Setup` store ON store.name = co.storeid
		WHERE {where}
		""",
		"cr",
		"crdate",
	)

	if not clauses:
		return []

	rows = frappe.db.sql(" UNION ALL ".join(clauses) + " ORDER BY tdate, doctype, documentid", params, as_dict=True)
	if filters.get("itemcode"):
		rows = [row for row in rows if row.get("itemcode") == filters["itemcode"]]
	if filters.get("storeid"):
		rows = [row for row in rows if row.get("storeid") == filters["storeid"]]
	return rows
