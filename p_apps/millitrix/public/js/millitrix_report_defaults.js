// Oracle :Global.Location_Id — session location, saved para filters, dependent links.
frappe.provide("millitrix.report_defaults");

(function () {
	let scopePromise = null;

	millitrix.report_defaults.fetch_scope = function () {
		if (!scopePromise) {
			scopePromise = frappe
				.xcall("millitrix.api.user_context.get_user_scope")
				.then((scope) => scope || {})
				.catch(() => ({}));
		}
		return scopePromise;
	};

	millitrix.report_defaults.clear_scope_cache = function () {
		scopePromise = null;
	};

	millitrix.report_defaults.apply_session_location = function (query_report) {
		if (!query_report?.filters?.length) {
			return Promise.resolve(false);
		}

		const field = query_report.filters.find((f) => f.df?.fieldname === "location_id");
		if (!field || field.get_value()) {
			return Promise.resolve(false);
		}

		return millitrix.report_defaults.fetch_scope().then((scope) => {
			const loc = scope.location_id;
			if (!loc || field.get_value()) {
				return false;
			}
			query_report._no_refresh = true;
			field.set_value(loc);
			query_report._no_refresh = false;
			return true;
		});
	};

	millitrix.report_defaults.apply_saved_filters = function (query_report) {
		if (!query_report?.report_name || query_report._millitrix_saved_applied) {
			return Promise.resolve(false);
		}
		return frappe
			.xcall("millitrix.api.user_context.get_saved_filters_for_report", {
				report_name: query_report.report_name,
			})
			.then((saved) => {
				if (!saved || !query_report.filters?.length) {
					return false;
				}
				let applied = false;
				query_report._no_refresh = true;
				for (const filter of query_report.filters) {
					const key = filter.df?.fieldname;
					if (!key || filter.get_value()) {
						continue;
					}
					const value = saved[key];
					if (value !== undefined && value !== null && value !== "") {
						filter.set_value(value);
						applied = true;
					}
				}
				query_report._no_refresh = false;
				if (applied) {
					query_report._millitrix_saved_applied = true;
				}
				return applied;
			})
			.catch(() => false);
	};

	millitrix.report_defaults.apply_dependent_queries = function (query_report) {
		if (!query_report?.filters?.length) {
			return;
		}
		const by_field = {};
		query_report.filters.forEach((f) => {
			if (f.df?.fieldname) {
				by_field[f.df.fieldname] = f;
			}
		});

		const location_field = by_field.location_id;
		const store_field = by_field.storeid;
		if (store_field && location_field) {
			store_field.get_query = () => {
				const loc = location_field.get_value();
				return { filters: loc ? { location_id: loc } : {} };
			};
		}

		const party_filters = {
			supplierid: ["12"],
			customerid: ["13"],
			brokerid: ["11"],
		};
		Object.entries(party_filters).forEach(([fieldname, pcat]) => {
			const field = by_field[fieldname];
			if (!field) {
				return;
			}
			field.get_query = () => ({ filters: { pcat_id: ["in", pcat] } });
		});

		const party_field = by_field.partyid;
		if (party_field) {
			party_field.get_query = () => ({ filters: {} });
		}
	};

	millitrix.report_defaults.after_filters_ready = function (query_report) {
		millitrix.report_defaults.apply_dependent_queries(query_report);
		return millitrix.report_defaults.apply_saved_filters(query_report).then((saved) =>
			millitrix.report_defaults.apply_session_location(query_report).then((loc) => saved || loc)
		);
	};

	function patch_query_report() {
		if (!frappe.views?.QueryReport) {
			return;
		}
		const proto = frappe.views.QueryReport.prototype;
		if (proto.__millitrix_location_patched) {
			return;
		}
		proto.__millitrix_location_patched = true;

		const orig_refresh = proto.refresh_report;
		proto.refresh_report = function (route_options) {
			const result = orig_refresh.call(this, route_options);
			if (!result || !result.then) {
				return result;
			}
			return result.then(() =>
				millitrix.report_defaults.after_filters_ready(this).then((applied) => {
					if (applied) {
						this.refresh(true);
					}
				})
			);
		};
	}

	patch_query_report();
	$(document).on("app_ready", patch_query_report);
})();
