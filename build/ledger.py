"""Observed prices, kept apart from the authored dataset.

`rows.py` is the hand-written record: the source, the configuration and the
price a person checked. This ledger is the market record: the last price a
browser read and the day it read it. The build applies a ledger entry over the
authored value only while the entry's `base` still equals that value, so a
hand edit invalidates the override instead of being quietly outvoted by an old
observation.

The file is written by `price_watch.py --apply`, not by hand. Its shape is:

    {
      "version": 1,
      "updated": "2026-11-16T18:00:00+00:00",
      "rows": {
        "epson-et-2951": {
          "price": {"base": 319.99, "price": 299.99, "checked": "2026-11-16",
                    "in_stock": false}
        },
        "oura-ring-4": {
          "offers": {
            "argos_oura4": {"base": 329.0, "checked": "2026-11-16"}
          }
        }
      }
    }

`price` is omitted when the observation matches the authored value; the check
date is still recorded. A row whose price is out of stock keeps its price and
sets `in_stock: false`, so the page can show `Check price`. A row with offers
has no row price, because its offers are the price.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping

LEDGER_PATH = Path(__file__).with_name("price_ledger.json")
VERSION = 1

DATE_TEXT = re.compile(
    r"\b\d{1,2} (?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December) \d{4}\b"
)
MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


@dataclass(frozen=True)
class PriceEntry:
    """One observed figure and the authored figure it replaces."""

    base: float
    price: float | None
    checked: str
    in_stock: bool | None = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"base": self.base, "checked": self.checked}
        if self.price is not None:
            out["price"] = self.price
        if self.in_stock is not None:
            out["in_stock"] = self.in_stock
        return out


@dataclass(frozen=True)
class RowEntry:
    """The observed price and any observed offers for one row."""

    price: PriceEntry | None = None
    offers: Mapping[str, PriceEntry] | None = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.price is not None:
            out["price"] = self.price.to_json()
        if self.offers:
            out["offers"] = {
                source: entry.to_json()
                for source, entry in sorted(self.offers.items())
            }
        return out


@dataclass(frozen=True)
class Ledger:
    """The whole observed record, plus the day any entry last moved."""

    rows: Mapping[str, RowEntry]
    updated: str

    def base_for(self, row_id: str, kind: str, source: str = "") -> float | None:
        entry = self.rows.get(row_id)
        if entry is None:
            return None
        if kind == "offer":
            offer = (entry.offers or {}).get(source)
            return offer.base if offer else None
        return entry.price.base if entry.price else None

    def stock_for(self, row_id: str, source: str) -> bool | None:
        """The last stock reading for one offer, or None when it was not read."""
        entry = self.rows.get(row_id)
        if entry is None:
            return None
        offer = (entry.offers or {}).get(source)
        return offer.in_stock if offer else None

    def price_stock_for(self, row_id: str) -> bool | None:
        """The last stock reading for a single-seller row's price."""
        entry = self.rows.get(row_id)
        return entry.price.in_stock if entry and entry.price else None

    def record(
        self, readings: Iterable["Reading"], checked: str
    ) -> tuple["Ledger", int]:
        """Apply confirmed readings, preserving entries no page was read for."""
        rows = {
            row_id: RowEntry(
                price=entry.price,
                offers=dict(entry.offers or {}) or None,
            )
            for row_id, entry in self.rows.items()
        }
        written = 0
        for reading in readings:
            entry = rows.get(reading.row_id, RowEntry())
            observed = None if abs(reading.price - reading.base) < 0.005 else reading.price
            offers = dict(entry.offers or {}) if reading.kind == "offer" else None
            before = offers.get(reading.source) if offers is not None else entry.price
            stock = reading.in_stock
            if stock is None and before is not None:
                stock = before.in_stock
            price = PriceEntry(
                base=reading.base,
                price=observed,
                checked=checked,
                in_stock=stock,
            )
            if offers is not None:
                offers[reading.source] = price
                rows[reading.row_id] = RowEntry(
                    price=entry.price, offers=offers or None
                )
            else:
                rows[reading.row_id] = RowEntry(price=price, offers=entry.offers)
            if before != price:
                written += 1
        return Ledger(rows=rows, updated=self.updated), written


@dataclass(frozen=True)
class Reading:
    """One page read that is safe to write."""

    row_id: str
    kind: str
    source: str
    base: float
    price: float
    in_stock: bool | None = None


def day_text(value: str) -> str:
    day = date.fromisoformat(value)
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def note_with_date(note: str, checked: str) -> str:
    """Keep the note's own words and move its check date to `checked`."""
    label = day_text(checked)
    cleaned = note.strip()
    if DATE_TEXT.search(cleaned):
        return DATE_TEXT.sub(label, cleaned, count=1)
    if not cleaned:
        return f"checked {label}"
    return f"{cleaned.rstrip(' .')}, checked {label}"


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if not isinstance(value, (int, float)):
        return None
    number = round(float(value), 2)
    return number if number > 0 else None


def _entry(raw: object, where: str) -> tuple[PriceEntry | None, list[str]]:
    if not isinstance(raw, Mapping):
        return None, [f"{where} is not an object"]
    base = _number(raw.get("base"))
    if base is None:
        return None, [f"{where} has no positive base"]
    checked = raw.get("checked")
    if not isinstance(checked, str):
        return None, [f"{where} has no check date"]
    try:
        day = date.fromisoformat(checked)
    except ValueError:
        return None, [f"{where} check date {checked!r} is not an ISO date"]
    if day > date.today():
        return None, [f"{where} check date {checked} is in the future"]
    price = raw.get("price")
    observed = None if price is None else _number(price)
    if price is not None and observed is None:
        return None, [f"{where} price {price!r} is not positive"]
    in_stock = raw.get("in_stock")
    if in_stock is not None and not isinstance(in_stock, bool):
        return None, [f"{where} in_stock {in_stock!r} is not true or false"]
    return PriceEntry(
        base=base, price=observed, checked=checked, in_stock=in_stock
    ), []


def load(path: Path = LEDGER_PATH) -> tuple[Ledger, list[str]]:
    """Read the ledger once, naming every malformed entry."""
    if not path.exists():
        return Ledger(rows={}, updated=""), []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return Ledger(rows={}, updated=""), [f"price ledger: {error}"]
    if not isinstance(raw, Mapping):
        return Ledger(rows={}, updated=""), ["price ledger: the root is not an object"]
    if raw.get("version") != VERSION:
        return Ledger(rows={}, updated=""), [
            f"price ledger: version {raw.get('version')!r} is not {VERSION}"
        ]
    rows_raw = raw.get("rows")
    if not isinstance(rows_raw, Mapping):
        return Ledger(rows={}, updated=""), ["price ledger: rows is not an object"]
    rows: dict[str, RowEntry] = {}
    problems: list[str] = []
    for row_id, value in rows_raw.items():
        if not isinstance(row_id, str) or not row_id:
            problems.append("price ledger: a row id is not a string")
            continue
        if not isinstance(value, Mapping):
            problems.append(f"price ledger: {row_id} is not an object")
            continue
        price = None
        if "price" in value:
            price, price_problems = _entry(value.get("price"), f"{row_id} price")
            problems.extend(price_problems)
        offers: dict[str, PriceEntry] = {}
        offers_raw = value.get("offers")
        if offers_raw is not None:
            if not isinstance(offers_raw, Mapping):
                problems.append(f"price ledger: {row_id} offers is not an object")
            else:
                for source, offer in offers_raw.items():
                    if not isinstance(source, str) or not source:
                        problems.append(f"price ledger: {row_id} has no offer source")
                        continue
                    parsed, offer_problems = _entry(
                        offer, f"{row_id} offer {source}"
                    )
                    problems.extend(offer_problems)
                    if parsed is not None:
                        offers[source] = parsed
        if price is not None and offers:
            problems.append(
                f"price ledger: {row_id} has both a price and offers; offers are the price"
            )
        if price is not None or offers:
            rows[row_id] = RowEntry(price=price, offers=offers or None)
    updated = raw.get("updated")
    return Ledger(
        rows=rows,
        updated=updated if isinstance(updated, str) else "",
    ), problems


def apply_to_rows(
    ledger: Ledger,
    raw_rows: Iterable[dict[str, Any]],
    sources: Mapping[str, object],
) -> list[str]:
    """Put observed values over the authored rows, naming a stale base."""
    by_id = {str(row["id"]): row for row in raw_rows}
    problems: list[str] = []
    for row_id, entry in ledger.rows.items():
        row = by_id.get(row_id)
        if row is None:
            problems.append(f"price ledger: {row_id} is not a row")
            continue
        offers = row.get("offers") or ()
        if offers:
            if entry.price is not None:
                problems.append(
                    f"price ledger: {row_id} has a price, but its offers are the price"
                )
            by_source = {str(offer["src"]): offer for offer in offers}
            for source, observed in (entry.offers or {}).items():
                offer = by_source.get(source)
                if offer is None:
                    problems.append(
                        f"price ledger: {row_id} has no offer from {source}"
                    )
                    continue
                if source not in sources:
                    problems.append(
                        f"price ledger: {row_id} offer {source} is not in the source register"
                    )
                    continue
                if abs(float(offer["price"]) - observed.base) >= 0.005:
                    problems.append(
                        f"price ledger: {row_id} offer {source} base is "
                        f"{observed.base:.2f}, but the authored price is "
                        f"{float(offer['price']):.2f}; remove or re-observe the entry"
                    )
                    continue
                if observed.price is not None:
                    offer["price"] = observed.price
                if observed.in_stock is not None:
                    offer["in_stock"] = observed.in_stock
                offer["checked_iso"] = observed.checked
            continue
        if entry.offers:
            problems.append(f"price ledger: {row_id} has offers, but the row does not")
            continue
        if entry.price is None:
            continue
        if str(row["price_src"]) not in sources:
            problems.append(
                f"price ledger: {row_id} price source {row['price_src']} is not registered"
            )
            continue
        if abs(float(row["price"]) - entry.price.base) >= 0.005:
            problems.append(
                f"price ledger: {row_id} base is {entry.price.base:.2f}, but the "
                f"authored price is {float(row['price']):.2f}; remove or re-observe the entry"
            )
            continue
        if entry.price.price is not None:
            row["price"] = entry.price.price
        if entry.price.in_stock is False:
            row["price_check"] = True
        row["checked_iso"] = entry.price.checked
        row["price_note"] = note_with_date(
            str(row["price_note"]), entry.price.checked
        )
    return problems


def write(ledger: Ledger, path: Path = LEDGER_PATH, updated: str = "") -> None:
    """Replace the ledger atomically, so a crash cannot leave half a file."""
    data = {
        "version": VERSION,
        "updated": updated or ledger.updated,
        "rows": {
            row_id: entry.to_json()
            for row_id, entry in sorted(ledger.rows.items())
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)
