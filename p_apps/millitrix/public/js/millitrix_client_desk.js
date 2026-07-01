// Millitrix Client — Awesome Bar: Millitrix routes only (boot filters can_read; drop Frappe shortcuts).
(function () {
	if (!frappe.boot || !frappe.boot.millitrix_client_search) {
		return;
	}

	const can_read = () => frappe.boot.user.can_read || [];
	const allowed = (doctype) => can_read().includes(doctype);

	frappe.provide("frappe.search.utils");

	const utils = frappe.search.utils;
	const origGetPages = utils.get_pages.bind(utils);

	utils.get_pages = function (keywords) {
		return origGetPages(keywords).filter((item) => {
			const route = item.route || [];
			if (route[0] === "List" && route[1]) {
				return allowed(route[1]);
			}
			return false;
		});
	};

	const origGetDashboards = utils.get_dashboards.bind(utils);
	utils.get_dashboards = function (keywords) {
		return origGetDashboards(keywords).filter((item) => {
			const route = item.route || [];
			return route[0] === "dashboard-view" && allowed(route[1]);
		});
	};
})();
