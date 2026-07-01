#!/usr/bin/env python3
"""Read-only Oracle Forms to Millitrix parity audit.

This script intentionally does not patch DocTypes or database state. It extracts
evidence from the phase-one Oracle Forms folder and compares that evidence with
the current Millitrix custom Frappe app metadata.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


APP_ROOT = Path(__file__).resolve().parents[1]
APPS_ROOT = APP_ROOT.parent
DEFAULT_SOURCE = APPS_ROOT / "TAHSEEN BHAI" / "Documents"
DEFAULT_DOCS = APP_ROOT / "docs"

TRIGGER_RE = re.compile(
	r"(PRE-INSERT|PRE-UPDATE|PRE-QUERY|POST-QUERY|WHEN-[A-Z-]+|ON-CHECK-DELETE-MASTER|KEY-[A-Z-]+)"
	r"\s*(?:\(([^)]+)\))?"
)
TABLE_RE = re.compile(r"\b(?:FROM|UPDATE|INTO|TABLE)\s+([A-Z][A-Z0-9_]{2,})\b")
PROCEDURE_RE = re.compile(r"\bPROCEDURE\s+([A-Z][A-Z0-9_]{2,})\b", re.IGNORECASE)
REPORT_RE = re.compile(r"UPPER\(''([A-Za-z0-9_]+)''\)")
ORACLE_REF_RE = re.compile(r"Oracle\s+([A-Za-z0-9_./ -]+\.(?:fmb|fmx|RDF|rdf|rep))")
FILE_REF_RE = re.compile(r"([A-Za-z0-9_]+\.(?:fmb|fmx|RDF|rdf|rep))")
FIELD_TOKEN_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")

NOISE_TOKENS = {
	"BEGIN",
	"DECLARE",
	"END",
	"FORM50",
	"FORMS40",
	"FORMS4C",
	"FORMS4G",
	"FORMS4W",
	"FORM_SUCCESS",
	"FORM_TRIGGER_FAILURE",
	"INIT",
	"NOT",
	"PKG",
	"RAISE",
	"SQLFORMS",
	"STANDARD",
	"THEN",
	"VARCHAR2",
}

FORM_TO_DOCTYPES = {
	"CrashRefine.fmb": ["Crashing Refine", "Crash Refine Input", "Crash Refine Output"],
	"GatePass.fmb": ["In Out Gate Pass", "Gate Pass Detail"],
	"POCancel.fmb": ["PO Cancellation", "PO Cancellation Detail"],
	"Pay_PaySlip.fmb": ["PaySlip", "PaySlip Detail"],
	"Project_Menus.fmb": ["Menu", "Module", "Document Type"],
	"PurchInvoice.fmb": ["Purchase Invoice", "Purchase Invoice Detail", "Document Transaction"],
	"PurchOrder.fmb": ["Purchase Order"],
	"PurchOtherBill.fmb": ["Purchase Other Bill", "Purchase Other Bill Detail", "Document Transaction"],
	"PurchParaForm.fmb": ["Purch Parameter Form"],
	"PurchRetOtherBill.fmb": [
		"Purchase Return Other Bill",
		"Purchase Other Bill Return Detail",
		"Document Transaction",
	],
	"PurchReturn.fmb": ["Purchase Return", "Purchase Return Detail", "Document Transaction"],
	"SOCancel.fmb": ["SO Cancellation", "SO Cancellation Detail"],
	"SalesInvoice.fmb": ["Sales Invoice", "Sales Invoice Detail", "Document Transaction"],
	"SalesOrder.fmb": ["Sales Order"],
	"SalesOtherBill.fmb": ["Sales Other Bill", "Sales Other Bill Detail", "Document Transaction"],
	"SalesParaForm.fmb": ["Sales Parameter Form"],
	"SalesRetOtherBill.fmb": [
		"Sales Return Other Bill",
		"Sales Other Bill Return Detail",
		"Document Transaction",
	],
	"SalesReturn.fmb": ["Sales Return", "Sales Return Detail", "Document Transaction"],
	"StockParaForm.fmb": ["Stock Parameter Form"],
	"StockTransfer.fmb": ["Stock Transfer Note", "Stock Transfer Detail", "Document Transaction"],
	"Stock_Adjustment.fmb": ["Stock Adjustment", "Stock Adjustment Detail"],
}

DOC_EVENT_HINTS = {
	"PRE-INSERT": "before_insert/autoname",
	"PRE-UPDATE": "validate/before_save",
	"PRE-QUERY": "permission query/list filters",
	"POST-QUERY": "fetch/denormalized display values",
	"WHEN-VALIDATE-ITEM": "field validation/client or server helper",
	"WHEN-VALIDATE-RECORD": "document validate",
	"WHEN-CHECKBOX-CHANGED": "client script state change",
	"WHEN-RADIO-CHANGED": "client script state change",
	"WHEN-LIST-CHANGED": "client script state change",
	"ON-CHECK-DELETE-MASTER": "Frappe link/child table restrictions",
	"KEY-COMMIT": "save/submit action",
}


@dataclass
class FieldInfo:
	fieldname: str
	label: str | None
	fieldtype: str | None
	options: str | None
	reqd: bool
	read_only: bool
	hidden: bool


@dataclass
class DocTypeInfo:
	name: str
	path: str
	module: str | None
	istable: bool
	is_submittable: bool
	autoname: str | None
	classification: str
	table_fields: list[dict[str, str | None]]
	fields: list[FieldInfo]


@dataclass
class FormInfo:
	filename: str
	path: str
	kind: str
	triggers: list[dict[str, str]]
	trigger_summary: dict[str, int]
	sql_tables: list[str]
	procedures: list[str]
	reports: list[str]
	field_tokens: list[str]
	mapped_doctypes: list[str]
	matched_doctypes: list[str]
	missing_doctypes: list[str]
	parity_notes: list[str]


def run_strings(path: Path) -> str:
	return subprocess.check_output(["strings", "-n", "4", str(path)], text=True, errors="replace")


def unique_ordered(values: Iterable[str]) -> list[str]:
	seen: set[str] = set()
	out: list[str] = []
	for value in values:
		if not value or value in seen:
			continue
		seen.add(value)
		out.append(value)
	return out


def normalize_oracle_ref(ref: str) -> str:
	parts = [part.strip() for part in ref.strip().replace("\\", "/").split("/")]
	return parts[-1] if parts else ref.strip()


def extract_forms(source: Path, doctype_names: set[str]) -> list[FormInfo]:
	forms: list[FormInfo] = []
	for form_path in sorted(source.glob("*.fmb")):
		text = run_strings(form_path)
		triggers = [
			{"name": match.group(1), "target": (match.group(2) or "").strip()}
			for match in TRIGGER_RE.finditer(text)
		]
		trigger_counts = Counter(trigger["name"] for trigger in triggers)
		sql_tables = sorted(set(TABLE_RE.findall(text)))
		procedures = sorted({match.group(1).upper() for match in PROCEDURE_RE.finditer(text)})
		reports = sorted(set(REPORT_RE.findall(text)))
		tokens = [
			token
			for token in FIELD_TOKEN_RE.findall(text)
			if token not in NOISE_TOKENS and not token.startswith("P0_") and not token.startswith("P1_")
		]
		field_tokens = unique_ordered(tokens)[:140]
		mapped = FORM_TO_DOCTYPES.get(form_path.name, [])
		matched = [doctype for doctype in mapped if doctype in doctype_names or doctype.endswith(" Parameter Form")]
		missing = [doctype for doctype in mapped if doctype not in doctype_names and not doctype.endswith(" Parameter Form")]
		forms.append(
			FormInfo(
				filename=form_path.name,
				path=str(form_path),
				kind="Oracle Forms source",
				triggers=triggers,
				trigger_summary=dict(sorted(trigger_counts.items())),
				sql_tables=sql_tables,
				procedures=procedures,
				reports=reports,
				field_tokens=field_tokens,
				mapped_doctypes=mapped,
				matched_doctypes=matched,
				missing_doctypes=missing,
				parity_notes=build_form_notes(triggers, sql_tables, procedures),
			)
		)
	return forms


def build_form_notes(triggers: list[dict[str, str]], sql_tables: list[str], procedures: list[str]) -> list[str]:
	trigger_names = {trigger["name"] for trigger in triggers}
	notes: list[str] = []
	for trigger_name, hint in DOC_EVENT_HINTS.items():
		if trigger_name in trigger_names:
			notes.append(f"{trigger_name} should map to {hint}.")
	if "DOCTRANSACTION" in sql_tables:
		notes.append("Uses DOCTRANSACTION; verify GL/document ledger creation on submit.")
	if "IN_STORE_ITEMS" in sql_tables or "VIEW_US_STOCK" in sql_tables:
		notes.append("Uses stock tables; verify stock balance validation and stock ledger mutation.")
	if "USER_STORES" in sql_tables or "USER_LOCATIONS" in sql_tables or "USERSPRIVILEGES" in sql_tables:
		notes.append("Uses Oracle user access tables; verify Frappe role, location, and store permissions.")
	if any(proc.endswith("SUBMIT") or proc == "SUBMIT" for proc in procedures):
		notes.append("Has Oracle submit procedure; verify docstatus submit flow and posted lock behavior.")
	return unique_ordered(notes)


def load_doctypes() -> dict[str, DocTypeInfo]:
	doctype_root = APP_ROOT / "millitrix_erp" / "doctype"
	out: dict[str, DocTypeInfo] = {}
	for json_path in sorted(doctype_root.glob("*/*.json")):
		data = json.loads(json_path.read_text())
		name = data.get("name") or data.get("doctype") or json_path.parent.name
		fields = [
			FieldInfo(
				fieldname=field.get("fieldname") or "",
				label=field.get("label"),
				fieldtype=field.get("fieldtype"),
				options=field.get("options"),
				reqd=bool(field.get("reqd")),
				read_only=bool(field.get("read_only")),
				hidden=bool(field.get("hidden")),
			)
			for field in data.get("fields", [])
		]
		table_fields = [
			{"fieldname": field.fieldname, "options": field.options}
			for field in fields
			if field.fieldtype == "Table"
		]
		istable = bool(data.get("istable"))
		is_submittable = bool(data.get("is_submittable"))
		out[name] = DocTypeInfo(
			name=name,
			path=str(json_path),
			module=data.get("module"),
			istable=istable,
			is_submittable=is_submittable,
			autoname=data.get("autoname"),
			classification=classify_doctype(name, istable, is_submittable, table_fields),
			table_fields=table_fields,
			fields=fields,
		)
	return out


def classify_doctype(
	name: str,
	istable: bool,
	is_submittable: bool,
	table_fields: list[dict[str, str | None]],
) -> str:
	if istable:
		return "Child table"
	if name in {"Document Transaction", "Stock Ledger Entry", "Stock In Hand", "Report Parameter"}:
		return "Ledger/system generated"
	if "Parameter" in name or name in {"Menu", "Module", "Document Type"}:
		return "Report/parameter helper"
	if name in {
		"Location",
		"Party",
		"Party Category",
		"Item Setup",
		"Item Class",
		"Store Setup",
		"Store Types",
		"City Setup",
		"Chart of Accounting",
		"Employee Setup",
		"Employee Category",
		"Departments",
		"Designation",
		"Bank",
		"Bank Account",
		"Bank Branch",
		"Mill Information",
		"User Rights",
	}:
		return "Master/setup"
	if is_submittable:
		return "Core migrated transaction"
	if table_fields:
		return "Probably duplicate or over-modeled"
	return "Master/setup"


def scan_oracle_references(source_files: set[str]) -> dict[str, list[str]]:
	refs: dict[str, list[str]] = defaultdict(list)
	for path in sorted(APP_ROOT.rglob("*")):
		if not path.is_file():
			continue
		if path.suffix.lower() not in {".py", ".js", ".json", ".md", ".txt"}:
			continue
		if "__pycache__" in path.parts:
			continue
		try:
			text = path.read_text(errors="replace")
		except UnicodeDecodeError:
			continue
		for match in ORACLE_REF_RE.finditer(text):
			for file_ref in FILE_REF_RE.findall(match.group(1)):
				ref = normalize_oracle_ref(file_ref)
				if ref not in source_files:
					refs[ref].append(str(path.relative_to(APP_ROOT)))
	return dict(sorted((ref, unique_ordered(paths)) for ref, paths in refs.items()))


def find_extra_doctypes(doctypes: dict[str, DocTypeInfo], forms: list[FormInfo]) -> list[str]:
	mapped = {doctype for form in forms for doctype in form.mapped_doctypes}
	return sorted(name for name in doctypes if name not in mapped)


def find_possible_duplicates(doctypes: dict[str, DocTypeInfo]) -> list[str]:
	groups: dict[str, list[str]] = defaultdict(list)
	for name in doctypes:
		key = re.sub(r"\b(Purchase|Sales|Paid|Received|Payable|Receivable|Payment|Receipt)\b", "", name)
		key = re.sub(r"\s+", " ", key).strip().lower()
		groups[key].append(name)
	return sorted(name for names in groups.values() if len(names) > 1 for name in names)


def build_audit(source: Path) -> dict:
	doctypes = load_doctypes()
	source_files = {path.name for path in source.glob("*.fmb")} | {path.name for path in source.glob("*.fmx")}
	forms = extract_forms(source, set(doctypes))
	missing_refs = scan_oracle_references(source_files)
	class_counts = Counter(info.classification for info in doctypes.values())
	return {
		"source": str(source),
		"assumptions": [
			"Phase one uses only TAHSEEN BHAI/Documents as authoritative Oracle source.",
			"Millitrix remains a custom Frappe v15 app; ERPNext migration is out of scope.",
			"Missing Oracle references are evidence gaps, not automatic cleanup instructions.",
			"No deletion or schema mutation is performed by this audit.",
		],
		"summary": {
			"oracle_fmb_files": len(list(source.glob("*.fmb"))),
			"oracle_fmx_files": len(list(source.glob("*.fmx"))),
			"doctype_count": len(doctypes),
			"submittable_doctypes": sum(1 for item in doctypes.values() if item.is_submittable),
			"child_table_doctypes": sum(1 for item in doctypes.values() if item.istable),
			"classification_counts": dict(sorted(class_counts.items())),
		},
		"forms": [asdict(form) for form in forms],
		"doctypes": {name: asdict(info) for name, info in sorted(doctypes.items())},
		"extra_doctypes": find_extra_doctypes(doctypes, forms),
		"possible_duplicates": find_possible_duplicates(doctypes),
		"evidence_missing": missing_refs,
	}


def render_markdown(audit: dict) -> str:
	lines = [
		"# Millitrix Oracle FMB Parity Audit",
		"",
		"Generated by `scripts/audit_oracle_fmb_parity.py`.",
		"",
		"## Summary",
		"",
	]
	summary = audit["summary"]
	lines.extend(
		[
			f"- Source folder: `{audit['source']}`",
			f"- Oracle `.fmb` files scanned: {summary['oracle_fmb_files']}",
			f"- Oracle `.fmx` files present: {summary['oracle_fmx_files']}",
			f"- Millitrix DocTypes scanned: {summary['doctype_count']}",
			f"- Submittable DocTypes: {summary['submittable_doctypes']}",
			f"- Child table DocTypes: {summary['child_table_doctypes']}",
			"",
			"## Assumptions",
			"",
		]
	)
	lines.extend(f"- {item}" for item in audit["assumptions"])
	lines.extend(["", "## Matched", ""])
	for form in audit["forms"]:
		matched = ", ".join(form["matched_doctypes"]) or "None"
		lines.append(f"- `{form['filename']}` -> {matched}")
	lines.extend(["", "## Missing", ""])
	missing_lines = [
		f"- `{form['filename']}` expected missing DocTypes: {', '.join(form['missing_doctypes'])}"
		for form in audit["forms"]
		if form["missing_doctypes"]
	]
	lines.extend(missing_lines or ["- No mapped phase-one DocTypes are missing."])
	lines.extend(["", "## Extra", ""])
	lines.append(
		"These DocTypes are not directly mapped to the phase-one Oracle source files. "
		"They may be masters, ledgers, reports, or functionality from missing Oracle evidence."
	)
	lines.append("")
	for name in audit["extra_doctypes"]:
		info = audit["doctypes"][name]
		lines.append(f"- `{name}` - {info['classification']}")
	lines.extend(["", "## Duplicate Or Over-Modeled Candidates", ""])
	for name in audit["possible_duplicates"]:
		info = audit["doctypes"][name]
		lines.append(f"- `{name}` - {info['classification']}")
	if not audit["possible_duplicates"]:
		lines.append("- None detected by name grouping.")
	lines.extend(["", "## Needs Frappe-Native Simplification", ""])
	lines.extend(
		[
			"- Prefer Frappe `docstatus` and submit/cancel hooks over Oracle `POSTED` UI state.",
			"- Keep ledger and stock tables custom because ERPNext is not installed.",
			"- Keep user/location/store access in Frappe permission hooks instead of Oracle `CHECK_QUERY` patterns.",
			"- Review report parameter pages as Frappe report filters before adding more custom parameter DocTypes.",
			"- Treat duplicate payment/receipt/advance variants as consolidation candidates only after parity evidence is reviewed.",
		]
	)
	lines.extend(["", "## Evidence Missing", ""])
	if audit["evidence_missing"]:
		for ref, paths in audit["evidence_missing"].items():
			lines.append(f"- `{ref}` referenced by {', '.join(f'`{path}`' for path in paths[:8])}")
	else:
		lines.append("- No missing Oracle source references found in Millitrix code.")
	lines.extend(["", "## Per-Form Audit", ""])
	for form in audit["forms"]:
		lines.extend(render_form_section(form, audit["doctypes"]))
	lines.extend(["", "## DocType Classification", ""])
	for classification, count in summary["classification_counts"].items():
		lines.append(f"- {classification}: {count}")
	lines.append("")
	return "\n".join(lines)


def render_form_section(form: dict, doctypes: dict) -> list[str]:
	lines = [
		f"### {form['filename']}",
		"",
		f"- Mapped DocTypes: {', '.join(f'`{item}`' for item in form['mapped_doctypes']) or 'None'}",
		f"- Matched DocTypes: {', '.join(f'`{item}`' for item in form['matched_doctypes']) or 'None'}",
		f"- Oracle SQL tables: {', '.join(f'`{item}`' for item in form['sql_tables'][:30]) or 'None'}",
		f"- Oracle procedures: {', '.join(f'`{item}`' for item in form['procedures'][:20]) or 'None'}",
		f"- Report targets: {', '.join(f'`{item}`' for item in form['reports']) or 'None found'}",
		"",
		"Trigger summary:",
	]
	for name, count in form["trigger_summary"].items():
		lines.append(f"- `{name}`: {count}")
	lines.append("")
	lines.append("Parity notes:")
	for note in form["parity_notes"] or ["No high-risk parity notes detected."]:
		lines.append(f"- {note}")
	lines.append("")
	for doctype_name in form["matched_doctypes"]:
		if doctype_name not in doctypes:
			lines.append(f"- `{doctype_name}` is represented as a Frappe Page or report launcher, not a DocType JSON.")
			continue
		info = doctypes[doctype_name]
		lines.append(
			f"- `{doctype_name}`: {info['classification']}; "
			f"fields={len(info['fields'])}; submittable={bool(info['is_submittable'])}; "
			f"child tables={', '.join(field['options'] or field['fieldname'] for field in info['table_fields']) or 'none'}"
		)
	lines.append("")
	return lines


def write_outputs(audit: dict, docs_dir: Path) -> tuple[Path, Path]:
	docs_dir.mkdir(parents=True, exist_ok=True)
	json_path = docs_dir / "oracle_parity_audit.json"
	md_path = docs_dir / "oracle_parity_audit.md"
	json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
	md_path.write_text(render_markdown(audit))
	return md_path, json_path


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
	parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS)
	parser.add_argument("--write", action="store_true", help="write docs/oracle_parity_audit.md and .json")
	args = parser.parse_args()

	if not args.source.is_dir():
		raise SystemExit(f"Oracle source folder not found: {args.source}")

	audit = build_audit(args.source)
	if args.write:
		md_path, json_path = write_outputs(audit, args.docs_dir)
		print(f"Wrote {md_path}")
		print(f"Wrote {json_path}")
	else:
		print(render_markdown(audit))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
