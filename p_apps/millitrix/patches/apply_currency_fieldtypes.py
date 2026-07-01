# Copyright (c) 2026, Millitrix and contributors
# A.6 — Oracle screenshots use Currency for money; keep Float for qty/weight.

from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "millitrix_erp" / "doctype"

# Money columns on transaction / master forms (screenshots_report.md Currency rows).
CURRENCY_FIELDNAMES = frozenset(
	{
		"amount",
		"debit",
		"credit",
		"balance",
		"docbalamnt",
		"suspense",
		"total_debit",
		"total_credit",
		"payable",
		"receivable",
		"salary",
		"creditlimit",
		"amntlimit",
		"purchrate",
		"salesrate",
		"movingrate",
		"rate",
		"bagrate",
		"dust_rate",
		"cartage",
		"totalamnt",
		"labouramnt",
		"brokeramnt",
		"brokerypayable",
		"bagamnt",
		"b_amount",
	}
)

# Qty / weight / mixed-unit brokery — stay Float.
KEEP_FLOAT = frozenset({"total_stock", "value_1", "value_2", "total_weight"})


def apply() -> None:
	changed_doctypes: list[str] = []
	for folder in sorted(BASE.iterdir()):
		if not folder.is_dir():
			continue
		json_path = folder / f"{folder.name}.json"
		if not json_path.exists():
			continue
		data = json.loads(json_path.read_text(encoding="utf-8"))
		doctype = data.get("name") or folder.name.replace("_", " ").title()
		changed = False
		for field in data.get("fields", []):
			fname = field.get("fieldname")
			if not fname or field.get("fieldtype") != "Float":
				continue
			if fname in KEEP_FLOAT:
				continue
			if fname not in CURRENCY_FIELDNAMES:
				continue
			field["fieldtype"] = "Currency"
			changed = True
		if changed:
			json_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
			changed_doctypes.append(doctype)
	for name in changed_doctypes:
		print("updated", name)


if __name__ == "__main__":
	apply()


def execute() -> None:
	apply()
