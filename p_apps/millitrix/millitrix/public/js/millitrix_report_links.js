// Copyright (c) 2026, Millitrix and contributors
// Query report drill-down — open forms from register rows.

frappe.provide("millitrix.report_links");

millitrix.report_links.LINK_FIELDS = {
	partyid: "Party",
	supplierid: "Party",
	customerid: "Party",
	brokerid: "Party",
	itemcode: "Item Setup",
	accid: "Chart of Accounting",
	location_id: "Location",
	storeid: "Store Setup",
	tostoreid: "Store Setup",
	empno: "Employee Setup",
};

millitrix.report_links.DOC_FIELDS = {
	purchinvno: "Purchase Invoice",
	salesinvno: "Sales Invoice",
	ponumber: "Purchase Order",
	sonumber: "Sales Order",
	purchretno: "Purchase Return",
	salesretno: "Sales Return",
	gatepassno: "In Out Gate Pass",
	cnbvno: "Payment Voucher",
};

millitrix.report_links.PNR_DOCTYPES = new Set([
	"Purchase Invoice Payment",
	"Sales Invoice Receipt",
	"Broker Invoice Payment",
	"Advance Payment",
	"Advance Receipt",
	"Payable Discount Note",
	"Receivable Discount Note",
]);

millitrix.report_links.form_route = (fieldname, value, row) => {
	if (value === null || value === undefined || value === "") {
		return null;
	}
	const text = String(value).trim();
	if (!text) {
		return null;
	}

	if (millitrix.report_links.LINK_FIELDS[fieldname]) {
		return [millitrix.report_links.LINK_FIELDS[fieldname], text];
	}

	const doctype = millitrix.report_links.DOC_FIELDS[fieldname];
	if (doctype) {
		if (fieldname === "cnbvno") {
			const mode = String(row?.vouchmode || "").toUpperCase();
			const dt = mode.startsWith("R") ? "Receipt Voucher" : "Payment Voucher";
			return [dt, text];
		}
		return [doctype, text];
	}

	if (fieldname === "pnrno") {
		const dt = row?.doctypeid;
		if (dt && millitrix.report_links.PNR_DOCTYPES.has(dt)) {
			return [dt, text];
		}
		return ["Purchase Invoice Payment", text];
	}

	if (fieldname === "documentid" && row?.doctypeid) {
		return [row.doctypeid, text];
	}

	if (fieldname === "voucherno") {
		return ["Voucher Transaction", text];
	}

	return null;
};

millitrix.report_links.is_html = (value) =>
	typeof value === "string" && /<a[\s>]/i.test(value);

millitrix.report_links.wrap_formatter = (report_name) => {
	const settings = (frappe.query_reports[report_name] =
		frappe.query_reports[report_name] || {});
	if (settings.__millitrix_drilldown) {
		return;
	}
	const orig = settings.formatter;
	settings.formatter = function (value, row, column, data, default_formatter) {
		const formatted = orig
			? orig(value, row, column, data, default_formatter)
			: default_formatter(value, row, column, data);

		if (!column?.fieldname || formatted === undefined || formatted === null) {
			return formatted;
		}

		// Link columns: Frappe already returns clickable HTML — do not double-wrap.
		if (column.fieldtype === "Link" || millitrix.report_links.is_html(formatted)) {
			return formatted;
		}

		const route = millitrix.report_links.form_route(column.fieldname, value, data || row);
		if (!route) {
			return formatted;
		}

		const [doctype, name] = route;
		const href = frappe.utils.get_form_link(doctype, name);
		const label = frappe.utils.escape_html(String(formatted ?? value ?? ""));
		return `<a class="millitrix-report-link" href="${href}">${label}</a>`;
	};
	settings.__millitrix_drilldown = true;
};

millitrix.report_links.enhance_datatable = (query_report) => {
	if (!query_report?.report_settings || query_report.report_settings.__millitrix_datatable) {
		return;
	}
	const orig = query_report.report_settings.get_datatable_options;
	query_report.report_settings.get_datatable_options = function (options) {
		const out = orig ? orig(options) : { ...options };
		out.layout = out.layout || "fixed";
		out.cellHeight = out.cellHeight || 33;
		return out;
	};
	query_report.report_settings.__millitrix_datatable = true;
};

millitrix.report_links.patch_query_report = function () {
	if (!frappe.views?.QueryReport) {
		return;
	}
	const proto = frappe.views.QueryReport.prototype;
	if (proto.__millitrix_drilldown_patched) {
		return;
	}
	proto.__millitrix_drilldown_patched = true;

	const orig_load = proto.load_report;
	proto.load_report = function () {
		const result = orig_load.apply(this, arguments);
		const finish = () => {
			if (this.report_doc?.module === "Millitrix ERP") {
				millitrix.report_links.wrap_formatter(this.report_name);
				millitrix.report_links.enhance_datatable(this);
			}
		};
		if (result?.then) {
			return result.then(finish);
		}
		finish();
		return result;
	};

	const orig_prepare = proto.prepare_columns;
	if (orig_prepare) {
		proto.prepare_columns = function (columns) {
			const prepared = orig_prepare.call(this, columns);
			if (this.report_doc?.module !== "Millitrix ERP") {
				return prepared;
			}
			return prepared.map((col) => {
				if (col.fieldtype === "Link" || col.fieldtype === "Dynamic Link") {
					col.width = Math.max(parseInt(col.width) || 0, 120);
				}
				if (col.fieldname === "status" || col.fieldname === "posted") {
					col.width = Math.max(parseInt(col.width) || 0, 100);
				}
				if (col.fieldtype === "Date") {
					col.width = Math.max(parseInt(col.width) || 0, 110);
				}
				return col;
			});
		};
	}
};

millitrix.report_links.patch_query_report();
$(document).on("app_ready", millitrix.report_links.patch_query_report);
