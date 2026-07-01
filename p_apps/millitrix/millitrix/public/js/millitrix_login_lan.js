// Login page — server PC uses millitrix.local; copy LAN IP for phone/other laptops.
// Copyright (c) 2026, Millitrix and contributors

(function () {
	if (!window.location.pathname.startsWith("/login")) {
		return;
	}

	const is_server_host = () => {
		const host = (window.location.hostname || "").toLowerCase();
		return host === "millitrix.local" || host === "local.mill" || host === "127.0.0.1" || host === "localhost";
	};

	const copy_text = async (text) => {
		try {
			await navigator.clipboard.writeText(text);
			frappe.show_alert({ message: __("Copied"), indicator: "green" });
		} catch (e) {
			const input = document.createElement("textarea");
			input.value = text;
			document.body.appendChild(input);
			input.select();
			document.execCommand("copy");
			input.remove();
			frappe.show_alert({ message: __("Copied"), indicator: "green" });
		}
	};

	const render_lan_box = (host, data) => {
		if (!data.enabled || !data.ip) {
			return;
		}

		const local_label = `${data.local_host}:${data.port}`;
		const network_url = data.ip_login_url || `http://${data.ip}:${data.port}/login`;
		let box = document.getElementById("millitrix-lan-access");

		if (!box) {
			box = document.createElement("div");
			box.id = "millitrix-lan-access";
			box.className = "millitrix-lan-access text-center mt-4";
			box.innerHTML = `
				<div class="text-muted small millitrix-lan-local">${__("This PC")}: ${frappe.utils.escape_html(local_label)}</div>
				<div class="text-muted small mt-2 mb-1">${__(
					"Hotspot / LAN cable — other devices paste in browser"
				)}</div>
				<div class="millitrix-lan-row">
					<span class="millitrix-lan-ip"></span>
					<button type="button" class="btn btn-default btn-sm millitrix-lan-copy">${__(
						"Copy"
					)}</button>
				</div>
			`;
			host.appendChild(box);
			box.querySelector(".millitrix-lan-copy").addEventListener("click", () => {
				const url = box.dataset.networkUrl || network_url;
				copy_text(url);
			});
		}

		box.dataset.networkUrl = network_url;
		const ip_el = box.querySelector(".millitrix-lan-ip");
		if (ip_el) {
			ip_el.textContent = network_url;
		}
	};

	const refresh_lan_access = (host) => {
		frappe.call({
			method: "millitrix.api.lan.get_lan_access",
			callback(r) {
				render_lan_box(host, r.message || {});
			},
		});
	};

	frappe.ready(() => {
		// Only on server laptop (millitrix.local). Mobile opens IP directly — no extra box.
		if (!is_server_host()) {
			return;
		}

		const host = document.querySelector(".page-card") || document.querySelector(".for-login");
		if (!host) {
			return;
		}

		refresh_lan_access(host);
		// WiFi change → IP updates on login page without restart.
		setInterval(() => refresh_lan_access(host), 20000);
	});
})();
