// Millitrix desk branding — navbar logo + favicon
(function () {
	const logo = () => frappe.boot && frappe.boot.app_logo_url;

	const set_favicon = () => {
		const url = logo();
		if (!url) return;
		$('link[rel="icon"], link[rel="shortcut icon"]').remove();
		$('<link rel="icon" type="image/svg+xml">').attr("href", url).appendTo("head");
	};

	frappe.ready(() => {
		const url = logo();
		if (!url) return;
		$(".navbar-brand .app-logo").attr("src", url);
		set_favicon();
	});
})();
