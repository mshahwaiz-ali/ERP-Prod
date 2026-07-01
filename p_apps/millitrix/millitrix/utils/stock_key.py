# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockKey:
	storeid: str
	itemcode: str
	bagitemcode: str | None = None
	partyid: str | None = None
	bags_are: str | None = None
