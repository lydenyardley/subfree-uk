#!/usr/bin/env python3
"""Read the price behind every recorded row and offer, without changing data.

The weekly workflow runs this on Monday. It opens each source in Chromium,
reads the product's JSON-LD offer first, then falls back to the source's CSS
selectors. On local runs, pages Chromium cannot read are retried in Firefox,
because some retailers block Chromium's browser fingerprint. The weekly
workflow opts out of that retry because the runner's network is blocked before
the browser matters. Google's consent interstitial is rejected before the
product is read. A changed price, a bot wall, a dead page and a page whose
price cannot be identified are all reported; none is written back to `rows.py`.

The comparison is against the recorded figure, not against a scraped figure
from last week. That keeps the report meaningful after a human edits the data:
the next run compares the live page with what the page now publishes.

    python build/price_watch.py
    python build/price_watch.py --category printers
    python build/price_watch.py --source epson_et2951
    python build/price_watch.py --concurrency 2
    xvfb-run -a python build/price_watch.py --headed

Exit status is 0 when a report was produced, even when prices changed or pages
were unreadable. A browser that cannot start, or a crash while assembling the
report, exits non-zero.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from catalog import CATEGORIES

import rows


READ = "read"
BLOCKED = "blocked"
DEAD = "dead"
ERROR = "error"
UNREADABLE = "unreadable"
AMBIGUOUS = "ambiguous"
FALLBACK_STATUSES = {BLOCKED, UNREADABLE, AMBIGUOUS, ERROR}

# The pages that list more than one product. A JSON-LD product must be matched
# by name there; a single CSS price on the page could belong to a neighbour. A
# product page with one recorded row is safe to read with CSS when it has no
# JSON-LD.
LISTING_SOURCES = {
    "reo_gb_home",
    "reo_store",
}

# Product cards on pages whose offers are not in JSON-LD. The card text holds
# the product name and the current and crossed-out prices in that order.
LISTING_CSS: dict[str, tuple[str, ...]] = {
    "reo_gb_home": (".product-card",),
    "reo_store": ("[class*='product-details']",),
}

# Product names used only where one page holds several products. A single
# product page needs no name match. These are the shortest strings that pick the
# right product out of the page's JSON-LD.
ROW_MATCH: dict[str, dict[str, str]] = {
    "reo_gb_home": {
        "reo-rlc820a": "RLC-820A",
        "reo-e1out": "E1 Outdoor Pro",
        "reo-arguspt": "Argus PT Ultra 4K Color Night Vision",
    },
    "reo_store": {
        "reo-wifi": "Reolink Video Doorbell WiFi",
        "reo-poe": "Reolink Video Doorbell PoE",
    },
    "weenect_xt": {"weenect-xt": "GPS dog tracker"},
}

# CSS is the fallback for pages without a usable Product offer. Host defaults
# cover the shop platforms. The last three selectors are generic metadata that
# many shops emit even when they publish no JSON-LD.
DEFAULT_CSS: tuple[str, ...] = (
    'meta[property="product:price:amount"]',
    "[itemprop='price']",
    "[data-price]",
    ".price",
)

CSS_BY_HOST: dict[str, tuple[str, ...]] = {
    "en-uk.ring.com": (".product__price", ".price", "[data-product-price]"),
    "store.google.com": ("[data-test='price']", "[data-testid='price']", ".price"),
    "www.eufy.com": ("[data-product-price]", ".price"),
    "www.anker.com": ("[data-product-price]", ".price"),
    "store.reolink.com": (".product-price", ".price"),
    "reolink.com": (".product-price", ".price"),
    "uk.store.tapo.com": (".product__price", ".price"),
    "www.arlo.com": (".product-price", ".price"),
    "www.easygates.co.uk": (".product-price", ".price"),
    "www.aqara-shop.co.uk": (".product-price", ".price"),
    "www.amazon.co.uk": (
        "#corePrice_feature_div .a-price .a-offscreen",
        ".a-price .a-offscreen",
    ),
    "www.chesterdigitalsupplies.co.uk": (".product-price", ".price"),
    "www.ertech.co.uk": (".product-price", ".price"),
    "eaglesecuritysolutions.co.uk": (".product-price", ".price"),
    "www.argos.co.uk": ("[data-testid='product-price']", ".product-price"),
    "www.ultrahuman.com": (".product-price", ".price"),
    "www.currys.co.uk": ("[data-testid='product-price']", ".product-price"),
    "uk.amazfit.com": (".product__price", ".price"),
    "www.epson.co.uk": (".product-price", ".price"),
    "www.canon.co.uk": (".product-price", ".price"),
    "store.brother.co.uk": (".product-price", ".price"),
    "www.ryman.co.uk": ("[itemprop='price']", ".price"),
    "www.hp.com": ("[data-testid='product-price']", ".price"),
    "www.pitpat.com": ("ins .woocommerce-Price-amount", ".shop-product-price"),
    "www.pawva.co.uk": (".product-price", ".price"),
    "tractive.com": (".product-price", ".price"),
    "www.weenect.com": (".product-price", ".price"),
    "www.pawfit.com": (".product-price", ".price"),
    "www.apple.com": ("[data-automation='price']", ".rf-buy__price"),
    "www.mamasandpapas.com": (".product-price", ".price"),
    "www.philips.co.uk": (".product-price", ".price"),
    "nanituk.co.uk": (".product__price", ".price"),
    "owletbabycare.co.uk": (".product__price", ".price"),
}

MONEY = re.compile(
    r"(?<![\d.])(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)(?![\d.])"
)
CARD_PRICE = re.compile(
    r"£\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)"
)
CURRENCY = {
    "£": "GBP",
    "GBP": "GBP",
    "€": "EUR",
    "EUR": "EUR",
    "$": "USD",
    "USD": "USD",
}
SOFT_ERROR = re.compile(
    r"page not found|something went wrong|access denied|just a moment|captcha|"
    r"enter the characters you see below|not a robot|verify you are human|"
    r"unusual traffic|automated access",
    re.IGNORECASE,
)
PRODUCT_TYPES = {
    "Product",
    "ProductGroup",
    "IndividualProduct",
    "ProductModel",
}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class Adapter:
    """How one source is read after JSON-LD has been tried."""

    match: str = ""
    css: tuple[str, ...] = DEFAULT_CSS


@dataclass(frozen=True)
class Want:
    """One recorded figure that a source page should still publish."""

    row_id: str
    category: str
    brand: str
    model: str
    kind: str
    expected: float
    source: str
    source_name: str
    url: str
    shop: str = ""

    @property
    def label(self) -> str:
        if self.kind == "offer":
            return f"{self.brand} {self.model} ({self.shop} offer)"
        return f"{self.brand} {self.model}"


@dataclass(frozen=True)
class Product:
    name: str
    price: float
    currency: str
    availability: str = ""


@dataclass(frozen=True)
class Observation:
    want: Want
    status: str
    observed: float | None = None
    method: str = ""
    detail: str = ""

    @property
    def changed(self) -> bool:
        return (
            self.status == READ
            and self.observed is not None
            and abs(self.observed - self.want.expected) >= 0.005
        )


def money(value: float) -> str:
    return f"£{value:,.2f}"


def plural(count: int, one: str, many: str | None = None) -> str:
    return f"{count} {one if count == 1 else (many or one + 's')}"


def difference(value: float) -> str:
    sign = "+" if value > 0 else "-"
    return f"{sign}£{abs(value):,.2f}"


def parse_money(value: object) -> tuple[float, str] | None:
    """A number and its currency from a JSON-LD value or visible price text."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = round(float(value), 2)
        return (number, "") if number > 0 else None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    found = MONEY.search(text.replace("\xa0", " "))
    if not found:
        return None
    try:
        number = round(float(found.group(1).replace(",", "")), 2)
    except ValueError:
        return None
    if number <= 0:
        return None
    currency = ""
    upper = text.upper()
    for marker, code in CURRENCY.items():
        if marker in upper:
            currency = code
            break
    return number, currency


def first_price(values: Iterable[str]) -> tuple[float, str] | None:
    """The first visible value that carries a number, in page order."""
    for value in values:
        parsed = parse_money(value)
        if parsed is not None:
            return parsed
    return None


def normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def type_names(node: Mapping[str, Any]) -> set[str]:
    raw = node.get("@type")
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {str(item) for item in raw}
    return set()


def offer_from(raw: Mapping[str, Any]) -> Product | None:
    """One Product-shaped value from an Offer or AggregateOffer node."""
    price = None
    for key in ("price", "lowPrice", "highPrice"):
        if raw.get(key) is not None:
            price = parse_money(raw.get(key))
            if price:
                break
    if price is None and raw.get("priceSpecification") is not None:
        specs = raw["priceSpecification"]
        for spec in specs if isinstance(specs, list) else [specs]:
            if isinstance(spec, Mapping):
                price = parse_money(spec.get("price"))
                if price:
                    break
    if price is None:
        return None
    number, currency = price
    return Product(
        name="",
        price=number,
        currency=currency or str(raw.get("priceCurrency") or "").upper(),
        availability=str(raw.get("availability") or ""),
    )


def products_from_jsonld(raw_blobs: Iterable[str]) -> list[Product]:
    """Every Product offer in the page's JSON-LD, with its product name."""
    out: list[Product] = []
    seen: set[tuple[str, float, str]] = set()

    def walk(node: object, inherited_name: str = "") -> None:
        if isinstance(node, list):
            for item in node:
                walk(item, inherited_name)
            return
        if not isinstance(node, Mapping):
            return

        name = str(node.get("name") or node.get("headline") or inherited_name)
        types = type_names(node)
        if types & PRODUCT_TYPES or (name and node.get("offers") is not None):
            offers = node.get("offers")
            offer_nodes = offers if isinstance(offers, list) else [offers]
            for offer in offer_nodes:
                if not isinstance(offer, Mapping):
                    continue
                parsed = offer_from(offer)
                if parsed is None:
                    continue
                product = Product(
                    name=name,
                    price=parsed.price,
                    currency=parsed.currency,
                    availability=parsed.availability,
                )
                signature = (normalise(product.name), product.price, product.currency)
                if signature not in seen:
                    seen.add(signature)
                    out.append(product)
        for key, value in node.items():
            if key in {"offers", "priceSpecification"}:
                continue
            if key in {"@graph", "mainEntity", "itemListElement", "item", "hasVariant"}:
                walk(value, name)

    for blob in raw_blobs:
        try:
            walk(json.loads(blob))
        except (TypeError, ValueError):
            continue
    return out


def choose_product(
    products: Sequence[Product],
    want: Want,
    adapter: Adapter,
    allow_single: bool,
) -> tuple[Product | None, str]:
    if not products:
        return None, "no Product offer in JSON-LD"
    if len(products) == 1 and allow_single:
        return products[0], ""
    match = adapter.match or want.model
    terms = [normalise(part) for part in match.split("|") if part.strip()]
    hits = [
        product
        for product in products
        if any(term and term in normalise(product.name) for term in terms)
    ]
    if len(hits) == 1:
        return hits[0], ""
    if len(hits) > 1:
        return None, f"{len(hits)} products match {match!r}"
    return None, f"no product matches {match!r}"


def adapter_for(want: Want) -> Adapter:
    host = urlparse(want.url).netloc.lower()
    return Adapter(
        match=ROW_MATCH.get(want.source, {}).get(want.row_id, ""),
        css=CSS_BY_HOST.get(host, DEFAULT_CSS),
    )


def wants() -> list[Want]:
    """Every recorded price and offer, deduplicated by row and expected figure."""
    out: list[Want] = []
    seen: set[tuple[str, str, str, float]] = set()
    categories = {cat["slug"]: cat for cat in CATEGORIES}
    for row in rows.ROWS:
        category = str(row["cat"])
        cat = categories.get(category)
        if cat is None:
            continue
        source = str(row["price_src"])
        name, url = rows.S[source]
        signature = (str(row["id"]), source, "price", float(row["price"]))
        if signature not in seen:
            seen.add(signature)
            out.append(
                Want(
                    row_id=str(row["id"]),
                    category=category,
                    brand=str(row["brand"]),
                    model=str(row["model"]),
                    kind="price",
                    expected=float(row["price"]),
                    source=source,
                    source_name=str(name),
                    url=str(url),
                )
            )
        for offer in row.get("offers") or ():
            offer_source = str(offer["src"])
            offer_name, offer_url = rows.S[offer_source]
            signature = (
                str(row["id"]),
                offer_source,
                "offer",
                float(offer["price"]),
            )
            if signature in seen:
                continue
            seen.add(signature)
            out.append(
                Want(
                    row_id=str(row["id"]),
                    category=category,
                    brand=str(row["brand"]),
                    model=str(row["model"]),
                    kind="offer",
                    expected=float(offer["price"]),
                    source=offer_source,
                    source_name=str(offer_name),
                    url=str(offer_url),
                    shop=str(offer["shop"]),
                )
            )
    return out


async def read_jsonld(page: Any) -> list[Product]:
    blobs = await page.locator('script[type="application/ld+json"]').all_text_contents()
    return products_from_jsonld(blobs)


async def read_css(page: Any, selectors: Sequence[str]) -> list[str]:
    return await page.evaluate(
        """(selectors) => {
            const values = [];
            for (const selector of selectors) {
                for (const element of document.querySelectorAll(selector)) {
                    const text = (element.textContent || "").trim();
                    const content = element.getAttribute("content") || "";
                    const value = text || content;
                    if (value) values.push(value);
                }
            }
            return values;
        }""",
        list(selectors),
    )


async def read_listing_cards(page: Any, selectors: Sequence[str]) -> list[str]:
    """The visible text of each product card, for listing pages without JSON-LD."""
    return await page.evaluate(
        """(selectors) => {
            const values = [];
            const seen = new Set();
            for (const selector of selectors) {
                for (const element of document.querySelectorAll(selector)) {
                    const value = (element.innerText || element.textContent || "").trim();
                    if (value && !seen.has(value)) {
                        seen.add(value);
                        values.push(value);
                    }
                }
            }
            return values;
        }""",
        list(selectors),
    )


def card_price(value: str) -> float | None:
    """The first sterling price on one product card."""
    found = CARD_PRICE.search(value.replace("\xa0", " "))
    if found is None:
        return None
    try:
        return round(float(found.group(1).replace(",", "")), 2)
    except ValueError:
        return None


def card_matches(want: Want, adapter: Adapter, card: str) -> bool:
    """Whether a listing card names the recorded product."""
    match = adapter.match or want.model
    terms = [normalise(part) for part in match.split("|") if part.strip()]
    haystack = normalise(card)
    return any(term and term in haystack for term in terms)


async def dismiss_google_consent(
    page: Any, url: str, timeout_ms: int
) -> Any | None:
    """Reject Google's consent page and reload the product behind it."""
    if "consent.google.com" not in page.url:
        return None
    button = page.get_by_role("button", name="Reject all")
    if not await button.count():
        return None
    await button.first.click(timeout=timeout_ms)
    await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    return await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)


async def probe_site(
    browser: Any,
    source: str,
    site_wants: Sequence[Want],
    semaphore: asyncio.Semaphore,
    timeout_ms: int,
) -> list[Observation]:
    """Read one page once and turn every wanted product on it into a result."""
    async with semaphore:
        context = None
        try:
            options: dict[str, Any] = {
                "locale": "en-GB",
                "timezone_id": "Europe/London",
                "viewport": {"width": 1366, "height": 900},
                "extra_http_headers": {"Accept-Language": "en-GB,en;q=0.9"},
            }
            if getattr(browser.browser_type, "name", "") != "firefox":
                options["user_agent"] = USER_AGENT
            context = await browser.new_context(**options)
            page = await context.new_page()

            async def block_assets(route: Any) -> None:
                if route.request.resource_type in {"image", "font", "media"}:
                    await route.abort()
                else:
                    await route.continue_()

            await page.route("**/*", block_assets)
            response = await page.goto(
                site_wants[0].url, wait_until="domcontentloaded", timeout=timeout_ms
            )
            response = (
                await dismiss_google_consent(page, site_wants[0].url, timeout_ms)
                or response
            )
            await page.wait_for_timeout(3000)
            status = response.status if response is not None else 0
            title = await page.title()
            body = await page.locator("body").inner_text(timeout=5000)
            text = f"{title}\n{body}"

            def failed(kind: str, detail: str) -> list[Observation]:
                return [
                    Observation(want=want, status=kind, detail=detail)
                    for want in site_wants
                ]

            if status in (401, 403, 407, 429):
                return failed(BLOCKED, f"HTTP {status}")
            if status in (404, 410):
                return failed(DEAD, f"HTTP {status}")
            if status >= 500:
                return failed(ERROR, f"HTTP {status}")
            if status and not 200 <= status < 300:
                return failed(ERROR, f"HTTP {status}")
            if SOFT_ERROR.search(text[:2000]):
                return failed(BLOCKED, "a bot wall or soft error is in the page text")

            products = await read_jsonld(page)
            listing_cards: list[str] = []
            if source in LISTING_SOURCES:
                listing_cards = await read_listing_cards(
                    page, LISTING_CSS.get(source, ())
                )
            observations: list[Observation] = []
            allow_single = (
                len(site_wants) == 1 and source not in LISTING_SOURCES
            )
            for want in site_wants:
                adapter = adapter_for(want)
                product, why = choose_product(products, want, adapter, allow_single)
                if product is not None:
                    if product.currency and product.currency != "GBP":
                        observations.append(
                            Observation(
                                want=want,
                                status=UNREADABLE,
                                detail=f"JSON-LD price is in {product.currency}",
                                method="JSON-LD",
                            )
                        )
                    else:
                        observations.append(
                            Observation(
                                want=want,
                                status=READ,
                                observed=product.price,
                                method="JSON-LD",
                                detail=product.availability,
                            )
                        )
                    continue

                if not allow_single:
                    hits = [
                        card
                        for card in listing_cards
                        if card_matches(want, adapter, card)
                    ]
                    if len(hits) == 1:
                        number = card_price(hits[0])
                        if number is not None:
                            observations.append(
                                Observation(
                                    want=want,
                                    status=READ,
                                    observed=number,
                                    method="listing card",
                                )
                            )
                            continue
                    if len(hits) > 1:
                        detail = f"{len(hits)} listing cards match {adapter.match!r}"
                        kind = AMBIGUOUS
                    elif hits:
                        detail = "listing card has no sterling price"
                        kind = UNREADABLE
                    elif listing_cards:
                        detail = "no matching listing card"
                        kind = UNREADABLE
                    else:
                        detail = why if products else "no JSON-LD; listing page needs a product match"
                        kind = AMBIGUOUS if products else UNREADABLE
                    observations.append(
                        Observation(want=want, status=kind, detail=detail)
                    )
                    continue

                values = await read_css(page, adapter.css)
                price = first_price(values)
                if price is None:
                    observations.append(
                        Observation(
                            want=want,
                            status=UNREADABLE,
                            detail=why if products else "no readable price in JSON-LD or CSS",
                        )
                    )
                    continue
                number, currency = price
                if currency and currency != "GBP":
                    observations.append(
                        Observation(
                            want=want,
                            status=UNREADABLE,
                            detail=f"CSS price is in {currency}",
                            method="CSS",
                        )
                    )
                    continue
                observations.append(
                    Observation(
                        want=want,
                        status=READ,
                        observed=number,
                        method="CSS",
                    )
                )
            return observations
        except Exception as error:  # a page's failure must not lose the other pages
            return [
                Observation(
                    want=want,
                    status=ERROR,
                    detail=f"{type(error).__name__}: {error}",
                )
                for want in site_wants
            ]
        finally:
            if context is not None:
                await context.close()


def needs_fallback(observations: Sequence[Observation]) -> bool:
    """Whether another browser might turn this page into a price."""
    return any(item.status in FALLBACK_STATUSES for item in observations)


def fallback_is_better(
    primary: Sequence[Observation], fallback: Sequence[Observation]
) -> bool:
    """Use the fallback only when it reads more of the same page."""
    primary_reads = sum(item.status == READ for item in primary)
    fallback_reads = sum(item.status == READ for item in fallback)
    return fallback_reads > primary_reads


def mark_fallback(items: Sequence[Observation]) -> list[Observation]:
    """Name the browser behind a read that only the fallback could get."""
    return [
        replace(item, method=f"{item.method} (Firefox)")
        if item.status == READ
        else item
        for item in items
    ]


def group_by_source(items: Sequence[Want]) -> list[tuple[str, list[Want]]]:
    grouped: dict[str, list[Want]] = {}
    for want in items:
        grouped.setdefault(want.source, []).append(want)
    return list(grouped.items())


def escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def report(observations: Sequence[Observation], checked_at: datetime) -> str:
    order = {cat["slug"]: index for index, cat in enumerate(CATEGORIES)}
    observations = sorted(
        observations,
        key=lambda item: (
            order.get(item.want.category, 99),
            item.want.brand,
            item.want.model,
            item.want.kind,
            item.want.shop,
        ),
    )
    changed = [item for item in observations if item.changed]
    unreadable = [item for item in observations if item.status != READ]
    read = [item for item in observations if item.status == READ]
    categories = {cat["slug"]: cat for cat in CATEGORIES}
    categories_checked = {item.want.category for item in observations}
    lines = [
        f"<!-- price-watch changed={len(changed)} unreadable={len(unreadable)} -->",
        "## Price watch",
        "",
        f"Checked {plural(len(observations), 'recorded price or offer', 'recorded prices and offers')} across "
        f"{plural(len(categories_checked), 'category', 'categories')} on "
        f"{checked_at.day} {checked_at:%B %Y} at {checked_at:%H:%M} UTC.",
        f"{len(read)} read, {len(changed)} changed, and "
        f"{len(unreadable)} could not be read. Prices were not edited.",
        "",
        "### Coverage",
        "",
        "| Category | Checks | Read | Changed | Unreadable |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for cat in CATEGORIES:
        slug = str(cat["slug"])
        subset = [item for item in observations if item.want.category == slug]
        if not subset:
            continue
        lines.append(
            f"| {escape(str(cat['nouns']).title())} | {len(subset)} | "
            f"{sum(item.status == READ for item in subset)} | "
            f"{sum(item.changed for item in subset)} | "
            f"{sum(item.status != READ for item in subset)} |"
        )
    lines += ["", "### Changed", ""]
    if changed:
        lines += [
            "| Category | Item | Recorded | Observed | Difference | Source | Read by |",
            "| --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
        for item in changed:
            category = categories.get(item.want.category)
            noun = str(category["nouns"]).title() if category else item.want.category
            assert item.observed is not None
            lines.append(
                f"| {escape(noun)} | {escape(item.want.label)} | "
                f"{money(item.want.expected)} | {money(item.observed)} | "
                f"{difference(item.observed - item.want.expected)} | "
                f"[{escape(item.want.source_name)}]({item.want.url}) | "
                f"{item.method} |"
            )
    else:
        lines.append("No recorded price changed.")
    lines += ["", "### Could not read", ""]
    if unreadable:
        lines += [
            "| Category | Item | Source | Status | Detail |",
            "| --- | --- | --- | --- | --- |",
        ]
        for item in unreadable:
            category = categories.get(item.want.category)
            noun = str(category["nouns"]).title() if category else item.want.category
            lines.append(
                f"| {escape(noun)} | {escape(item.want.label)} | "
                f"[{escape(item.want.source_name)}]({item.want.url}) | "
                f"{item.status} | "
                f"{escape(item.detail)} |"
            )
    else:
        lines.append("Every recorded price was readable.")
    lines += [
        "",
        "A changed price is a report, not an edit. Check the shop's page, stock "
        "and configuration before changing `rows.py`.",
    ]
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="only this source key; repeat for more than one",
    )
    parser.add_argument(
        "--category",
        action="append",
        default=[],
        help="only this category slug; repeat for more than one",
    )
    parser.add_argument("--concurrency", type=int, default=3, help="pages to read at once")
    parser.add_argument(
        "--headed",
        action="store_true",
        help="run the browsers with a window; under xvfb this passes some 403 bot walls",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=45_000,
        help="page timeout in milliseconds",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="skip the local Firefox retry for blocked pages",
    )
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print(
            "Playwright is not installed. Run: pip install -r build/requirements.txt",
            file=sys.stderr,
        )
        return 2

    selected = wants()
    if args.source:
        wanted = set(args.source)
        selected = [want for want in selected if want.source in wanted]
    if args.category:
        wanted_categories = set(args.category)
        selected = [want for want in selected if want.category in wanted_categories]
    if not selected:
        print("No recorded prices matched those filters.", file=sys.stderr)
        return 1

    groups = group_by_source(selected)
    semaphore = asyncio.Semaphore(max(1, min(args.concurrency, 8)))
    started = datetime.now(timezone.utc)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not args.headed)
        try:
            primary = await asyncio.gather(
                *(
                    probe_site(browser, source, site_wants, semaphore, args.timeout)
                    for source, site_wants in groups
                )
            )
        finally:
            await browser.close()

        by_source = {
            source: result for (source, _), result in zip(groups, primary)
        }
        retry: list[tuple[str, list[Want]]] = []
        if not args.no_fallback:
            retry = [
                (source, site_wants)
                for (source, site_wants), result in zip(groups, primary)
                if needs_fallback(result)
            ]
        if retry:
            browser = await playwright.firefox.launch(headless=not args.headed)
            try:
                fallback = await asyncio.gather(
                    *(
                        probe_site(browser, source, site_wants, semaphore, args.timeout)
                        for source, site_wants in retry
                    )
                )
            finally:
                await browser.close()
            for (source, _), result in zip(retry, fallback):
                if fallback_is_better(by_source[source], result):
                    by_source[source] = mark_fallback(result)

    observations = [item for group in by_source.values() for item in group]
    print(report(observations, started))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
