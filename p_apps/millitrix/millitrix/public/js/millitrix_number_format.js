// Millitrix — whole numbers without .00; show decimals only when non-zero (max 2 dp).
frappe.provide("millitrix.number_format");

// Desk bundle has no frappe.ready (website-only); shim for early app_include scripts.
if (typeof frappe.ready !== "function") {
	frappe.ready = function (fn) {
		if (document.readyState === "complete" || document.readyState === "interactive") {
			fn();
		} else {
			$(fn);
		}
	};
}

millitrix.number_format.MAX_DECIMALS = 2;

millitrix.number_format.is_millitrix_doctype = (doctype) => {
	if (!doctype) {
		return false;
	}
	const meta = frappe.get_meta(doctype);
	return Boolean(meta && meta.module === "Millitrix ERP");
};

millitrix.number_format.in_millitrix_context = (docfield, doc, control) => {
	if (docfield && millitrix.number_format.is_millitrix_doctype(docfield.parent)) {
		return true;
	}
	if (doc && millitrix.number_format.is_millitrix_doctype(doc.doctype)) {
		return true;
	}
	if (control) {
		if (millitrix.number_format.is_millitrix_doctype(control.doctype)) {
			return true;
		}
		const frm = control.frm || control.grid?.frm;
		if (frm?.meta?.module === "Millitrix ERP") {
			return true;
		}
		if (control.grid?.meta?.istable && control.grid?.frm?.meta?.module === "Millitrix ERP") {
			return true;
		}
	}
	if (cur_frm?.meta?.module === "Millitrix ERP") {
		return true;
	}
	return false;
};

millitrix.number_format.is_numeric_field = (df) =>
	Boolean(df && ["Float", "Currency", "Percent", "Int"].includes(df.fieldtype));

millitrix.number_format.trim = (value, maxDecimals = millitrix.number_format.MAX_DECIMALS) => {
	if (value === null || value === undefined || value === "") {
		return "";
	}
	const n = flt(value, maxDecimals);
	if (isNaN(n)) {
		return "";
	}
	return String(parseFloat(n.toFixed(maxDecimals)));
};

millitrix.number_format.strip_trailing_decimal_zeros = (formatted, info) => {
	if (!formatted || !info?.decimal_str) {
		return formatted;
	}
	const dec = info.decimal_str;
	if (!formatted.includes(dec)) {
		return formatted;
	}
	const negative = formatted.startsWith("-");
	let body = negative ? formatted.slice(1) : formatted;
	const idx = body.lastIndexOf(dec);
	if (idx === -1) {
		return formatted;
	}
	const intPart = body.slice(0, idx);
	let fracPart = body.slice(idx + dec.length).replace(/0+$/, "");
	if (!fracPart) {
		return (negative ? "-" : "") + intPart;
	}
	return (negative ? "-" : "") + intPart + dec + fracPart;
};

millitrix.number_format.get_number_format_for_field = (docfield, doc) => {
	if (docfield?.fieldtype === "Currency") {
		return get_number_format(frappe.meta.get_field_currency(docfield, doc));
	}
	return get_number_format();
};

millitrix.number_format.format = (value, numberFormat, maxDecimals = millitrix.number_format.MAX_DECIMALS) => {
	const trimmed = millitrix.number_format.trim(value, maxDecimals);
	if (trimmed === "") {
		return "";
	}
	const nf = numberFormat || get_number_format();
	const info = get_number_format_info(nf);
	const parts = trimmed.split(".");
	const frac = (parts[1] || "").replace(/0+$/, "");
	const decimals = frac.length ? Math.min(frac.length, maxDecimals) : 0;
	const formatted = format_number(trimmed, nf, decimals);
	return millitrix.number_format.strip_trailing_decimal_zeros(formatted, info);
};

millitrix.number_format.strip_currency_symbols = (formatted) => {
	if (!formatted || typeof formatted !== "string") {
		return formatted;
	}
	let text = formatted.trim();
	// Remove currency symbol prefix/suffix (Rs, PKR, etc.)
	text = text.replace(/^(?:Rs\.?|PKR|USD|EUR|GBP|INR|AED|SAR)\s+/i, "");
	text = text.replace(/\s+(?:Rs\.?|PKR|USD|EUR|GBP|INR|AED|SAR)$/i, "");
	text = text.replace(/^[$€£₹]\s*/, "");
	text = text.replace(/\s*[$€£₹]$/, "");
	return text.trim();
};

/** Strip Rs and .00 from Frappe grid HTML: <div style='text-align: right'>Rs 0.00</div> */
millitrix.number_format.clean_html_display = (html, docfield) => {
	if (!html || typeof html !== "string") {
		return html;
	}
	const wrapped = html.match(/^(<div[^>]*>)([\s\S]*?)(<\/div>)$/i);
	const inner_raw = wrapped ? wrapped[2] : html;
	let inner = millitrix.number_format.strip_currency_symbols(inner_raw);
	inner = inner.replace(/,/g, "");
	const n = flt(inner);
	if (!n) {
		return "";
	}
	const plain = millitrix.number_format.format(n, null);
	if (!plain) {
		return "";
	}
	if (wrapped) {
		return wrapped[1] + plain + wrapped[3];
	}
	return plain;
};

millitrix.number_format.format_display = (value, docfield) => {
	if (value === null || value === undefined || value === "") {
		return "";
	}
	const n = flt(value);
	if (!n) {
		return "";
	}
	return millitrix.number_format.format(n, null);
};

millitrix.number_format.normalize_formatted = (formatted, docfield, doc) => {
	return millitrix.number_format.clean_html_display(formatted, docfield);
};

millitrix.number_format.cap_precision = (precision) => {
	const p = cint(precision);
	if (!p) {
		return millitrix.number_format.MAX_DECIMALS;
	}
	return Math.min(p, millitrix.number_format.MAX_DECIMALS);
};

millitrix.number_format.apply_patches = () => {
	if (millitrix.number_format._patched) {
		return;
	}
	if (!frappe.ui?.form?.ControlFloat?.prototype || !frappe.format) {
		return;
	}
	millitrix.number_format._patched = true;

	const wrapNumericFormatter = (fieldtype, origFormatter) =>
		function (value, docfield, options, doc) {
			if (!millitrix.number_format.in_millitrix_context(docfield, doc)) {
				return origFormatter(value, docfield, options, doc);
			}
			if (value === null || value === "") {
				return "";
			}
			return frappe.form.formatters._right(
				millitrix.number_format.format(value, null),
				options
			);
		};

	const origFloatFormatter = frappe.form.formatters.Float;
	frappe.form.formatters.Float = wrapNumericFormatter("Float", origFloatFormatter);

	const origCurrencyFormatter = frappe.form.formatters.Currency;
	frappe.form.formatters.Currency = wrapNumericFormatter("Currency", origCurrencyFormatter);

	const origPercentFormatter = frappe.form.formatters.Percent;
	frappe.form.formatters.Percent = function (value, docfield, options, doc) {
		if (!millitrix.number_format.in_millitrix_context(docfield, doc)) {
			return origPercentFormatter(value, docfield, options, doc);
		}
		if (value === null || value === "") {
			return "";
		}
		const formatted = millitrix.number_format.format(value, null);
		return frappe.form.formatters._right(`${formatted}%`, options);
	};

	const origFrappeFormat = frappe.format;
	frappe.format = function (value, df, options, doc) {
		if (
			millitrix.number_format.is_numeric_field(df) &&
			millitrix.number_format.in_millitrix_context(df, doc)
		) {
			const plain = millitrix.number_format.format_display(value, df);
			if (!plain) {
				return "";
			}
			return frappe.form.formatters._right(plain, options);
		}
		const formatted = origFrappeFormat(value, df, options, doc);
		if (
			millitrix.number_format.is_numeric_field(df) &&
			millitrix.number_format.in_millitrix_context(df, doc)
		) {
			return millitrix.number_format.normalize_formatted(formatted, df, doc);
		}
		return formatted;
	};

	const origFormatForInput = frappe.ui.form.ControlFloat.prototype.format_for_input;
	frappe.ui.form.ControlFloat.prototype.format_for_input = function (value) {
		if (!millitrix.number_format.in_millitrix_context(this.df, this.doc, this)) {
			return origFormatForInput.call(this, value);
		}
		if (value === null || value === undefined || value === "") {
			return "";
		}
		if (isNaN(Number(value))) {
			return "";
		}
		return millitrix.number_format.format(value, this.get_number_format());
	};

	const origGetPrecision = frappe.ui.form.ControlFloat.prototype.get_precision;
	frappe.ui.form.ControlFloat.prototype.get_precision = function () {
		const precision = origGetPrecision.call(this);
		if (!millitrix.number_format.in_millitrix_context(this.df, this.doc, this)) {
			return precision;
		}
		return millitrix.number_format.cap_precision(precision);
	};

	const origFormatNumber = window.format_number;
	window.format_number = function (v, format, decimals) {
		if (!millitrix.number_format.in_millitrix_context(null, null, { frm: cur_frm })) {
			return origFormatNumber(v, format, decimals);
		}
		const maxD = millitrix.number_format.cap_precision(decimals);
		const trimmed = millitrix.number_format.trim(v, maxD);
		if (trimmed === "") {
			return "";
		}
		const nf = format || get_number_format();
		const info = get_number_format_info(nf);
		const parts = trimmed.split(".");
		const frac = (parts[1] || "").replace(/0+$/, "");
		const useDecimals = frac.length ? Math.min(frac.length, maxD) : 0;
		const formatted = origFormatNumber(trimmed, nf, useDecimals);
		return millitrix.number_format.strip_trailing_decimal_zeros(formatted, info);
	};

	if (typeof window.format_currency === "function") {
		const origFormatCurrency = window.format_currency;
		window.format_currency = function (v, currency, decimals) {
			if (millitrix.number_format.in_millitrix_context(null, null, { frm: cur_frm })) {
				return millitrix.number_format.format_display(v) || "";
			}
			return origFormatCurrency(v, currency, decimals);
		};
	}

	// Desk bundle may attach here instead of window
	if (frappe.utils && typeof frappe.utils.format_currency === "function") {
		const origUtilCurrency = frappe.utils.format_currency;
		frappe.utils.format_currency = function (v, currency, decimals) {
			if (millitrix.number_format.in_millitrix_context(null, null, { frm: cur_frm })) {
				return millitrix.number_format.format_display(v) || "";
			}
			return origUtilCurrency(v, currency, decimals);
		};
	}
};

frappe.ready(() => {
	millitrix.number_format.apply_patches();
});

$(document).on("app_ready", () => {
	millitrix.number_format.apply_patches();
});
