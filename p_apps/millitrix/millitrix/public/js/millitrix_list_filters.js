// Copyright (c) 2026, Millitrix and contributors
// Millitrix lists: sidebar collapsed, no top title filter bar, standard Frappe Filter button.

frappe.provide("millitrix.list_filters");

millitrix.list_filters._registered = new Set();
millitrix.list_filters.TOTAL_FIELDS = 10;

/** Hidden when Frappe Status indicator (docstatus) already shown. */
millitrix.list_filters.HIDE_WHEN_STATUS_INDICATOR = new Set(["posted"]);

millitrix.list_filters.BASE_SETTINGS = {
	hide_name_filter: true,
	hide_page_form: true,
	hide_name_column: true,
};

millitrix.list_filters.ROUTE_FILTER_KEYS = {
	"Purchase Invoice": [
		"millitrix_supplierid",
		"millitrix_itemcode",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Crashing Refine": [
		"millitrix_mill_id",
		"millitrix_primary_item",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"In Out Gate Pass": [
		"millitrix_gptype",
		"millitrix_partyid",
		"millitrix_itemcode",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"PaySlip": ["millitrix_from_date", "millitrix_to_date", "millitrix_paymonth"],
	"PO Cancellation": [
		"millitrix_partyid",
		"millitrix_primary_item",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Purchase Return": [
		"millitrix_supplierid",
		"millitrix_itemcode",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Purchase Order": [
		"millitrix_supplierid",
		"millitrix_itemcode",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Purchase Other Bill": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Sales Invoice": [
		"millitrix_customerid",
		"millitrix_itemcode",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Sales Order": [
		"millitrix_customerid",
		"millitrix_itemcode",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Sales Other Bill": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Sales Return": [
		"millitrix_customerid",
		"millitrix_itemcode",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Sales Return Other Bill": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"SO Cancellation": [
		"millitrix_partyid",
		"millitrix_primary_item",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Stock Adjustment": [
		"millitrix_primary_item",
		"millitrix_primary_store",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Opening Stock": [
		"millitrix_primary_item",
		"millitrix_primary_store",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Closing Stock": [
		"millitrix_primary_item",
		"millitrix_primary_store",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Stock Transfer Note": [
		"millitrix_itemcode",
		"millitrix_fromstoreid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Un-Submit Documents": [
		"millitrix_usdoctype",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Paid Advance Adjustment": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Received Advance Adjustment": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Chart of Accounting": [
		"millitrix_description",
		"millitrix_nature",
		"millitrix_transflag",
	],
	"Closing and Adjustment Entries": [
		"millitrix_primary_acc",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Payment Voucher": [
		"millitrix_primary_acc",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Receipt Voucher": [
		"millitrix_primary_acc",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Expense Voucher": [
		"millitrix_primary_acc",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Party Payment Voucher": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Party Receipt Voucher": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Employee Payment Voucher": [
		"millitrix_primary_employee",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Employee Receipt Voucher": [
		"millitrix_primary_employee",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Accounts Opening": [
		"millitrix_primary_acc",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"GL Statements": [
		"millitrix_statement",
		"millitrix_description",
		"millitrix_active",
	],
	"Advance Payment": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Advance Receipt": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Payable Discount Note": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Receivable Discount Note": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Party Gross Margin": [
		"millitrix_partyid",
		"millitrix_itemcode",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Purchase Invoice Payment": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Sales Invoice Receipt": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Broker Invoice Payment": [
		"millitrix_partyid",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Voucher Transaction": [
		"millitrix_primary_acc",
		"millitrix_from_date",
		"millitrix_to_date",
	],
	"Item Price List": [
		"millitrix_mill_id",
		"millitrix_itemcode",
		"millitrix_from_date",
		"millitrix_to_date",
	],
};

millitrix.list_filters.is_millitrix_list = (doctype) => {
	try {
		return frappe.get_meta(doctype)?.module === "Millitrix ERP";
	} catch (e) {
		return false;
	}
};

millitrix.list_filters.apply_list_settings = (listview) => {
	Object.assign(listview, millitrix.list_filters.BASE_SETTINGS);
	if (listview.page?.page_form) {
		listview.page.page_form.hide();
	}
};

millitrix.list_filters.collapse_sidebar = (listview) => {
	localStorage.setItem("show_sidebar", "false");
	document.body.classList.add("no-list-sidebar");
	if (listview?.show_or_hide_sidebar) {
		listview.show_or_hide_sidebar();
	}
};

millitrix.list_filters.apply_route_filters = (listview) => {
	const route_keys = millitrix.list_filters.ROUTE_FILTER_KEYS[listview.doctype] || [];
	const pending = [];
	route_keys.forEach((key) => {
		const value = frappe.route_options?.[key];
		if (value === undefined || value === null || value === "") {
			return;
		}
		pending.push([listview.doctype, key.replace(/^millitrix_/, ""), "=", value, false]);
		delete frappe.route_options[key];
	});
	if (pending.length && listview.filter_area) {
		listview.filter_area.add(pending);
	}
};

millitrix.list_filters.ensure_total_fields = (listview) => {
	if (!millitrix.list_filters.is_millitrix_list(listview.doctype)) {
		return;
	}
	listview.list_view_settings = listview.list_view_settings || {};
	const want = millitrix.list_filters.TOTAL_FIELDS;
	if ((listview.list_view_settings.total_fields || 0) < want) {
		listview.list_view_settings.total_fields = want;
	}
};

millitrix.list_filters.filter_list_columns = (listview) => {
	if (!millitrix.list_filters.is_millitrix_list(listview.doctype)) {
		return;
	}
	if (!frappe.has_indicator(listview.doctype)) {
		return;
	}
	listview.columns = (listview.columns || []).filter((col) => {
		if (col.type !== "Field" || !col.df?.fieldname) {
			return true;
		}
		return !millitrix.list_filters.HIDE_WHEN_STATUS_INDICATOR.has(col.df.fieldname);
	});
};

millitrix.list_filters.register = (doctype) => {
	if (millitrix.list_filters._registered.has(doctype)) {
		return;
	}
	millitrix.list_filters._registered.add(doctype);

	if (millitrix.premium_lists?.register) {
		millitrix.premium_lists.register(doctype);
	}

	const existing = frappe.listview_settings[doctype] || {};
	const prev_onload = existing.onload;
	const prev_refresh = existing.refresh;

	frappe.listview_settings[doctype] = {
		...existing,
		...millitrix.list_filters.BASE_SETTINGS,
		onload(listview) {
			millitrix.list_filters.apply_list_settings(listview);
			millitrix.list_filters.ensure_total_fields(listview);
			millitrix.list_filters.collapse_sidebar(listview);
			if (typeof prev_onload === "function") {
				prev_onload(listview);
			}
			millitrix.list_filters.apply_route_filters(listview);
		},
		refresh(listview) {
			if (typeof prev_refresh === "function") {
				prev_refresh(listview);
			}
			millitrix.list_filters.apply_list_settings(listview);
			millitrix.list_filters.collapse_sidebar(listview);
		},
	};
};

millitrix.list_filters.register_all_millitrix = () => {
	(frappe.boot.user.can_read || []).forEach((doctype) => {
		frappe.model.with_doctype(doctype, () => {
			if (millitrix.list_filters.is_millitrix_list(doctype)) {
				millitrix.list_filters.register(doctype);
			}
		});
	});
};

if (!millitrix.list_filters._setup_view_patched) {
	millitrix.list_filters._setup_view_patched = true;
	const _orig_setup_view = frappe.views.ListView.prototype.setup_view;
	frappe.views.ListView.prototype.setup_view = function () {
		millitrix.list_filters.ensure_total_fields(this);
		if (millitrix.list_filters.is_millitrix_list(this.doctype)) {
			millitrix.list_filters.apply_list_settings(this);
		}
		return _orig_setup_view.call(this);
	};

	const _orig_get_list_view_settings = frappe.views.BaseList.prototype.get_list_view_settings;
	frappe.views.BaseList.prototype.get_list_view_settings = function () {
		return _orig_get_list_view_settings.call(this).then(() => {
			if (millitrix.list_filters.is_millitrix_list(this.doctype)) {
				millitrix.list_filters.ensure_total_fields(this);
			}
		});
	};

	const _orig_refresh_columns = frappe.views.ListView.prototype.refresh_columns;
	frappe.views.ListView.prototype.refresh_columns = function (meta, list_view_settings) {
		_orig_refresh_columns.call(this, meta, list_view_settings);
		if (millitrix.list_filters.is_millitrix_list(this.doctype)) {
			millitrix.premium_lists?.apply_meta?.(this);
			millitrix.list_filters.ensure_total_fields(this);
			this.setup_columns();
			this.render_header();
		}
	};

	const _orig_setup_columns = frappe.views.ListView.prototype.setup_columns;
	frappe.views.ListView.prototype.setup_columns = function () {
		if (millitrix.list_filters.is_millitrix_list(this.doctype)) {
			millitrix.premium_lists?.apply_meta?.(this);
			millitrix.list_filters.ensure_total_fields(this);
		}
		_orig_setup_columns.call(this);
		millitrix.list_filters.filter_list_columns(this);
	};

	const _orig_setup_page = frappe.views.BaseList.prototype.setup_page;
	frappe.views.BaseList.prototype.setup_page = function () {
		const out = _orig_setup_page.call(this);
		if (millitrix.list_filters.is_millitrix_list(this.doctype)) {
			millitrix.list_filters.apply_list_settings(this);
		}
		return out;
	};
}

millitrix.list_filters.register_all_millitrix();

frappe.router.on("change", () => {
	const route = frappe.get_route();
	if (route[0] === "List" && route[1]) {
		frappe.model.with_doctype(route[1], () => {
			if (millitrix.list_filters.is_millitrix_list(route[1])) {
				millitrix.list_filters.register(route[1]);
				millitrix.list_filters.collapse_sidebar();
			}
		});
	}
});
