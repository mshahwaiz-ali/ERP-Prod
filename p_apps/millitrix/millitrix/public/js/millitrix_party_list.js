// Copyright (c) 2026, Millitrix and contributors
// Broker / Supplier / Customer list filters (Oracle All_Party split screens).

frappe.provide("millitrix.party_list");

const PCAT_STORAGE_KEY = "millitrix_party_pcat";

millitrix.party_list.SETUP = {
	"11": { title: "Broker Setup", label: "Broker", formTitle: "Broker Information" },
	"12": { title: "Supplier Setup", label: "Supplier", formTitle: "Supplier Information" },
	"13": { title: "Customer Setup", label: "Customer", formTitle: "Customer Information" },
};

millitrix.party_list.HEADER_LABELS = {
	"11": {
		city_name: "",
	},
	"12": {
		party_name: "Name",
		city_name: "",
	},
	"13": {
		party_name: "Name",
		city_name: "",
	},
};

millitrix.party_list.apply_header_labels = function (frm, pcat_id) {
	const labels = millitrix.party_list.HEADER_LABELS[String(pcat_id || "")] || {};
	Object.entries(labels).forEach(([fieldname, label]) => {
		if (frm.fields_dict[fieldname]) {
			frm.set_df_property(fieldname, "label", label);
		}
	});
	if (frm.fields_dict.city_name && labels.city_name === "") {
		frm.set_df_property("city_name", "label", "");
	}
};

millitrix.party_list.apply_broker_item_grid = function (frm) {
	const grid = frm.fields_dict.party_items?.grid;
	if (!grid?.update_docfields_property) {
		return;
	}
	["itemcode", "item_name", "value_type_1", "value_1", "value_type_2", "value_2"].forEach(
		(field) => {
			grid.update_docfields_property(field, "hidden", 0);
		}
	);
	frm.refresh_field("party_items");
};

/** Customer / supplier — Item Code + Item Name only (no brokery columns). */
millitrix.party_list.apply_simple_party_item_grid = function (frm) {
	const grid = frm.fields_dict.party_items?.grid;
	if (!grid?.update_docfields_property) {
		return;
	}
	["itemcode", "item_name"].forEach((field) => {
		grid.update_docfields_property(field, "hidden", 0);
	});
	["value_type_1", "value_1", "value_type_2", "value_2"].forEach((field) => {
		grid.update_docfields_property(field, "hidden", 1);
	});
	frm.refresh_field("party_items");
};

millitrix.party_list.PARTY_ITEMS_PCATS = new Set(["11", "12", "13"]);

millitrix.party_list.configure_party_items = function (frm) {
	const pcat = String(frm.doc.pcat_id || "");
	const show = millitrix.party_list.PARTY_ITEMS_PCATS.has(pcat);
	frm.toggle_display("party_items", show);
	if (!show) {
		return;
	}
	if (pcat === "11") {
		millitrix.party_list.apply_broker_item_grid(frm);
	} else {
		millitrix.party_list.apply_simple_party_item_grid(frm);
	}
};

/** Workspace card / shortcut labels → party category (Oracle split screens). */
millitrix.party_list.LABEL_TO_PCAT = {
	"Broker Setup": "11",
	"Supplier Setup": "12",
	"Customer Setup": "13",
};

millitrix.party_list.set_context = (pcat_id) => {
	if (pcat_id && millitrix.party_list.SETUP[String(pcat_id)]) {
		sessionStorage.setItem(PCAT_STORAGE_KEY, String(pcat_id));
	}
};

millitrix.party_list.get_context = () => {
	const pcat = sessionStorage.getItem(PCAT_STORAGE_KEY);
	return pcat && millitrix.party_list.SETUP[pcat] ? pcat : null;
};

millitrix.party_list.meta = (pcat_id) => {
	return millitrix.party_list.SETUP[String(pcat_id || "")] || null;
};

millitrix.party_list.open = (pcat_id) => {
	millitrix.party_list.set_context(pcat_id);
	frappe.route_options = { millitrix_pcat_id: String(pcat_id) };
	frappe.set_route("List", "Party");
};

millitrix.party_list.open_new = (pcat_id) => {
	millitrix.party_list.set_context(pcat_id);
	frappe.model.with_doctype("Party", () => {
		const doc = frappe.model.get_new_doc("Party");
		doc.pcat_id = String(pcat_id);
		frappe.route_options = { millitrix_pcat_id: String(pcat_id) };
		frappe.set_route("Form", doc.doctype, doc.name);
	});
};

millitrix.party_list.open_from_label = (label) => {
	const pcat = millitrix.party_list.LABEL_TO_PCAT[(label || "").trim()];
	if (pcat) {
		millitrix.party_list.open(pcat);
	}
};

frappe.listview_settings["Party"] = {
	onload(listview) {
		const pcat = frappe.route_options?.millitrix_pcat_id || millitrix.party_list.get_context();
		if (!pcat || !millitrix.party_list.SETUP[pcat]) {
			sessionStorage.removeItem(PCAT_STORAGE_KEY);
			return;
		}
		millitrix.party_list.set_context(pcat);
		listview.millitrix_pcat_id = pcat;
		listview.filter_area.add([["Party", "pcat_id", "=", pcat]]);
		const meta = millitrix.party_list.SETUP[pcat];
		listview.page.set_title(__(meta.title));
		delete frappe.route_options.millitrix_pcat_id;
	},

	refresh(listview) {
		const pcat = listview.millitrix_pcat_id;
		if (!pcat) {
			return;
		}
		const meta = millitrix.party_list.SETUP[pcat];
		listview.page.set_primary_action(
			__("New Party"),
			() => millitrix.party_list.open_new(pcat),
			"add"
		);
	},
};

frappe.ready(() => {
	// Workspace links (Master Setups cards)
	$(document).on("click", "a.link-item", function (e) {
		const label = $(this).attr("title");
		if (!millitrix.party_list.LABEL_TO_PCAT[label]) {
			return;
		}
		e.preventDefault();
		millitrix.party_list.open_from_label(label);
	});

	// Workspace shortcuts
	$(document).on("click", ".shortcut-widget-box", function (e) {
		const label = $(this).attr("aria-label");
		if (!millitrix.party_list.LABEL_TO_PCAT[label]) {
			return;
		}
		e.preventDefault();
		e.stopImmediatePropagation();
		millitrix.party_list.open_from_label(label);
		return false;
	});
});
