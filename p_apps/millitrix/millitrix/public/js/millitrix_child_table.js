// Copyright (c) 2026, Millitrix and contributors
//
// LOCKED — Millitrix child-table grid behaviour (all Millitrix ERP parent forms).
// 1. Columns from in_list_view + Configure Columns (gear); each column width 1; no 10-col cap
// 2. Horizontal scroll inside form width (millitrix-child-table-pack)
// 3. Footer Total row (column-aligned)
// 4. Live sums for sensible numeric fields (qty/amount/weight — not ids/rates)
// 5. Frappe gear/edit/modal/menus not clipped by scroll wrapper
// Scope: module === "Millitrix ERP" + istable child DocTypes only.

frappe.provide("millitrix");
frappe.provide("millitrix.child_table");

/** Frappe exposes read-only state as frm.read_only (boolean), not is_read_only(). */
millitrix.is_form_read_only = (frm) => Boolean(frm?.read_only);

millitrix.child_table.LAYOUT_FIELDS = frappe.model.layout_fields || [];
millitrix.child_table._setup_attempts = new WeakMap();

/** Forms where auto empty row causes premature mandatory errors — user adds rows manually. */
millitrix.child_table.SKIP_AUTO_ADD = {
	"Sales Invoice": ["details"],
	"Purchase Invoice": ["details"],
	"Sales Return": ["details"],
	"Purchase Return": ["details"],
	"In Out Gate Pass": ["details"],
	"Stock Transfer Note": ["details"],
	"Stock Adjustment": ["details"],
	"Opening Stock": ["details"],
	"Closing Stock": ["details"],
	"Purchase Other Bill": ["details"],
	"Sales Other Bill": ["details"],
	"Purchase Return Other Bill": ["details"],
	"Sales Return Other Bill": ["details"],
	"PO Cancellation": ["details"],
	"SO Cancellation": ["details"],
	"Voucher Transaction": ["details"],
};

/** Child DocType → key fields; row is blank if all are empty/zero. */
millitrix.child_table.BLANK_ROW_KEYS = {
	"Crash Refine Input": ["critem", "storeid", "bagqty"],
	"Crash Refine Output": ["proditem"],
	"Sales Invoice Detail": ["storeid", "truckqty", "bagqty", "sonumber"],
	"Purchase Invoice Detail": ["storeid", "truckqty", "bagqty", "ponumber"],
	"Sales Return Detail": ["storeid", "truckqty", "bagqty"],
	"Purchase Return Detail": ["storeid", "truckqty", "bagqty"],
	"Gate Pass Detail": ["storeid", "truckqty", "truckno"],
	"Stock Transfer Detail": ["tostoreid", "truckqty", "delikanta"],
	"Stock Adjustment Detail": ["storeid", "itemcode"],
	"Opening Stock Detail": ["storeid", "itemcode"],
	"Purchase Other Bill Detail": ["itemcode", "quantity"],
	"Sales Other Bill Detail": ["itemcode", "quantity"],
	"Purchase Other Bill Return Detail": ["pbdetlno", "quantity"],
	"Sales Other Bill Return Detail": ["sbdetlno", "quantity"],
	"PO Cancellation Detail": ["ponumber", "itemcode", "cancelqty"],
	"SO Cancellation Detail": ["sonumber", "cancelqty"],
	"Voucher Transaction Detail": ["accid", "debit", "credit"],
	"PaySlip Detail": ["empno", "amount"],
	"Payment and Receipt Document": ["documentid", "amount"],
	"Adjustment PNR": ["pnrno", "amount"],
	"Adjustment Invoice": ["documentid", "amount"],
	"Cash and Bank Voucher Document": ["documentid", "amount"],
	"Expense Voucher Detail": ["accid", "debit", "credit"],
	"Hawala Invoice": ["documentid", "amount"],
	"Hawala Party B": ["accid", "amount"],
};

/**
 * Optional per-child-doctype extras when heuristics are too conservative.
 * Most numeric qty/amount/weight columns are detected automatically.
 */
millitrix.child_table.SUMMABLE_FIELDS = {
	"Purchase Invoice Detail": new Set([
		"truckadv",
		"truckqty",
		"cartage",
		"bagqty",
		"total_weight",
		"inkanta",
		"delikanta",
		"lessweight",
		"dust",
		"netweight",
		"mund",
		"bagamnt",
		"bardana",
		"discount",
		"totalamnt",
		"brokeramnt",
		"labouramnt",
	]),
};

/** Fieldname patterns that must never be summed (ids, refs, row keys). */
millitrix.child_table.SUMMABLE_NAME_DENY = [
	/^(ponumber|sonumber|biltyno|truckno|transporter|gprefeno|gprefno)$/i,
	/detlno$/i,
	/^(storeid|bagid|tostoreid|itemcode|bagitemcode|partyid|accid|empno|psdetlid)$/i,
	/^(emptybags|bags_are|mundtype|critem|proditem)$/i,
	/^(pidetlno|sidetlno|pbdetlno|sbdetlno|rowidx)$/i,
];

/** Never sum even when whitelisted elsewhere (legacy guard). */
millitrix.child_table.NON_SUMMABLE_FIELDS = new Set([
	"ponumber",
	"sonumber",
	"biltyno",
	"truckno",
	"transporter",
	"gprefeno",
	"storeid",
	"bagid",
	"tostoreid",
	"pidetlno",
	"sidetlno",
	"emptybags",
	"bags_are",
	"itemcode",
	"bagitemcode",
	"partyid",
	"accid",
	"pbdetlno",
	"sbdetlno",
	"empno",
	"psdetlid",
]);

/** Unit rates / per-row weights — summing across rows is not meaningful. */
millitrix.child_table.UNIT_RATE_FIELDS = new Set([
	"rate",
	"bagrate",
	"order_rate",
	"brokery_mund",
	"bagweight",
]);

millitrix.child_table.NUMERIC_FIELDTYPES = new Set(["Float", "Int", "Currency", "Percent"]);

millitrix.child_table._format_total = (value, df) => {
	const n = flt(value);
	if (!n) {
		return "";
	}
	if (millitrix.number_format?.format) {
		return millitrix.number_format.format(n, null);
	}
	if (Math.abs(n - Math.round(n)) < 1e-9) {
		return String(Math.round(n));
	}
	return String(parseFloat(n.toFixed(2)));
};

millitrix.child_table._schedule_grid_totals = (grid) => {
	if (!grid) {
		return;
	}
	const table_field = grid.df?.fieldname;
	if (grid.frm) {
		millitrix.child_table.schedule_render_grid_totals(grid.frm, [table_field]);
	} else {
		millitrix.child_table.render_grid_totals(grid);
	}
};

/** Merge frm.doc rows with live control values (unsaved edits). */
millitrix.child_table.get_rows_for_totals = (grid) => {
	const fieldname = grid.df?.fieldname;
	const frm = grid.frm;
	if (!frm || !fieldname) {
		return [];
	}

	const rows = (frm.doc[fieldname] || []).map((row) => ({ ...row }));

	(grid.grid_rows || []).forEach((grid_row, idx) => {
		if (!rows[idx] || !grid_row?.doc) {
			return;
		}

		if (grid_row.row?.hasClass("editable-row") && grid_row.columns_list?.length) {
			grid_row.columns_list.forEach((column) => {
				const fname = column.df?.fieldname;
				if (!fname || !column.field?.get_value) {
					return;
				}
				rows[idx][fname] = column.field.get_value();
			});
		}

		const fields_dict = grid_row.grid_form?.fields_dict;
		if (fields_dict) {
			Object.keys(fields_dict).forEach((fname) => {
				const field = fields_dict[fname];
				if (field?.get_value) {
					rows[idx][fname] = field.get_value();
				}
			});
		}
	});

	return rows;
};

millitrix.child_table.bind_form_in_grid_totals = (grid_row) => {
	const grid = grid_row?.grid;
	if (!grid || !millitrix.child_table.uses_auto_totals(grid)) {
		return;
	}
	const schedule = () => millitrix.child_table._schedule_grid_totals(grid);
	const $wrapper = grid_row.grid_form?.wrapper;
	if (!$wrapper?.length) {
		return;
	}
	$wrapper
		.off(".millitrix-totals")
		.on("input.millitrix-totals change.millitrix-totals", "input, textarea, select", schedule);
	Object.values(grid_row.grid_form.fields_dict || {}).forEach((field) => {
		field.$input
			?.off(".millitrix-totals")
			.on("input.millitrix-totals change.millitrix-totals", schedule);
	});
};

millitrix.child_table.uses_auto_totals = (grid) => millitrix.child_table.is_millitrix_grid(grid);

millitrix.child_table.is_summable_column = (df, child_doctype) => {
	if (!df?.fieldname || df.hidden) {
		return false;
	}
	if (millitrix.child_table.NON_SUMMABLE_FIELDS.has(df.fieldname)) {
		return false;
	}
	if (millitrix.child_table.UNIT_RATE_FIELDS.has(df.fieldname)) {
		return false;
	}
	if (!millitrix.child_table.NUMERIC_FIELDTYPES.has(df.fieldtype)) {
		return false;
	}

	const fn = df.fieldname.toLowerCase();
	if (millitrix.child_table.SUMMABLE_NAME_DENY.some((re) => re.test(fn))) {
		return false;
	}
	if (/(^|_)rate$/.test(fn) || fn.endsWith("_rate")) {
		return false;
	}

	const extras = millitrix.child_table.SUMMABLE_FIELDS[child_doctype];
	if (extras?.has(df.fieldname)) {
		return true;
	}

	// Default: sum qty, weight, amounts, debit/credit, etc.
	return true;
};

millitrix.child_table.get_summable_fields = (grid) => {
	return (grid.visible_columns || [])
		.map((col) => col[0])
		.filter((df) => millitrix.child_table.is_summable_column(df, grid.doctype))
		.map((df) => df.fieldname);
};

millitrix.child_table.clear_grid_total_row = ($field) => {
	$field.find(".millitrix-grid-total-row").remove();
};

millitrix.child_table.get_grid_rows_container = (grid) => {
	if (grid?.parent) {
		const $from_parent = $(grid.parent).find("> .grid-body .rows, .grid-body > .rows").first();
		if ($from_parent.length) {
			return $from_parent;
		}
	}
	return grid?.wrapper?.closest(".grid-field").find(".grid-body .rows").first() || $();
};

millitrix.child_table.paint_grid_total_row = (grid, totals) => {
	const summable_fields = new Set(millitrix.child_table.get_summable_fields(grid));
	const $cols = grid._millitrix_total_row_el?.find(
		".data-row > .grid-static-col.millitrix-grid-col"
	);
	(grid.visible_columns || []).forEach((col, col_idx) => {
		const df = col[0];
		const fieldname = df.fieldname;
		const $cell = $cols?.eq(col_idx);
		if (!$cell?.length) {
			return;
		}
		let content = "";
		if (summable_fields.has(fieldname) && totals[fieldname] !== undefined) {
			content = millitrix.child_table._format_total(totals[fieldname], df);
		}
		$cell
			.toggleClass("text-right", millitrix.child_table.NUMERIC_FIELDTYPES.has(df.fieldtype))
			.find(".millitrix-grid-total-value")
			.text(content);
	});
};

millitrix.child_table.attach_grid_total_row = (grid, totals) => {
	const $rows = millitrix.child_table.get_grid_rows_container(grid);
	if (!$rows.length || !grid.visible_columns?.length) {
		return false;
	}

	const col_count = grid.visible_columns.length;
	let $total_row = $rows.children(".millitrix-grid-total-row").first();
	const existing_cols = $total_row.find(".data-row > .grid-static-col.millitrix-grid-col").length;

	if ($total_row.length && existing_cols !== col_count) {
		$total_row.remove();
		$total_row = $();
	}

	if (!$total_row.length) {
		$total_row = millitrix.child_table.build_grid_total_row(grid, totals);
		$rows.append($total_row);
	} else {
		grid._millitrix_total_row_el = $total_row;
		millitrix.child_table.paint_grid_total_row(grid, totals);
	}

	grid._millitrix_total_row_el = $total_row;
	$rows.append($total_row);

	if (millitrix.child_table.is_millitrix_grid(grid)) {
		millitrix.child_table.normalize_data_row($total_row.find(".data-row"), grid);
	}
	return true;
};

millitrix.child_table.compute_column_totals = (grid, summable_fields) => {
	const rows = millitrix.child_table.get_rows_for_totals(grid);
	const totals = {};
	summable_fields.forEach((fieldname) => {
		totals[fieldname] = rows.reduce((sum, row) => sum + flt(row[fieldname]), 0);
	});
	return totals;
};

millitrix.child_table.build_grid_total_row = (grid, totals) => {
	const $wrapper = $('<div class="grid-row millitrix-grid-total-row"></div>');
	const $data_row = $('<div class="data-row row"></div>').appendTo($wrapper);

	$data_row.append('<div class="row-check col"></div>');
	$data_row.append(
		`<div class="row-index col"><span>${frappe.utils.escape_html(__("Total"))}</span></div>`
	);

	(grid.visible_columns || []).forEach((col) => {
		const df = col[0];
		const colsize = col[1];
		const fieldname = df.fieldname;
		const align = millitrix.child_table.NUMERIC_FIELDTYPES.has(df.fieldtype)
			? " text-right"
			: "";
		let content = "";
		if (totals[fieldname] !== undefined) {
			content = millitrix.child_table._format_total(totals[fieldname], df);
		}
		$data_row.append(
			`<div class="col grid-static-col millitrix-grid-col${align}"><div class="static-area ellipsis"><span class="millitrix-grid-total-value">${content}</span></div></div>`
		);
	});
	$data_row.append('<div class="col grid-static-col millitrix-grid-row-spacer"></div>');

	millitrix.child_table.normalize_data_row($data_row, grid);

	return $wrapper;
};

millitrix.child_table.ensure_grid_totals_hook = (grid) => {
	if (!grid || grid._millitrix_totals_hook) {
		return;
	}
	grid._millitrix_totals_hook = true;
	const _orig_refresh = grid.refresh.bind(grid);
	grid.refresh = function (...args) {
		const out = _orig_refresh.apply(this, args);
		millitrix.child_table.render_grid_totals(grid);
		return out;
	};

	if (!grid._millitrix_add_row_hook && typeof grid.add_new_row === "function") {
		grid._millitrix_add_row_hook = true;
		const _orig_add_new_row = grid.add_new_row.bind(grid);
		grid.add_new_row = function (...args) {
			const out = _orig_add_new_row(...args);
			setTimeout(() => millitrix.child_table.render_grid_totals(grid), 0);
			return out;
		};
	}

	millitrix.child_table.bind_grid_live_totals(grid);
};

millitrix.child_table.bind_grid_live_totals = (grid, attempt = 0) => {
	if (!grid || grid._millitrix_live_totals_bound || !millitrix.child_table.uses_auto_totals(grid)) {
		return;
	}
	if (!grid.wrapper?.length) {
		if (attempt < 12) {
			setTimeout(() => millitrix.child_table.bind_grid_live_totals(grid, attempt + 1), 50);
		}
		return;
	}
	grid._millitrix_live_totals_bound = true;
	const schedule = () => millitrix.child_table._schedule_grid_totals(grid);

	grid.wrapper.on("input change", "input, select, textarea", schedule);

	if (grid.frm?.wrapper) {
		$(grid.frm.wrapper).on("grid-row-render grid-move-row grid-make-sortable", (_e, frm) => {
			if (frm === grid.frm) {
				schedule();
			}
		});
	}
};

millitrix.child_table.render_grid_totals = (grid) => {
	if (!grid?.wrapper || !millitrix.child_table.uses_auto_totals(grid)) {
		return;
	}

	const run = () => {
		if (!grid.visible_columns?.length) {
			return;
		}
		const summable_fields = millitrix.child_table.get_summable_fields(grid);
		const totals = millitrix.child_table.compute_column_totals(grid, summable_fields);
		millitrix.child_table.attach_grid_total_row(grid, totals);
		if (millitrix.child_table.is_millitrix_grid(grid)) {
			millitrix.child_table.sync_grid_content_width(grid);
		}
	};

	run();
	// Frappe may reorder .rows children after refresh — pin total row last
	setTimeout(run, 0);
};

millitrix.child_table.ensure_grid_total_row = (grid) => {
	if (!grid || !millitrix.child_table.uses_auto_totals(grid)) {
		return;
	}
	const $rows = millitrix.child_table.get_grid_rows_container(grid);
	if (!$rows.length) {
		return;
	}
	if (!$rows.children(".millitrix-grid-total-row").length) {
		millitrix.child_table.render_grid_totals(grid);
		return;
	}
	const summable_fields = millitrix.child_table.get_summable_fields(grid);
	const totals = millitrix.child_table.compute_column_totals(grid, summable_fields);
	millitrix.child_table.attach_grid_total_row(grid, totals);
};

millitrix.child_table.render_grid_totals_for_form = (frm, table_fieldnames) => {
	const fields = table_fieldnames || millitrix.child_table.table_fields(frm);
	for (const fieldname of fields) {
		const grid = frm.fields_dict[fieldname]?.grid;
		if (grid) {
			millitrix.child_table.render_grid_totals(grid);
		}
	}
};

millitrix.child_table.schedule_render_grid_totals = (frm, table_fieldnames) => {
	if (!frm || !millitrix.child_table.is_millitrix_form(frm)) {
		return;
	}
	if (!frm._millitrix_totals_timer) {
		frm._millitrix_totals_timer = null;
	}
	clearTimeout(frm._millitrix_totals_timer);
	frm._millitrix_totals_timer = setTimeout(() => {
		frm._millitrix_totals_timer = null;
		millitrix.child_table.render_grid_totals_for_form(frm, table_fieldnames);
	}, 30);
};

millitrix.child_table.is_blank_row = (row, child_doctype) => {
	const keys = millitrix.child_table.BLANK_ROW_KEYS[child_doctype];
	if (!keys?.length) {
		return false;
	}
	return !keys.some((field) => {
		const value = row[field];
		if (value === null || value === undefined || value === "") {
			return false;
		}
		if (typeof value === "number" && !value) {
			return false;
		}
		return true;
	});
};

millitrix.child_table.strip_blank_rows = (frm, table_field) => {
	const grid = frm.fields_dict[table_field]?.grid;
	const child_doctype = grid?.doctype;
	if (!child_doctype) {
		return false;
	}
	const rows = frm.doc[table_field] || [];
	const kept = rows.filter((row) => !millitrix.child_table.is_blank_row(row, child_doctype));
	if (kept.length === rows.length) {
		return false;
	}
	frm.doc[table_field] = kept;
	return true;
};

millitrix.child_table.strip_blank_rows_for_form = (frm) => {
	let changed = false;
	for (const fieldname of millitrix.child_table.table_fields(frm)) {
		if (millitrix.child_table.strip_blank_rows(frm, fieldname)) {
			changed = true;
		}
	}
	if (changed) {
		frm.refresh_fields();
	}
};

/** Calculated / fetch_from columns must never block save as mandatory. */
millitrix.child_table.apply_grid_reqd_guard = (grid) => {
	if (!grid?.update_docfields_property) {
		return;
	}
	(grid.docfields || []).forEach((df) => {
		if (df.read_only || df.fetch_from) {
			grid.update_docfields_property(df.fieldname, "reqd", 0);
		}
	});
	const calc_cols = [
		"total_weight",
		"netweight",
		"mund",
		"bagamnt",
		"bardana",
		"totalamnt",
		"weight",
		"ref_weight",
		"ref_bags",
		"prod_1",
		"prod_2",
		"amount",
		"docbalamnt",
		"balance",
		"stock_value",
		"adjusted_stock",
		"current_stock",
	];
	calc_cols.forEach((col) => {
		if ((grid.docfields || []).some((df) => df.fieldname === col)) {
			grid.update_docfields_property(col, "reqd", 0);
			grid.update_docfields_property(col, "read_only", 1);
		}
	});
};

/** Not on Oracle Closing grid — do not show "more fields" hint for these. */
millitrix.child_table.GRID_HINT_EXCLUDE = {
	"Closing and Adjustment Entries": {
		details: ["empno", "trans_id", "bnkcash_gl"],
	},
	"Closing Stock": {
		details: ["opening_stock"],
	},
	"Opening Stock": {
		details: ["closing_stock", "stock_value"],
	},
	"Crashing Refine": {
		inputs: ["rate", "mundtype", "bagrate", "dustitemid", "dust_rate"],
		outputs: ["rate"],
	},
	"Employee Payment Voucher": {
		documents: ["partyid", "accid", "doctypeid", "documentid", "docbalamnt"],
	},
	"Employee Receipt Voucher": {
		documents: ["partyid", "accid", "doctypeid", "documentid", "docbalamnt"],
	},
	"PaySlip": {
		employees: ["psdetlid"],
	},
	"Expense Voucher": {
		details: ["accid"],
	},
	"Payment Voucher": {
		details: [],
	},
	"Receipt Voucher": {
		details: [],
	},
};

millitrix.child_table.hint_excluded_fieldnames = (frm, table_fieldname) => {
	const by_form = millitrix.child_table.GRID_HINT_EXCLUDE[frm?.doctype];
	if (!by_form) {
		return [];
	}
	return by_form[table_fieldname] || [];
};

millitrix.child_table.is_millitrix_form = (frm) =>
	Boolean(frm?.meta?.module === "Millitrix ERP");

millitrix.child_table.format_grid_cell_html = (value, df) => {
	if (!millitrix.number_format?.is_numeric_field?.(df)) {
		return null;
	}
	const plain = millitrix.number_format.format_display(value, df);
	if (!plain) {
		return "";
	}
	return frappe.form.formatters._right(plain, null);
};

millitrix.child_table.sanitize_grid_row_display = (grid_row) => {
	if (!grid_row?.columns || !millitrix.number_format?.clean_html_display) {
		return;
	}
	Object.keys(grid_row.columns).forEach((fieldname) => {
		const column = grid_row.columns[fieldname];
		if (!column?.static_area?.length) {
			return;
		}
		const df = column.df || grid_row.docfields?.find((f) => f.fieldname === fieldname);
		if (!millitrix.number_format.is_numeric_field(df)) {
			return;
		}
		const html = column.static_area.html();
		if (!html || !/Rs|PKR|\$|€|£|₹/i.test(html)) {
			if (grid_row.doc && df) {
				const fixed = millitrix.child_table.format_grid_cell_html(
					grid_row.doc[fieldname],
					df
				);
				if (fixed !== null && fixed !== html) {
					column.static_area.html(fixed);
				}
			}
			return;
		}
		const cleaned = millitrix.number_format.clean_html_display(html, df);
		if (cleaned !== html) {
			column.static_area.html(cleaned);
		}
	});
};

millitrix.child_table.is_millitrix_grid = (grid) =>
	Boolean(
		grid?.meta?.istable &&
			millitrix.child_table.is_millitrix_form(grid.frm)
	);

millitrix.child_table.is_grid_data_field = (df, grid) =>
	Boolean(
		df?.fieldname &&
			!df.hidden &&
			!frappe.model.layout_fields.includes(df.fieldtype) &&
			((grid.frm && grid.frm.get_perm(df.permlevel, "read")) || !grid.frm)
	);

millitrix.child_table.GRID_COL_PX = 96;
millitrix.child_table.TRAIL_COL_PX = 40;

millitrix.child_table.style_grid_column = ($col, colsize) => {
	if (!$col?.length) {
		return;
	}
	const w = millitrix.child_table.GRID_COL_PX * (cint(colsize) || 1);
	const cls = ($col.attr("class") || "")
		.replace(/\bcol-xs-\d+\b/g, "")
		.replace(/\bmillitrix-grid-col\b/g, "")
		.trim();
	$col.attr("class", `${cls} millitrix-grid-col`.trim());
	$col.css({
		width: `${w}px`,
		minWidth: `${w}px`,
		maxWidth: `${w}px`,
		flex: `0 0 ${w}px`,
		float: "none",
	});
};

millitrix.child_table.style_trail_column = ($col) => {
	if (!$col?.length) {
		return;
	}
	const w = millitrix.child_table.TRAIL_COL_PX;
	$col.css({
		width: `${w}px`,
		minWidth: `${w}px`,
		maxWidth: `${w}px`,
		flex: `0 0 ${w}px`,
		float: "none",
	});
};

millitrix.child_table.normalize_data_row = ($row, grid) => {
	if (!$row?.length || !millitrix.child_table.is_millitrix_grid(grid)) {
		return;
	}
	const $grid_row = $row.closest(".grid-row");
	if ($grid_row.hasClass("grid-row-open") || $row.hasClass("grid-row-open")) {
		return;
	}
	if ($grid_row.find(".form-in-grid").length) {
		return;
	}

	$row.css({
		display: "flex",
		flexWrap: "nowrap",
		marginLeft: 0,
		marginRight: 0,
		float: "none",
	});

	$row.children(".row-check").css({
		width: "34px",
		minWidth: "34px",
		maxWidth: "34px",
		flex: "0 0 34px",
		float: "none",
	});

	$row.children(".row-index").css({
		width: "42px",
		minWidth: "42px",
		maxWidth: "42px",
		flex: "0 0 42px",
		float: "none",
	});

	$row.children(".grid-static-col").each(function () {
		const $c = $(this);
		if (
			$c.hasClass("search") ||
			$c.hasClass("millitrix-grid-row-spacer") ||
			$c.hasClass("d-flex")
		) {
			millitrix.child_table.style_trail_column($c);
			return;
		}
		if ($c.find(".btn-open-row").length) {
			return;
		}
		millitrix.child_table.style_grid_column($c, 1);
	});

	$row.children(".col").filter(function () {
		return Boolean($(this).find(".btn-open-row").length);
	}).each(function () {
		millitrix.child_table.style_trail_column($(this));
	});

	$row.children(".millitrix-grid-row-spacer, .grid-static-col.search").each(function () {
		millitrix.child_table.style_trail_column($(this));
	});

	const total_px = millitrix.child_table.grid_content_width(grid);
	if (total_px) {
		const px = `${total_px}px`;
		$row.css({ width: px, minWidth: px, maxWidth: px });
	}
};

millitrix.child_table.normalize_all_grid_rows = (grid) => {
	if (!millitrix.child_table.is_millitrix_grid(grid)) {
		return;
	}
	if (
		grid.wrapper?.closest(".frappe-control").hasClass("millitrix-grid-row-editing") ||
		grid.wrapper?.find(".grid-row-open").length
	) {
		return;
	}
	const $form_grid = grid.wrapper?.find("> .form-grid-container > .form-grid");
	$form_grid?.find(".data-row").each(function () {
		millitrix.child_table.normalize_data_row($(this), grid);
	});
	millitrix.child_table.sync_grid_content_width(grid);
};

millitrix.child_table.apply_row_scroll_layout = (grid_row) => {
	millitrix.child_table.normalize_data_row(grid_row?.row, grid_row?.grid);
};

millitrix.child_table.grid_content_width = (grid) => {
	const col_count = grid.visible_columns?.length || 0;
	if (!col_count) {
		return 0;
	}
	return 34 + 42 + col_count * millitrix.child_table.GRID_COL_PX + millitrix.child_table.TRAIL_COL_PX;
};

millitrix.child_table.sync_grid_content_width = (grid) => {
	if (!millitrix.child_table.is_millitrix_grid(grid)) {
		return;
	}
	if (grid.wrapper?.closest(".frappe-control").hasClass("millitrix-grid-row-editing")) {
		return;
	}
	const total_px = millitrix.child_table.grid_content_width(grid);
	if (!total_px) {
		return;
	}
	const px = `${total_px}px`;
	const $form_grid = grid.wrapper?.find("> .form-grid-container > .form-grid");
	if (!$form_grid?.length) {
		return;
	}
	const form_el = $form_grid[0];
	form_el.style.position = "static";
	form_el.style.left = "0";
	form_el.style.width = px;
	form_el.style.minWidth = px;
	form_el.style.maxWidth = px;

	$form_grid.find(".grid-heading-row, .grid-body, .data-row").css({
		width: px,
		minWidth: px,
		maxWidth: px,
	});
	millitrix.child_table.sync_grid_container_width(grid);
};

/** Border wrapper matches table column width; max-width caps when scroll is needed. */
millitrix.child_table.sync_grid_container_width = (grid) => {
	if (!millitrix.child_table.is_millitrix_grid(grid)) {
		return;
	}
	const $container = grid.wrapper?.children(".form-grid-container");
	const $control = grid.wrapper?.closest(".frappe-control");
	if (!$container?.length) {
		return;
	}
	if (
		$control?.hasClass("millitrix-grid-row-editing") ||
		grid.wrapper?.find(".grid-row-open").length
	) {
		$container[0].style.width = "100%";
		$container[0].style.maxWidth = "100%";
		return;
	}
	const total_px = millitrix.child_table.grid_content_width(grid);
	if (!total_px) {
		return;
	}
	$container[0].style.width = `${total_px}px`;
	$container[0].style.maxWidth = "100%";
};

/** Row edit form uses normal Frappe layout — release scroll-pack pixel widths. */
millitrix.child_table.set_grid_scroll_widths = (grid, scroll_enabled) => {
	if (!millitrix.child_table.is_millitrix_grid(grid)) {
		return;
	}
	const $form_grid = grid.wrapper?.find("> .form-grid-container > .form-grid");
	const $control = grid.wrapper?.closest(".frappe-control");
	if (!$form_grid?.length) {
		return;
	}

	if (!scroll_enabled) {
		$control.addClass("millitrix-grid-row-editing");
		const form_el = $form_grid[0];
		form_el.style.width = "100%";
		form_el.style.minWidth = "0";
		form_el.style.maxWidth = "100%";
		$form_grid.find(".grid-heading-row, .grid-body").css({
			width: "100%",
			minWidth: "0",
			maxWidth: "100%",
		});
		$form_grid.find(".data-row").css({
			width: "",
			minWidth: "",
			maxWidth: "",
		});
		return;
	}

	$control.removeClass("millitrix-grid-row-editing");
	millitrix.child_table.sync_grid_content_width(grid);
	millitrix.child_table.normalize_all_grid_rows(grid);
};

millitrix.child_table.sanitize_all_grid_displays = (grid) => {
	if (!millitrix.child_table.is_millitrix_grid(grid)) {
		return;
	}
	(grid.grid_rows || []).forEach((grid_row) => {
		millitrix.child_table.sanitize_grid_row_display(grid_row);
	});
};

millitrix.child_table.apply_grid_scroll_layout = (grid) => {
	if (!millitrix.child_table.is_millitrix_grid(grid)) {
		return;
	}
	if (
		grid.wrapper?.closest(".frappe-control").hasClass("millitrix-grid-row-editing") ||
		grid.wrapper?.find(".grid-row-open").length
	) {
		return;
	}
	millitrix.child_table.mark_grid_scrollable(grid);
	millitrix.child_table.normalize_all_grid_rows(grid);
	millitrix.child_table.sanitize_all_grid_displays(grid);
	millitrix.child_table.ensure_grid_total_row(grid);
	const $container = grid.wrapper?.children(".form-grid-container");
	const $control = grid.wrapper?.closest(".frappe-control");
	if ($container?.length) {
		millitrix.child_table.update_grid_scroll_hints($container, $control);
	}
};

/** Install Grid / GridRow prototype patches (frappe.ui.form.Grid does not exist). */
millitrix.child_table._install_grid_prototypes = () => {
	if (millitrix.child_table._grid_proto_installed) {
		return true;
	}

	const ControlTable = frappe.ui.form.ControlTable;
	if (!ControlTable) {
		return false;
	}

	const orig_table_make = ControlTable.prototype.make;
	ControlTable.prototype.make = function () {
		orig_table_make.apply(this, arguments);
		millitrix.child_table._patch_grid_from_instance(this.grid);
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			millitrix.child_table.reset_grid_columns(this.grid);
		}
	};

	millitrix.child_table._grid_proto_installed = true;
	return true;
};

millitrix.child_table._patch_grid_from_instance = (grid) => {
	if (!grid || millitrix.child_table._grid_methods_patched) {
		return;
	}

	const grid_proto = Object.getPrototypeOf(grid);
	const orig_setup = grid_proto.setup_visible_columns;
	const orig_make_head = grid_proto.make_head;
	const orig_refresh = grid_proto.refresh;

	grid_proto.setup_visible_columns = function () {
		if (!millitrix.child_table.is_millitrix_grid(this)) {
			return orig_setup.call(this);
		}
		if (this.visible_columns && this.visible_columns.length > 0) {
			return;
		}

		this.user_defined_columns = [];
		this.setup_user_defined_columns();

		const fields =
			this.user_defined_columns && this.user_defined_columns.length > 0
				? this.user_defined_columns
				: this.editable_fields || this.docfields;

		this.visible_columns = [];

		for (const ci in fields) {
			const _df = fields[ci];
			const df =
				this.user_defined_columns && this.user_defined_columns.length > 0
					? _df
					: this.fields_map[_df.fieldname];

			if (
				df &&
				!df.hidden &&
				(this.user_defined_columns?.length > 0 ||
					this.editable_fields ||
					df.in_list_view) &&
				((this.frm && this.frm.get_perm(df.permlevel, "read")) || !this.frm) &&
				!frappe.model.layout_fields.includes(df.fieldtype)
			) {
				df.colsize = 1;
				df.columns = 1;
				this.visible_columns.push([df, 1]);
			}
		}
	};

	grid_proto.make_head = function () {
		orig_make_head.apply(this, arguments);
		millitrix.child_table._patch_grid_row_from_instance(this.header_row);
		if (millitrix.child_table.is_millitrix_grid(this)) {
			millitrix.child_table.apply_grid_scroll_layout(this);
		}
	};

	const orig_render_result_rows = grid_proto.render_result_rows;
	grid_proto.render_result_rows = function (...args) {
		const out = orig_render_result_rows.apply(this, args);
		if (millitrix.child_table.uses_auto_totals(this)) {
			millitrix.child_table.ensure_grid_total_row(this);
		}
		return out;
	};

	grid_proto.refresh = function (...args) {
		const out = orig_refresh.apply(this, args);
		if (
			millitrix.child_table.is_millitrix_grid(this) &&
			!this.wrapper?.closest(".frappe-control").hasClass("millitrix-grid-row-editing")
		) {
			millitrix.child_table.apply_grid_scroll_layout(this);
		}
		if (millitrix.child_table.uses_auto_totals(this)) {
			millitrix.child_table.render_grid_totals(this);
		}
		return out;
	};

	millitrix.child_table._grid_methods_patched = true;
};

millitrix.child_table._patch_grid_row_from_instance = (grid_row) => {
	if (!grid_row || millitrix.child_table._grid_row_methods_patched) {
		return;
	}

	const row_proto = Object.getPrototypeOf(grid_row);
	const orig_validate = row_proto.validate_columns_width;
	const orig_make_column = row_proto.make_column;
	const orig_make_search_column = row_proto.make_search_column;
	const orig_setup_columns = row_proto.setup_columns;
	const orig_add_configure_btn = row_proto.add_column_configure_button;
	const orig_add_open_form_btn = row_proto.add_open_form_button;
	const orig_show_form = row_proto.show_form;
	const orig_hide_form = row_proto.hide_form;
	const orig_make_control = row_proto.make_control;
	const orig_refresh_field = row_proto.refresh_field;

	row_proto.make_column = function (df, colsize, txt, ci) {
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			colsize = 1;
			if (this.doc) {
				const fixed = millitrix.child_table.format_grid_cell_html(
					this.doc[df.fieldname],
					df
				);
				if (fixed !== null) {
					txt = fixed;
				}
			}
		}
		const $col = orig_make_column.call(this, df, colsize, txt, ci);
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			millitrix.child_table.style_grid_column($col, 1);
		}
		return $col;
	};

	row_proto.make_search_column = function (df, colsize) {
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			colsize = 1;
		}
		const $col = orig_make_search_column.call(this, df, colsize);
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			millitrix.child_table.style_grid_column($col, 1);
		}
		return $col;
	};

	row_proto.setup_columns = function () {
		orig_setup_columns.apply(this, arguments);
		if (millitrix.child_table.is_millitrix_grid(this.grid) && !this.wrapper?.hasClass("grid-row-open")) {
			millitrix.child_table.sanitize_grid_row_display(this);
			millitrix.child_table.normalize_data_row(this.row, this.grid);
		}
	};

	row_proto.refresh_field = function (fieldname, txt) {
		const out = orig_refresh_field.call(this, fieldname, txt);
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			millitrix.child_table.sanitize_grid_row_display(this);
		}
		return out;
	};

	row_proto.add_column_configure_button = function () {
		orig_add_configure_btn.apply(this, arguments);
		if (millitrix.child_table.is_millitrix_grid(this.grid) && this.configure_columns_button) {
			millitrix.child_table.style_trail_column($(this.configure_columns_button));
			millitrix.child_table.normalize_data_row(this.row, this.grid);
		}
	};

	row_proto.add_open_form_button = function () {
		orig_add_open_form_btn.apply(this, arguments);
		if (millitrix.child_table.is_millitrix_grid(this.grid) && this.open_form_button) {
			$(this.open_form_button)
				.closest(".col")
				.each(function () {
					millitrix.child_table.style_trail_column($(this));
				});
			millitrix.child_table.normalize_data_row(this.row, this.grid);
		}
	};

	row_proto.show_form = function () {
		let saved_docfields;
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			millitrix.child_table.set_grid_scroll_widths(this.grid, false);
			saved_docfields = this.docfields;
			this.docfields = millitrix.child_table.visible_column_docfields(this);
		}
		const out = orig_show_form.apply(this, arguments);
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			this.docfields = saved_docfields;
			const $control = this.grid.wrapper?.closest(".frappe-control");
			$control?.addClass("millitrix-grid-row-editing");
			setTimeout(() => {
				millitrix.child_table.bind_form_in_grid_totals(this);
				millitrix.child_table.portal_row_edit_form(this);
				$control?.addClass("millitrix-grid-row-editing");
			}, 0);
		}
		return out;
	};

	row_proto.make_control = function (column) {
		const out = orig_make_control.apply(this, arguments);
		if (millitrix.child_table.is_millitrix_grid(this.grid) && column?.field) {
			const schedule = () => millitrix.child_table._schedule_grid_totals(this.grid);
			column.field.$input
				?.off(".millitrix-totals")
				.on("input.millitrix-totals change.millitrix-totals", schedule);
		}
		return out;
	};

	row_proto.hide_form = function () {
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			millitrix.child_table.restore_row_edit_form(this);
		}
		const out = orig_hide_form.apply(this, arguments);
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			this.grid.wrapper?.closest(".frappe-control")?.removeClass("millitrix-grid-row-editing");
			millitrix.child_table.set_grid_scroll_widths(this.grid, true);
		}
		return out;
	};

	row_proto.validate_columns_width = function () {
		if (millitrix.child_table.is_millitrix_grid(this.grid)) {
			return;
		}
		return orig_validate.call(this);
	};

	millitrix.child_table._grid_row_methods_patched = true;
};

millitrix.child_table.ensure_grid_edit_portal = ($grid_field) => {
	let $portal = $grid_field.children(".millitrix-grid-edit-portal");
	if (!$portal.length) {
		$portal = $('<div class="millitrix-grid-edit-portal"></div>');
		$grid_field.children(".form-grid-container").after($portal);
	}
	return $portal;
};

millitrix.child_table.sync_portaled_row_edit_form = (grid_row) => {
	const $container = grid_row.grid.wrapper?.children(".form-grid-container");
	const $portal = grid_row.grid.wrapper?.children(".millitrix-grid-edit-portal");
	const $form = $portal?.children(".form-in-grid");
	if (!$container?.length || !$portal?.length || !$form?.length) {
		return;
	}
	const w = $container[0].offsetWidth;
	$portal.css({ width: w ? `${w}px` : "100%", maxWidth: "100%" });
	$form.css({ width: "100%", maxWidth: "100%", margin: 0 });
};

millitrix.child_table.clear_portaled_row_edit_sync = ($portal) => {
	const el = $portal?.[0];
	if (!el?._millitrix_edit_sync) {
		return;
	}
	window.removeEventListener("scroll", el._millitrix_edit_sync, true);
	window.removeEventListener("resize", el._millitrix_edit_sync);
	el._millitrix_edit_scroll_targets?.forEach((node) => {
		node.removeEventListener("scroll", el._millitrix_edit_sync);
	});
	delete el._millitrix_edit_sync;
	delete el._millitrix_edit_scroll_targets;
	delete el._millitrix_edit_grid_row;
};

millitrix.child_table.portal_row_edit_form = (grid_row) => {
	const $grid_field = grid_row.grid.wrapper;
	const $form = grid_row.wrapper?.find("> .form-in-grid");
	if (!$grid_field?.length || !$form?.length) {
		return;
	}
	const $portal = millitrix.child_table.ensure_grid_edit_portal($grid_field);
	millitrix.child_table.clear_portaled_row_edit_sync($portal);
	$form[0]._millitrix_edit_home = grid_row.wrapper[0];
	$form.appendTo($portal);

	const sync = () => millitrix.child_table.sync_portaled_row_edit_form(grid_row);
	$portal[0]._millitrix_edit_sync = sync;
	$portal[0]._millitrix_edit_grid_row = grid_row;
	const scroll_targets = [$grid_field.children(".form-grid-container")[0]].filter(Boolean);
	$portal[0]._millitrix_edit_scroll_targets = scroll_targets;
	requestAnimationFrame(sync);
	window.addEventListener("scroll", sync, true);
	window.addEventListener("resize", sync);
	scroll_targets.forEach((node) => node.addEventListener("scroll", sync, { passive: true }));
};

millitrix.child_table.restore_row_edit_form = (grid_row) => {
	const $grid_field = grid_row.grid.wrapper;
	const $portal = $grid_field?.children(".millitrix-grid-edit-portal");
	const $form = $portal?.children(".form-in-grid");
	millitrix.child_table.clear_portaled_row_edit_sync($portal);
	if ($form?.length) {
		const home = $form[0]._millitrix_edit_home || grid_row.wrapper?.[0];
		if (home) {
			$(home).append($form);
		}
		delete $form[0]._millitrix_edit_home;
	}
	$portal?.empty();
};

millitrix.child_table.visible_column_docfields = (grid_row) => {
	const visible = new Set((grid_row.grid.visible_columns || []).map((c) => c[0].fieldname));
	return (grid_row.docfields || []).filter((df) => visible.has(df.fieldname));
};

millitrix.child_table.mark_grid_scrollable = (grid) => {
	if (!grid?.wrapper || !millitrix.child_table.is_millitrix_grid(grid)) {
		return;
	}

	const $control = grid.wrapper.closest(".frappe-control");
	const $container = grid.wrapper.children(".form-grid-container");

	$control.addClass("millitrix-child-table-pack");

	if ($container.length) {
		const el = $container[0];
		el.style.boxSizing = "border-box";
		el.style.overflowX = "auto";
		el.style.overflowY = "visible";
		millitrix.child_table.bind_grid_wheel_passthrough($container, $control);
		millitrix.child_table.bind_grid_focus_layer($control);
		millitrix.child_table.sync_grid_container_width(grid);
	}
};

/** Let vertical trackpad / wheel scroll the form page instead of trapping in the grid. */
millitrix.child_table.find_vertical_scroll_parent = (el) => {
	let node = el?.parentElement;
	while (node && node !== document.body) {
		const style = window.getComputedStyle(node);
		const overflowY = style.overflowY;
		if (
			(overflowY === "auto" || overflowY === "scroll" || overflowY === "overlay") &&
			node.scrollHeight > node.clientHeight + 1
		) {
			return node;
		}
		node = node.parentElement;
	}
	return document.scrollingElement || document.documentElement;
};

millitrix.child_table.bind_grid_wheel_passthrough = ($container, $control) => {
	if (!$container?.length || $container[0]._millitrix_wheel_bound) {
		return;
	}
	$container[0]._millitrix_wheel_bound = true;

	const update_hints = () => millitrix.child_table.update_grid_scroll_hints($container, $control);
	update_hints();
	$container.on("scroll.millitrix-grid", update_hints);

	$container[0].addEventListener(
		"wheel",
		(e) => {
			if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) {
				return;
			}
			const parent = millitrix.child_table.find_vertical_scroll_parent($container[0]);
			if (!parent || parent === $container[0]) {
				return;
			}
			parent.scrollTop += e.deltaY;
			e.preventDefault();
		},
		{ passive: false }
	);
};

millitrix.child_table.update_grid_scroll_hints = ($container, $control) => {
	if (!$container?.length || !$control?.length) {
		return;
	}
	if ($control.hasClass("millitrix-grid-row-editing") || $control.find(".grid-row-open").length) {
		$control.removeClass("millitrix-grid-scroll-left millitrix-grid-scroll-right");
		return;
	}
	const el = $container[0];
	const max = Math.max(0, el.scrollWidth - el.clientWidth);
	const left = el.scrollLeft > 4;
	const right = max > 4 && el.scrollLeft < max - 4;
	$control.toggleClass("millitrix-grid-scroll-left", left);
	$control.toggleClass("millitrix-grid-scroll-right", right);
};

millitrix.child_table.bind_grid_focus_layer = ($control) => {
	if (!$control?.length || $control[0]._millitrix_focus_bound) {
		return;
	}
	$control[0]._millitrix_focus_bound = true;
	$control.on("focusin.millitrix-grid", () => {
		$(".millitrix-child-table-pack.millitrix-grid-active").removeClass("millitrix-grid-active");
		$control.addClass("millitrix-grid-active");
	});
	$control.on("focusout.millitrix-grid", () => {
		setTimeout(() => {
			if (!$control[0].contains(document.activeElement)) {
				$control.removeClass("millitrix-grid-active");
			}
		}, 0);
	});
};

/** Portal only the awesomplete <ul> to body — grid/row stay inside scroll wrapper. */
millitrix.child_table.get_grid_dropdown_list = (input) => {
	const list_id = input?.getAttribute?.("aria-owns");
	return list_id ? document.getElementById(list_id) : null;
};

millitrix.child_table.sync_portaled_dropdown = (ul, input) => {
	if (!ul || !input) {
		return;
	}
	const rect = input.getBoundingClientRect();
	const min_width = 250;
	const width = Math.max(rect.width, min_width);
	let left = rect.left;
	if (left + width > window.innerWidth - 8) {
		left = Math.max(8, rect.right - width);
		ul.classList.add("awesomplete-align-right");
	} else {
		ul.classList.remove("awesomplete-align-right");
	}
	const list_height = ul.offsetHeight || ul.scrollHeight || 0;
	const space_below = window.innerHeight - rect.bottom - 8;
	const space_above = rect.top - 8;
	let top = rect.bottom;
	if (list_height && list_height > space_below && space_above > list_height) {
		top = rect.top - list_height;
	}
	Object.assign(ul.style, {
		position: "fixed",
		top: `${top}px`,
		left: `${left}px`,
		width: `${width}px`,
		right: "auto",
		zIndex: "1100",
	});
};

millitrix.child_table.observe_portaled_dropdown = (ul, input, $control) => {
	if (!ul || ul._millitrix_portal_observer) {
		return;
	}
	const sync = () => millitrix.child_table.sync_portaled_dropdown(ul, input);
	ul._millitrix_portal_observer = new MutationObserver(() => {
		requestAnimationFrame(sync);
	});
	ul._millitrix_portal_observer.observe(ul, { childList: true, subtree: true });
	millitrix.child_table.portal_bind_scroll(ul, input, $control, sync);
	requestAnimationFrame(() => requestAnimationFrame(sync));
};

millitrix.child_table.clear_portaled_dropdown = (ul) => {
	if (!ul) {
		return;
	}
	ul.classList.remove("millitrix-portaled-dropdown");
	ul.style.position = "";
	ul.style.top = "";
	ul.style.left = "";
	ul.style.width = "";
	ul.style.right = "";
	ul.style.zIndex = "";
	delete ul._millitrix_portal_input;
	if (ul._millitrix_portal_observer) {
		ul._millitrix_portal_observer.disconnect();
		delete ul._millitrix_portal_observer;
	}
	if (ul._millitrix_portal_sync) {
		window.removeEventListener("scroll", ul._millitrix_portal_sync, true);
		window.removeEventListener("resize", ul._millitrix_portal_sync);
		ul._millitrix_portal_scroll_targets?.forEach((node) => {
			node.removeEventListener("scroll", ul._millitrix_portal_sync);
		});
		delete ul._millitrix_portal_sync;
		delete ul._millitrix_portal_scroll_targets;
	}
};

millitrix.child_table.restore_portaled_dropdown = (ul) => {
	if (!ul?._millitrix_portal_home) {
		return;
	}
	const home = ul._millitrix_portal_home;
	millitrix.child_table.clear_portaled_dropdown(ul);
	if (ul.parentElement !== home) {
		home.appendChild(ul);
	}
	delete ul._millitrix_portal_home;
};

millitrix.child_table.portal_bind_scroll = (ul, input, $control, sync) => {
	ul._millitrix_portal_sync = sync;
	const scroll_targets = [$control.find(".form-grid-container")[0]].filter(Boolean);
	ul._millitrix_portal_scroll_targets = scroll_targets;
	window.addEventListener("scroll", sync, true);
	window.addEventListener("resize", sync);
	scroll_targets.forEach((node) => {
		node.addEventListener("scroll", sync, { passive: true });
	});
};

millitrix.child_table.portal_grid_dropdown = (input, $control) => {
	const ul = millitrix.child_table.get_grid_dropdown_list(input);
	const home = input?.closest?.(".awesomplete");
	if (!ul || !home) {
		return;
	}
	millitrix.child_table.restore_portaled_dropdown(ul);
	ul._millitrix_portal_home = home;
	ul._millitrix_portal_input = input;
	ul.classList.add("millitrix-portaled-dropdown");
	document.body.appendChild(ul);
	millitrix.child_table.observe_portaled_dropdown(ul, input, $control);
};

millitrix.child_table.bind_grid_dropdown_portal = () => {
	if (millitrix.child_table._dropdown_portal_global_bound) {
		return;
	}
	millitrix.child_table._dropdown_portal_global_bound = true;

	$(document).on(
		"awesomplete-open.millitrix-portal",
		".millitrix-child-table-pack input",
		function () {
			const $control = $(this).closest(".millitrix-child-table-pack");
			millitrix.child_table.portal_grid_dropdown(this, $control);
		}
	);

	$(document).on(
		"awesomplete-close.millitrix-portal",
		".millitrix-child-table-pack input",
		function () {
			millitrix.child_table.restore_portaled_dropdown(
				millitrix.child_table.get_grid_dropdown_list(this)
			);
		}
	);
};

millitrix.child_table.reset_grid_columns = (grid) => {
	if (!millitrix.child_table.is_millitrix_grid(grid)) {
		return;
	}
	millitrix.child_table.mark_grid_scrollable(grid);
	if (!grid.visible_columns?.length && typeof grid.setup_visible_columns === "function") {
		grid.setup_visible_columns();
	}
	millitrix.child_table.apply_grid_scroll_layout(grid);
};

millitrix.child_table.ensure_grid_patches = () => {
	if (!millitrix.child_table._install_grid_prototypes()) {
		setTimeout(millitrix.child_table.ensure_grid_patches, 100);
	}
};
millitrix.child_table.ensure_grid_patches();
$(document).on("app_ready", millitrix.child_table.ensure_grid_patches);

/** Frappe hides empty read-only controls (status "None"). Millitrix: always show labels. */
millitrix.child_table.patch_readonly_always_visible = () => {
	if (millitrix.child_table._readonly_visibility_patched) {
		return;
	}
	millitrix.child_table._readonly_visibility_patched = true;
	const orig_get_status = frappe.ui.form.Control.prototype.get_status;
	frappe.ui.form.Control.prototype.get_status = function (explain) {
		const status = orig_get_status.call(this, explain);
		if (
			status === "None" &&
			this.df?.read_only &&
			!this.df?.hidden &&
			millitrix.child_table.is_millitrix_form(this.frm)
		) {
			return "Read";
		}
		return status;
	};
};
millitrix.child_table.patch_readonly_always_visible();

millitrix.child_table.table_fields = (frm) => {
	if (!frm?.meta?.fields) {
		return [];
	}
	return frm.meta.fields
		.filter((df) => df.fieldtype === "Table" && !df.hidden)
		.map((df) => df.fieldname);
};

millitrix.child_table.is_data_field = (df) =>
	Boolean(
		df &&
			!df.hidden &&
			!millitrix.child_table.LAYOUT_FIELDS.includes(df.fieldtype)
	);

millitrix.child_table.hidden_fields = (grid) => {
	const visible = new Set((grid.visible_columns || []).map((col) => col[0].fieldname));
	const excluded = new Set(
		millitrix.child_table.hint_excluded_fieldnames(grid.frm, grid.df?.fieldname)
	);
	return (grid.docfields || []).filter(
		(df) =>
			millitrix.child_table.is_data_field(df) &&
			!df.in_list_view &&
			!visible.has(df.fieldname) &&
			!excluded.has(df.fieldname)
	);
};

millitrix.child_table.render_hidden_hint = (grid) => {
	grid?.wrapper?.closest(".grid-field")?.find(".millitrix-hidden-fields-hint").remove();
	return true;
};

millitrix.child_table.ensure_default_rows = (frm, table_fields) => {
	if (!frm.is_new() || frm.doc.docstatus > 0) {
		return false;
	}

	let changed = false;
	for (const fieldname of table_fields) {
		const skip = millitrix.child_table.SKIP_AUTO_ADD[frm.doctype];
		if (skip?.includes(fieldname)) {
			continue;
		}
		const rows = frm.doc[fieldname] || [];
		if (!rows.length) {
			frm.add_child(fieldname);
			changed = true;
		}
	}
	return changed;
};

millitrix.child_table.refresh_table_hints = (frm, table_fields) => {
	let all_ready = true;
	for (const fieldname of table_fields) {
		const grid = frm.fields_dict[fieldname]?.grid;
		if (!grid) {
			all_ready = false;
			continue;
		}
		millitrix.child_table.reset_grid_columns(grid);
		millitrix.child_table.apply_grid_reqd_guard(grid);
		millitrix.child_table.ensure_grid_totals_hook(grid);
		millitrix.child_table.render_grid_totals(grid);
		if (!millitrix.child_table.render_hidden_hint(grid)) {
			all_ready = false;
		}
	}
	return all_ready;
};

millitrix.child_table.apply = (frm, attempt = 0) => {
	if (!millitrix.child_table.is_millitrix_form(frm)) {
		return;
	}

	const table_fields = millitrix.child_table.table_fields(frm);
	if (!table_fields.length) {
		return;
	}

	const changed = millitrix.child_table.ensure_default_rows(frm, table_fields);
	if (changed) {
		frm.refresh_fields(table_fields);
	}

	const hints_ready = millitrix.child_table.refresh_table_hints(frm, table_fields);
	if (!hints_ready && attempt < 50) {
		setTimeout(() => millitrix.child_table.apply(frm, attempt + 1), 150);
	}
};

/** Refresh footer totals when any child-table cell changes in the model. */
millitrix.child_table.patch_child_row_model_totals = () => {
	if (millitrix.child_table._model_totals_patched) {
		return;
	}
	millitrix.child_table._model_totals_patched = true;
	const orig_set_value = frappe.model.set_value;
	frappe.model.set_value = function (doctype, docname, fieldname, value, fieldtype, skip_dirty_trigger) {
		const out = orig_set_value.apply(this, arguments);
		millitrix.child_table._after_child_model_set_value(doctype, docname, fieldname);
		return out;
	};
};

millitrix.child_table._after_child_model_set_value = (doctype, docname, fieldname) => {
	let child_doctype = doctype;
	if ($.isPlainObject(doctype)) {
		child_doctype = doctype.doctype;
	}
	const meta = frappe.get_meta(child_doctype);
	if (!meta?.istable || meta?.module !== "Millitrix ERP" || !cur_frm) {
		return;
	}
	for (const [tf, field] of Object.entries(cur_frm.fields_dict || {})) {
		if (field?.df?.fieldtype === "Table" && field?.df?.options === child_doctype) {
			millitrix.child_table.schedule_render_grid_totals(cur_frm, [tf]);
			break;
		}
	}
};

millitrix.child_table.setup = (frm) => {
	if (!millitrix.child_table.is_millitrix_form(frm)) {
		return;
	}

	const prev = millitrix.child_table._setup_attempts.get(frm) || 0;
	millitrix.child_table._setup_attempts.set(frm, prev + 1);
	millitrix.child_table.apply(frm, 0);
};

millitrix.child_table.bind_grid_total_events = () => {
	if (millitrix.child_table._grid_total_events_bound) {
		return;
	}
	millitrix.child_table._grid_total_events_bound = true;

	millitrix.child_table.patch_child_row_model_totals();

	$(document).on("grid-row-render", (_e, grid_row) => {
		const grid = grid_row?.grid;
		if (grid && millitrix.child_table.uses_auto_totals(grid)) {
			millitrix.child_table.bind_grid_live_totals(grid);
			millitrix.child_table.ensure_grid_total_row(grid);
		}
		if (grid && millitrix.child_table.is_millitrix_grid(grid)) {
			millitrix.child_table.normalize_data_row(grid_row?.row, grid);
			millitrix.child_table.normalize_all_grid_rows(grid);
		}
	});
};
millitrix.child_table.bind_grid_total_events();
millitrix.child_table.bind_grid_dropdown_portal();

$(document).on("form-load form-refresh", function (_e, frm) {
	millitrix.child_table.setup(frm);
});
