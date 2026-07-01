# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

from dataclasses import dataclass


def _norm_link(value: str | None) -> str:
        """Normalize optional Link fields for stable Stock In Hand identity."""
        return (value or "").strip()


def _norm_bags_are(value: str | None, *, is_bardana: bool = False) -> str:
        """
        Normalize Bags Are for stock balance identity.

        Grain/non-bardana stock must consistently use Our because Stock In Hand
        metadata defaults bags_are to Our. Without this, callers passing None
        can miss rows saved with the DocType default.
        """
        value = (value or "").strip()
        if not value:
                return "Our"
        return value


@dataclass(frozen=True)
class StockKey:
        storeid: str
        itemcode: str
        bagitemcode: str | None = None
        partyid: str | None = None
        bags_are: str | None = None

        def normalized_parts(self) -> tuple[str, str, str, str, str]:
                is_bardana = bool(_norm_link(self.bagitemcode))
                return (
                        _norm_link(self.storeid),
                        _norm_link(self.itemcode),
                        _norm_link(self.bagitemcode),
                        _norm_link(self.partyid),
                        _norm_bags_are(self.bags_are, is_bardana=is_bardana),
                )

        def stock_key(self) -> str:
                return make_stock_key(self)


def make_stock_key(key: StockKey) -> str:
        return "|".join(key.normalized_parts())


def make_stock_key_from_values(
        *,
        storeid: str | None,
        itemcode: str | None,
        bagitemcode: str | None = None,
        partyid: str | None = None,
        bags_are: str | None = None,
) -> str:
        return StockKey(
                storeid=storeid or "",
                itemcode=itemcode or "",
                bagitemcode=bagitemcode,
                partyid=partyid,
                bags_are=bags_are,
        ).stock_key()


def normalized_bags_are_for_stock_key(key: StockKey) -> str:
        return key.normalized_parts()[4]
