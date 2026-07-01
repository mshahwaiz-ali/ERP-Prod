// Premium list views for all Millitrix transaction forms.
// Loaded via app_include_js — works without bench build of doctype *_list.js bundles.
// Copyright (c) 2026, Millitrix and contributors

frappe.provide("millitrix.premium_lists");

/** Mirrors millitrix.utils.list_view_plan — keep in sync. */
millitrix.premium_lists.CONFIG = {
	"Crashing Refine": {
		columns: ["crdate", "mill_id", "primary_item", "primary_output", "input_weight", "crashid"],
		title: "primary_item",
		fallback: "crashid",
		date: "crdate",
		add_fields: [
			"crashid",
			"crdate",
			"mill_id",
			"primary_item",
			"primary_output",
			"input_weight",
			"docstatus",
		],
		session_mill: true,
	},
	"Purchase Invoice": {
		columns: ["invdate", "itemcode", "supplierid", "brokerid", "kantatype", "amount", "payable", "purchinvno"],
		title: "itemcode",
		fallback: "purchinvno",
		date: "invdate",
		add_fields: [
			"purchinvno",
			"invdate",
			"itemcode",
			"supplierid",
			"brokerid",
			"kantatype",
			"amount",
			"payable",
			"docstatus",
		],
	},
	"Sales Invoice": {
		columns: ["invdate", "itemcode", "customerid", "brokerid", "kantatype", "amount", "receivable", "salesinvno"],
		title: "itemcode",
		fallback: "salesinvno",
		date: "invdate",
		add_fields: [
			"salesinvno",
			"invdate",
			"itemcode",
			"customerid",
			"brokerid",
			"kantatype",
			"amount",
			"receivable",
			"docstatus",
		],
	},
	"Sales Order": {
		columns: ["sodate", "itemcode", "customerid", "brokerid", "rate", "amount", "status", "sonumber"],
		title: "itemcode",
		fallback: "sonumber",
		date: "sodate",
		add_fields: [
			"sonumber",
			"sodate",
			"sotype",
			"itemcode",
			"customerid",
			"brokerid",
			"rate",
			"amount",
			"status",
			"docstatus",
		],
	},
	"In Out Gate Pass": {
		columns: ["gpdate", "gptype", "itemcode", "partyid", "gatepassno"],
		title: "itemcode",
		fallback: "gatepassno",
		date: "gpdate",
		add_fields: ["gatepassno", "gpdate", "gptype", "partyid", "itemcode", "docstatus"],
	},
	"PaySlip": {
		columns: ["paymonth", "pdate", "primary_employee", "employee_count", "total_salary", "remarks", "pslipid"],
		title: "paymonth",
		fallback: "pslipid",
		date: "pdate",
		add_fields: [
			"pslipid",
			"pdate",
			"paymonth",
			"primary_employee",
			"employee_count",
			"total_salary",
			"remarks",
			"docstatus",
		],
	},
	"PO Cancellation": {
		columns: ["candate", "partyid", "primary_item", "total_cancel_qty", "line_count", "remarks", "pocid"],
		title: "partyid",
		fallback: "pocid",
		date: "candate",
		add_fields: [
			"pocid",
			"candate",
			"partyid",
			"primary_item",
			"total_cancel_qty",
			"line_count",
			"remarks",
			"docstatus",
		],
	},
	"Purchase Return": {
		columns: ["retdate", "itemcode", "supplierid", "brokerid", "purchinvno", "amount", "purchretno"],
		title: "itemcode",
		fallback: "purchretno",
		date: "retdate",
		add_fields: [
			"purchretno",
			"retdate",
			"itemcode",
			"supplierid",
			"brokerid",
			"purchinvno",
			"amount",
			"docstatus",
		],
	},
	"Purchase Return Other Bill": {
		columns: ["brdate", "partyid", "pbillno", "amount", "prbillno"],
		title: "partyid",
		fallback: "prbillno",
		date: "brdate",
		add_fields: ["prbillno", "brdate", "partyid", "pbillno", "amount", "docstatus"],
	},
	"Sales Return": {
		columns: ["retdate", "itemcode", "customerid", "brokerid", "salesinvno", "amount", "salesretno"],
		title: "itemcode",
		fallback: "salesretno",
		date: "retdate",
		add_fields: [
			"salesretno",
			"retdate",
			"itemcode",
			"customerid",
			"brokerid",
			"salesinvno",
			"amount",
			"docstatus",
		],
	},
	"Sales Return Other Bill": {
		columns: ["brdate", "partyid", "sbillno", "amount", "srbillno"],
		title: "partyid",
		fallback: "srbillno",
		date: "brdate",
		add_fields: ["srbillno", "brdate", "partyid", "sbillno", "amount", "docstatus"],
	},
	"Sales Other Bill": {
		columns: ["billdate", "partyid", "amount", "sbillno"],
		title: "partyid",
		fallback: "sbillno",
		date: "billdate",
		add_fields: ["sbillno", "billdate", "partyid", "amount", "docstatus"],
	},
	"SO Cancellation": {
		columns: ["candate", "partyid", "primary_item", "total_cancel_qty", "line_count", "remarks", "socid"],
		title: "partyid",
		fallback: "socid",
		date: "candate",
		add_fields: [
			"socid",
			"candate",
			"partyid",
			"primary_item",
			"total_cancel_qty",
			"line_count",
			"remarks",
			"docstatus",
		],
	},
	"Stock Adjustment": {
		columns: ["sadate", "primary_item", "primary_store", "line_count", "total_amount", "remarks", "stkadjid"],
		title: "primary_item",
		fallback: "stkadjid",
		date: "sadate",
		add_fields: [
			"stkadjid",
			"sadate",
			"primary_item",
			"primary_store",
			"line_count",
			"total_amount",
			"remarks",
			"docstatus",
		],
	},
	"Opening Stock": {
		columns: ["opendate", "primary_item", "primary_store", "line_count", "total_stock_value", "sopenid"],
		title: "primary_item",
		fallback: "sopenid",
		date: "opendate",
		add_fields: [
			"sopenid",
			"opendate",
			"primary_item",
			"primary_store",
			"line_count",
			"total_stock_value",
			"docstatus",
		],
	},
	"Closing Stock": {
		columns: ["opendate", "primary_item", "primary_store", "line_count", "total_stock", "remarks", "sopenid"],
		title: "primary_item",
		fallback: "sopenid",
		date: "opendate",
		add_fields: [
			"sopenid",
			"opendate",
			"primary_item",
			"primary_store",
			"line_count",
			"total_stock",
			"remarks",
			"docstatus",
		],
	},
	"Stock Transfer Note": {
		columns: [
			"tdate",
			"itemcode",
			"fromstoreid",
			"primary_tostore",
			"line_count",
			"total_netweight",
			"transferno",
		],
		title: "itemcode",
		fallback: "transferno",
		date: "tdate",
		add_fields: [
			"transferno",
			"tdate",
			"itemcode",
			"fromstoreid",
			"primary_tostore",
			"line_count",
			"total_netweight",
			"kantatype",
			"docstatus",
		],
	},
	"Un-Submit Documents": {
		columns: ["usdate", "usdoctype", "documentid", "doc_description", "remarks", "us_id"],
		title: "documentid",
		fallback: "us_id",
		date: "usdate",
		add_fields: [
			"us_id",
			"usdate",
			"usdoctype",
			"target_doctype",
			"documentid",
			"doc_description",
			"remarks",
			"docstatus",
		],
	},
	"Menu": {
		columns: ["description", "parentid", "sortby", "menuid"],
		title: "description",
		add_fields: ["description", "parentid", "sortby", "menuid"],
	},
	"Module": {
		columns: ["module", "menuid", "nature", "moduletype", "runtimefile", "moduleid"],
		title: "module",
		add_fields: ["module", "menuid", "moduletype", "nature", "runtimefile", "doctypeid", "moduleid"],
	},
	"Location": {
		columns: ["description", "short_name", "company_id", "cityid", "phno1", "address", "location_id"],
		title: "description",
		fallback: "location_id",
		add_fields: [
			"description",
			"short_name",
			"company_id",
			"cityid",
			"phno1",
			"address",
			"location_id",
		],
	},
	"Mill Information": {
		columns: ["description", "short_name", "phno1", "address", "company_id"],
		title: "description",
		fallback: "company_id",
		add_fields: ["description", "short_name", "phno1", "address", "company_id"],
	},
	"City Setup": {
		columns: ["cityname", "cityid"],
		title: "cityname",
		fallback: "cityid",
		add_fields: ["cityname", "cityid"],
	},
	"Departments": {
		columns: ["description", "deptid"],
		title: "description",
		fallback: "deptid",
		add_fields: ["description", "deptid"],
	},
	"Designation": {
		columns: ["description", "desigid"],
		title: "description",
		fallback: "desigid",
		add_fields: ["description", "desigid"],
	},
	"Party": {
		columns: ["party_name", "cityid", "mobileno", "phno1", "creditlimit", "pcat_id", "partyid"],
		title: "party_name",
		fallback: "partyid",
		add_fields: [
			"party_name",
			"cityid",
			"city_name",
			"mobileno",
			"phno1",
			"creditlimit",
			"pcat_id",
			"partyid",
		],
	},
	"Bank": {
		columns: ["bankname", "shortname", "branch_count", "account_count", "bankid"],
		title: "bankname",
		fallback: "bankid",
		add_fields: ["bankname", "shortname", "branch_count", "account_count", "bankid"],
	},
	"Employee Setup": {
		columns: ["ename", "location_id", "deptid", "desigid", "ecatid", "salary", "phno1", "empno"],
		title: "ename",
		fallback: "empno",
		add_fields: [
			"ename",
			"location_id",
			"deptid",
			"desigid",
			"ecatid",
			"salary",
			"phno1",
			"empno",
		],
	},
	"Store Setup": {
		columns: ["store_name", "trans_allow", "storetypeid", "location_id", "store_address", "storeid"],
		title: "store_name",
		fallback: "storeid",
		add_fields: [
			"store_name",
			"trans_allow",
			"storetypeid",
			"location_id",
			"store_address",
			"storeid",
		],
	},
	"Store Types": {
		columns: ["description", "storetypeid"],
		title: "description",
		fallback: "storetypeid",
		add_fields: ["description", "storetypeid"],
	},
	"Item Class": {
		columns: ["description", "iclassid"],
		title: "description",
		fallback: "iclassid",
		add_fields: ["description", "iclassid"],
	},
	"Item Setup": {
		columns: ["itemname", "iclassid", "mundtype", "stockable", "itemcode"],
		title: "itemname",
		fallback: "itemcode",
		add_fields: ["itemname", "iclassid", "mundtype", "stockable", "itemcode", "class_name"],
	},
	"Item Price List": {
		columns: ["ipdate", "location_id", "itemcode", "iclassid", "purchrate", "salesrate", "westage"],
		title: "itemcode",
		date: "ipdate",
		session_mill: true,
		add_fields: [
			"ipdate",
			"location_id",
			"itemcode",
			"item_name",
			"iclassid",
			"purchrate",
			"salesrate",
			"westage",
			"bagweight",
		],
	},
	"Other Contact Setup": {
		columns: ["name", "cityid", "pcat_id", "mobileno", "phno1", "address", "contactid"],
		title: "name",
		fallback: "contactid",
		add_fields: ["name", "cityid", "city_name", "pcat_id", "mobileno", "phno1", "address", "contactid"],
	},
	"Party Category": {
		columns: ["description", "accid", "account_description", "pcat_id"],
		title: "description",
		fallback: "pcat_id",
		add_fields: ["description", "accid", "account_description", "pcat_id"],
	},
	"Employee Category": {
		columns: ["description", "accid", "account_description", "payslip", "ecatid"],
		title: "description",
		fallback: "ecatid",
		add_fields: ["description", "accid", "account_description", "payslip", "ecatid"],
	},
	"Transaction Category": {
		columns: ["description", "accid", "account_description", "tcat_id"],
		title: "description",
		fallback: "tcat_id",
		add_fields: ["description", "accid", "account_description", "tcat_id"],
	},
	"Transaction List": {
		columns: ["description", "tcat_id", "category_description", "trans_id"],
		title: "description",
		fallback: "trans_id",
		add_fields: ["description", "tcat_id", "category_description", "trans_id"],
	},
	"User Rights": {
		columns: ["username", "erp_user", "location_id", "empno", "employee_name", "activestatus", "userid"],
		title: "username",
		fallback: "userid",
		add_fields: ["username", "erp_user", "location_id", "empno", "employee_name", "activestatus", "userid"],
	},
	"Paid Advance Adjustment": {
		columns: ["adjdate", "partyid", "amount", "line_count", "narration", "adjid"],
		title: "partyid",
		fallback: "adjid",
		date: "adjdate",
		add_fields: [
			"adjid",
			"adjdate",
			"partyid",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Received Advance Adjustment": {
		columns: ["adjdate", "partyid", "amount", "line_count", "narration", "adjid"],
		title: "partyid",
		fallback: "adjid",
		date: "adjdate",
		add_fields: [
			"adjid",
			"adjdate",
			"partyid",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Chart of Accounting": {
		columns: ["description", "nature", "chartlevel", "parentid", "transflag", "accid"],
		title: "description",
		fallback: "accid",
		add_fields: [
			"accid",
			"description",
			"nature",
			"chartlevel",
			"parentid",
			"transflag",
		],
	},
	"Closing and Adjustment Entries": {
		columns: [
			"vouchdate",
			"narration",
			"reference",
			"primary_acc",
			"line_count",
			"total_debit",
			"total_credit",
			"voucherno",
		],
		title: "narration",
		fallback: "voucherno",
		date: "vouchdate",
		add_fields: [
			"voucherno",
			"vouchdate",
			"narration",
			"reference",
			"primary_acc",
			"line_count",
			"total_debit",
			"total_credit",
			"docstatus",
		],
	},
	"Payment Voucher": {
		columns: ["vouchdate", "primary_acc", "paymode", "amount", "line_count", "narration", "cnbvno"],
		title: "amount",
		fallback: "cnbvno",
		date: "vouchdate",
		add_fields: [
			"cnbvno",
			"vouchdate",
			"primary_acc",
			"paymode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Receipt Voucher": {
		columns: ["vouchdate", "primary_acc", "paymode", "amount", "line_count", "narration", "cnbvno"],
		title: "amount",
		fallback: "cnbvno",
		date: "vouchdate",
		add_fields: [
			"cnbvno",
			"vouchdate",
			"primary_acc",
			"paymode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Expense Voucher": {
		columns: ["vouchdate", "primary_acc", "paymode", "amount", "line_count", "narration", "cnbvno"],
		title: "amount",
		fallback: "cnbvno",
		date: "vouchdate",
		add_fields: [
			"cnbvno",
			"vouchdate",
			"primary_acc",
			"paymode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Party Payment Voucher": {
		columns: ["vouchdate", "partyid", "paymode", "amount", "line_count", "narration", "cnbvno"],
		title: "partyid",
		fallback: "cnbvno",
		date: "vouchdate",
		add_fields: [
			"cnbvno",
			"vouchdate",
			"partyid",
			"paymode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Party Receipt Voucher": {
		columns: ["vouchdate", "partyid", "paymode", "amount", "line_count", "narration", "cnbvno"],
		title: "partyid",
		fallback: "cnbvno",
		date: "vouchdate",
		add_fields: [
			"cnbvno",
			"vouchdate",
			"partyid",
			"paymode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Employee Payment Voucher": {
		columns: [
			"vouchdate",
			"primary_employee",
			"paymode",
			"amount",
			"line_count",
			"narration",
			"empvno",
		],
		title: "primary_employee",
		fallback: "empvno",
		date: "vouchdate",
		add_fields: [
			"empvno",
			"vouchdate",
			"primary_employee",
			"paymode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Employee Receipt Voucher": {
		columns: [
			"vouchdate",
			"primary_employee",
			"paymode",
			"amount",
			"line_count",
			"narration",
			"empvno",
		],
		title: "primary_employee",
		fallback: "empvno",
		date: "vouchdate",
		add_fields: [
			"empvno",
			"vouchdate",
			"primary_employee",
			"paymode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Accounts Opening": {
		columns: [
			"opening_date",
			"primary_acc",
			"line_count",
			"total_debit",
			"total_credit",
			"glopenid",
		],
		title: "primary_acc",
		fallback: "glopenid",
		date: "opening_date",
		add_fields: [
			"glopenid",
			"opening_date",
			"primary_acc",
			"line_count",
			"total_debit",
			"total_credit",
			"docstatus",
		],
	},
	"GL Statements": {
		columns: [
			"statement",
			"description",
			"active",
			"operation",
			"line_count",
			"account_count",
			"statementid",
		],
		title: "description",
		fallback: "statementid",
		add_fields: [
			"statementid",
			"statement",
			"description",
			"active",
			"operation",
			"line_count",
			"account_count",
		],
	},
	"Advance Payment": {
		columns: ["pnrdate", "partyid", "pnrmode", "amount", "narration", "pnrno"],
		title: "partyid",
		fallback: "pnrno",
		date: "pnrdate",
		add_fields: [
			"pnrno",
			"pnrdate",
			"partyid",
			"pnrmode",
			"amount",
			"narration",
			"docstatus",
		],
	},
	"Advance Receipt": {
		columns: ["pnrdate", "partyid", "pnrmode", "amount", "narration", "pnrno"],
		title: "partyid",
		fallback: "pnrno",
		date: "pnrdate",
		add_fields: [
			"pnrno",
			"pnrdate",
			"partyid",
			"pnrmode",
			"amount",
			"narration",
			"docstatus",
		],
	},
	"Payable Discount Note": {
		columns: ["pnrdate", "partyid", "amount", "line_count", "narration", "pnrno"],
		title: "partyid",
		fallback: "pnrno",
		date: "pnrdate",
		add_fields: [
			"pnrno",
			"pnrdate",
			"partyid",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Receivable Discount Note": {
		columns: ["pnrdate", "partyid", "amount", "line_count", "narration", "pnrno"],
		title: "partyid",
		fallback: "pnrno",
		date: "pnrdate",
		add_fields: [
			"pnrno",
			"pnrdate",
			"partyid",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Party Gross Margin": {
		columns: [
			"pgdate",
			"partyid",
			"itemcode",
			"amount",
			"line_count",
			"pgmode",
			"narration",
			"pgmid",
		],
		title: "partyid",
		fallback: "pgmid",
		date: "pgdate",
		add_fields: [
			"pgmid",
			"pgdate",
			"partyid",
			"itemcode",
			"amount",
			"line_count",
			"pgmode",
			"narration",
			"docstatus",
		],
	},
	"Purchase Invoice Payment": {
		columns: ["pnrdate", "partyid", "pnrmode", "amount", "line_count", "narration", "pnrno"],
		title: "partyid",
		fallback: "pnrno",
		date: "pnrdate",
		add_fields: [
			"pnrno",
			"pnrdate",
			"partyid",
			"pnrmode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Sales Invoice Receipt": {
		columns: ["pnrdate", "partyid", "pnrmode", "amount", "line_count", "narration", "pnrno"],
		title: "partyid",
		fallback: "pnrno",
		date: "pnrdate",
		add_fields: [
			"pnrno",
			"pnrdate",
			"partyid",
			"pnrmode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Broker Invoice Payment": {
		columns: ["pnrdate", "partyid", "pnrmode", "amount", "line_count", "narration", "pnrno"],
		title: "partyid",
		fallback: "pnrno",
		date: "pnrdate",
		add_fields: [
			"pnrno",
			"pnrdate",
			"partyid",
			"pnrmode",
			"amount",
			"line_count",
			"narration",
			"docstatus",
		],
	},
	"Voucher Transaction": {
		columns: [
			"vouchdate",
			"narration",
			"reference",
			"primary_acc",
			"line_count",
			"total_debit",
			"total_credit",
			"voucherno",
		],
		title: "narration",
		fallback: "voucherno",
		date: "vouchdate",
		add_fields: [
			"voucherno",
			"vouchdate",
			"narration",
			"reference",
			"primary_acc",
			"line_count",
			"total_debit",
			"total_credit",
			"docstatus",
		],
	},
};

millitrix.premium_lists.get_config = (doctype) => millitrix.premium_lists.CONFIG[doctype];

millitrix.premium_lists.apply_meta = (listview) => {
	const cfg = millitrix.premium_lists.get_config(listview.doctype);
	if (!cfg || !listview.meta) {
		return;
	}
	if (cfg.title) {
		listview.meta.title_field = cfg.title;
	}
	(cfg.columns || []).forEach((fieldname) => {
		const df = frappe.meta.get_docfield(listview.doctype, fieldname);
		if (df) {
			df.in_list_view = 1;
		}
	});
};

millitrix.premium_lists.apply_month_filter = (listview, cfg) => {
	if (!cfg?.date || listview.filter_area?.filter_list?.length) {
		return Promise.resolve(false);
	}
	if (millitrix.list_view?.apply_month_date_filter) {
		return millitrix.list_view.apply_month_date_filter(listview, cfg.date);
	}
	return Promise.resolve(false);
};

millitrix.premium_lists.apply_session_mill = (listview) => {
	if (
		listview.doctype !== "Crashing Refine" ||
		listview._millitrix_cr_session_mill ||
		listview.filter_area?.filter_list?.length
	) {
		return Promise.resolve(false);
	}
	return frappe
		.xcall("millitrix.api.user_context.get_user_scope")
		.then((scope) => {
			const mill = scope?.location_id;
			if (!mill || listview.filter_area?.filter_list?.length) {
				return false;
			}
			listview._millitrix_cr_session_mill = true;
			return listview.filter_area
				.add([["Crashing Refine", "mill_id", "=", mill, false]])
				.then(() => true);
		})
		.catch(() => false);
};

millitrix.premium_lists.register = (doctype) => {
	const cfg = millitrix.premium_lists.get_config(doctype);
	if (!cfg) {
		return;
	}
	const existing = frappe.listview_settings[doctype] || {};
	if (existing._millitrix_premium_registered) {
		return;
	}
	const prev_onload = existing.onload;
	frappe.listview_settings[doctype] = {
		...existing,
		_millitrix_premium_registered: true,
		hide_name_filter: true,
		add_fields: cfg.add_fields || cfg.columns,
		onload(listview) {
			millitrix.premium_lists.apply_meta(listview);
			if (millitrix.list_view?.patch_subject_formatter && cfg.title) {
				millitrix.list_view.patch_subject_formatter(doctype, cfg.title, cfg.fallback);
			}
			if (typeof prev_onload === "function") {
				prev_onload(listview);
			}
			if (listview.filter_area?.filter_list?.length) {
				return;
			}
			if (cfg.session_mill) {
				millitrix.premium_lists.apply_session_mill(listview).then((applied) => {
					if (!applied) {
						millitrix.premium_lists.apply_month_filter(listview, cfg);
					}
				});
				return;
			}
			millitrix.premium_lists.apply_month_filter(listview, cfg);
		},
	};
};

millitrix.premium_lists.register_all = () => {
	Object.keys(millitrix.premium_lists.CONFIG).forEach((doctype) => {
		frappe.model.with_doctype(doctype, () => {
			millitrix.premium_lists.register(doctype);
		});
	});
};

millitrix.premium_lists.register_all();
