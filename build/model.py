"""The data's shape after authoring: frozen records, parsed once.

`rows.py` still authors each product as a dict, because a 900-line literal is
easier to read beside its source comment than a constructor per line. That is
the boundary: `Row.from_raw()` parses every dict once, after the derived figures
are computed, and every page, CSV and check reads `Row` from then on. A frozen
record cannot have a field added by a check, and a misspelt attribute fails
instead of quietly reading `None`.

A row's figures live in one frozen `Figures`, so "which numbers are authored and
which are sums" is visible in the type rather than in a convention. A lineup
entry is either a current row or an absent one, so the pair-and-a-flag shape of
the old maps cannot be confused with a row id.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Mapping, NamedTuple, cast


class Source(NamedTuple):
    name: str
    url: str


@dataclass(frozen=True)
class Offer:
    shop: str
    src: str
    price: float
    pay: int
    note: str = ""

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


@dataclass(frozen=True)
class Figures:
    """The numbers the page shows that are not authored input."""

    score_total: int
    nosub3: float
    sub3: float | None
    keep3: float | None
    maths_free: str
    maths_sub: str
    keep_basis: str
    keep_note: str
    offer_at: str = ""


FIGURE_KEYS = frozenset(Figures.__dataclass_fields__)

# The keys the build and the checks may index. A misspelt literal is now a mypy
# error, which is the check that a plain dict could never give them.
RowKey = Literal[
    "cat", "id", "brand", "model", "rec", "power", "ha",
    "price", "price_note", "price_src", "extra", "extra_note",
    "free_records", "sub", "sub_name", "best", "catch", "storage",
    "live", "alerts", "ai", "history", "paywalled", "sub_text", "ha_text",
    "wifi", "score", "src", "unverified", "rec_src", "history_src",
    "ha_src", "plan_src", "power_note", "cards", "plan_region",
    "extra_src", "kit_src", "kit_label", "kit_price", "nosub_say",
    "plan_say", "buy", "buy_label", "price_check", "offers", "verdict",
    "plain", "figures", "offer_conflict", "score_total", "nosub3", "sub3",
    "keep3", "maths_free", "maths_sub", "keep_basis", "keep_note", "offer_at",
]


@dataclass(frozen=True)
class Row:
    cat: str
    id: str
    brand: str
    model: str
    rec: str
    power: tuple[str, ...]
    ha: int
    price: float
    price_note: str
    price_src: str
    extra: float
    extra_note: str
    free_records: bool
    sub: float | None
    sub_name: str
    best: str
    catch: str
    storage: str
    live: str
    alerts: str
    ai: str
    history: str
    paywalled: str
    sub_text: str
    ha_text: str
    wifi: str
    score: Mapping[str, int]
    src: tuple[str, ...]
    unverified: str
    rec_src: str
    history_src: str
    ha_src: str
    plan_src: str
    power_note: str
    cards: int
    plan_region: str
    extra_src: str | None
    kit_src: str | None
    kit_label: str | None
    kit_price: float | None
    nosub_say: str | None
    plan_say: str | None
    buy: str | None
    buy_label: str
    price_check: bool
    offers: tuple[Offer, ...]
    verdict: str | None
    plain: tuple[str, str] | None
    figures: Figures
    offer_conflict: bool = False

    def __getitem__(self, key: RowKey) -> Any:
        if key in FIGURE_KEYS:
            return getattr(self.figures, key)
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key) from None

    def get(self, key: RowKey, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        try:
            self[cast(RowKey, key)]
        except KeyError:
            return False
        return True

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "Row":
        offers = tuple(
            Offer(
                shop=str(offer["shop"]),
                src=str(offer["src"]),
                price=float(offer["price"]),
                pay=int(offer["pay"]),
                note=str(offer.get("note", "")),
            )
            for offer in raw.get("offers") or ()
        )
        return cls(
            cat=str(raw["cat"]),
            id=str(raw["id"]),
            brand=str(raw["brand"]),
            model=str(raw["model"]),
            rec=str(raw["rec"]),
            power=tuple(raw.get("power") or ()),
            ha=int(raw["ha"]),
            price=float(raw["price"]),
            price_note=str(raw["price_note"]),
            price_src=str(raw["price_src"]),
            extra=float(raw["extra"]),
            extra_note=str(raw["extra_note"]),
            free_records=bool(raw["free_records"]),
            sub=None if raw["sub"] is None else float(raw["sub"]),
            sub_name=str(raw["sub_name"]),
            best=str(raw["best"]),
            catch=str(raw["catch"]),
            storage=str(raw["storage"]),
            live=str(raw["live"]),
            alerts=str(raw["alerts"]),
            ai=str(raw["ai"]),
            history=str(raw["history"]),
            paywalled=str(raw["paywalled"]),
            sub_text=str(raw["sub_text"]),
            ha_text=str(raw["ha_text"]),
            wifi=str(raw["wifi"]),
            score=MappingProxyType({str(k): int(v) for k, v in raw["score"].items()}),
            src=tuple(raw["src"]),
            unverified=str(raw["unverified"]),
            rec_src=str(raw["rec_src"]),
            history_src=str(raw["history_src"]),
            ha_src=str(raw["ha_src"]),
            plan_src=str(raw["plan_src"]),
            power_note=str(raw.get("power_note", "")),
            cards=int(raw.get("cards", 1)),
            plan_region=str(raw.get("plan_region", "UK")),
            extra_src=raw.get("extra_src"),
            kit_src=raw.get("kit_src"),
            kit_label=raw.get("kit_label"),
            kit_price=None if raw.get("kit_price") is None else float(raw["kit_price"]),
            nosub_say=raw.get("nosub_say"),
            plan_say=raw.get("plan_say"),
            buy=raw.get("buy"),
            buy_label=str(raw.get("buy_label", "Amazon")),
            price_check=bool(raw.get("price_check", False)),
            offers=offers,
            verdict=raw.get("verdict"),
            plain=raw.get("plain"),
            figures=Figures(
                score_total=int(raw["score_total"]),
                nosub3=float(raw["nosub3"]),
                sub3=None if raw["sub3"] is None else float(raw["sub3"]),
                keep3=None if raw["keep3"] is None else float(raw["keep3"]),
                maths_free=str(raw["maths_free"]),
                maths_sub=str(raw["maths_sub"]),
                keep_basis=str(raw["keep_basis"]),
                keep_note=str(raw["keep_note"]),
                offer_at=str(raw.get("offer_at", "")),
            ),
            offer_conflict=bool(raw.get("offer_conflict", False)),
        )


@dataclass(frozen=True)
class Current:
    row_id: str


@dataclass(frozen=True)
class Absent:
    model: str | None
    reason: str
    verified: bool = False


def parse_lineup(cat: Mapping[str, Any], rows_by_id: Mapping[str, Row]):
    """Turn the authored current/previous maps into records, by brand.

    A current entry is a row id or a pair that records the last model and why
    the brand has no current one. A previous entry is a row id or a pair whose
    optional `True` says a person verified the absence. A bare pair is a to-do,
    not a parse failure, so the five open brands stay visible in the check notes.
    """
    problems: list[str] = []
    current: dict[str, Current | Absent] = {}
    for brand, named in (cat.get("current") or {}).items():
        if isinstance(named, str):
            found = rows_by_id.get(named)
            if found is None:
                problems.append(f"{cat['slug']}: {brand}'s current model {named!r} is not a row")
            elif found.brand != brand:
                problems.append(
                    f"{cat['slug']}: {brand}'s current model {named!r} belongs to {found.brand}"
                )
            else:
                current[brand] = Current(named)
        elif isinstance(named, tuple) and len(named) == 2 and isinstance(named[0], str):
            model, reason = named
            if not model.strip():
                problems.append(f"{cat['slug']}: {brand}'s current absence names no last model")
            elif not str(reason or "").strip():
                problems.append(f"{cat['slug']}: {brand} has no current model and no reason")
            else:
                current[brand] = Absent(model, str(reason), True)
        else:
            problems.append(
                f"{cat['slug']}: {brand}'s current entry must be a row id or (last model, reason)"
            )

    previous: dict[str, Current | Absent] = {}
    for brand, named in (cat.get("previous") or {}).items():
        if isinstance(named, str):
            found = rows_by_id.get(named)
            if found is None:
                problems.append(
                    f"{cat['slug']}: {brand}'s last-generation model {named!r} is not a row"
                )
            elif found.brand != brand:
                problems.append(
                    f"{cat['slug']}: {brand}'s last-generation model {named!r} belongs "
                    f"to {found.brand}"
                )
            elif current.get(brand) == Current(named):
                problems.append(
                    f"{cat['slug']}: {brand}'s last-generation model {named!r} is also "
                    "its current one"
                )
            else:
                previous[brand] = Current(named)
        elif isinstance(named, tuple):
            if len(named) not in (2, 3) or named[0] is not None:
                problems.append(
                    f"{cat['slug']}: {brand}'s pair must be (None, reason) or "
                    "(None, reason, True)"
                )
                continue
            if len(named) == 3 and named[2] is not True:
                problems.append(
                    f"{cat['slug']}: {brand}'s verified pair must end in True"
                )
                continue
            reason = str(named[1] or "").strip()
            if not reason:
                problems.append(
                    f"{cat['slug']}: {brand} has no last-generation row and no reason"
                )
                continue
            previous[brand] = Absent(None, reason, len(named) == 3)
        else:
            problems.append(
                f"{cat['slug']}: {brand}'s previous entry must be a row id or "
                "(None, reason[, True])"
            )
    return {"current": current, "previous": previous}, problems
