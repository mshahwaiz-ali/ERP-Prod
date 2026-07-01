// Copyright (c) 2026, Millitrix and contributors

function _party_context(frm) {
	const from_route = frappe.route_options?.millitrix_pcat_id;
	if (from_route && millitrix.party_list?.meta(from_route)) {
		millitrix.party_list.set_context(from_route);
		delete frappe.route_options.millitrix_pcat_id;
		return String(from_route);
	}
	const stored = millitrix.party_list?.get_context();
	if (stored && String(frm.doc.pcat_id || stored) === stored) {
		return stored;
	}
	return null;
}

function _apply_setup_form(frm) {
	const ctx = _party_context(frm);
	const meta = ctx ? millitrix.party_list.meta(ctx) : null;

	if (meta && frm.is_new() && !frm.doc.pcat_id) {
		frm.set_value("pcat_id", ctx);
	}

	if (meta) {
		frm.set_df_property("pcat_id", "hidden", 1);
		frm.set_df_property("pcat_id", "read_only", 1);
		const title = frm.is_new() ? __("New Party") : __(meta.formTitle);
		frm.page.set_title(title);
		millitrix.party_list.apply_header_labels(frm, ctx);
	} else {
		frm.set_df_property("pcat_id", "hidden", 0);
		frm.set_df_property("pcat_id", "read_only", 0);
	}

	millitrix.party_list.configure_party_items(frm);
	if (millitrix.child_table) {
		millitrix.child_table.setup(frm);
	}
}

frappe.ui.form.on("Party", {
	onload(frm) {
		_apply_setup_form(frm);
	},

	refresh(frm) {
		_apply_setup_form(frm);
	},

	pcat_id(frm) {
		const pcat = String(frm.doc.pcat_id || "");
		if (!millitrix.party_list.PARTY_ITEMS_PCATS.has(pcat) && frm.doc.party_items?.length) {
			frm.clear_table("party_items");
			frm.refresh_field("party_items");
		}
		millitrix.party_list.configure_party_items(frm);
	},
});
