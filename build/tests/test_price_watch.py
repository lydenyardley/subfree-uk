"""Fixture tests for the price watch adapters and its report.

The browser fixtures exercise the same JSON-LD and CSS readers the scheduled
probe uses. They are local files, so the suite never requests a vendor page.
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from playwright.async_api import async_playwright

from catalog import CATEGORIES
from price_watch import (
    BLOCKED,
    READ,
    Adapter,
    Observation,
    Product,
    Want,
    adapter_for,
    card_matches,
    card_price,
    choose_product,
    fallback_is_better,
    first_price,
    mark_fallback,
    needs_fallback,
    parse_money,
    read_css,
    read_jsonld,
    read_listing_cards,
    report,
    wants,
)

FIXTURES = HERE / "fixtures"


def make_want(**overrides: Any) -> Want:
    values: dict[str, Any] = dict(
        row_id="epson-et-2951",
        category="printers",
        brand="Epson",
        model="EcoTank ET-2951",
        kind="price",
        expected=239.99,
        source="epson_et2951",
        source_name="Epson UK",
        url="https://www.epson.co.uk/et-2951",
        shop="",
    )
    values.update(overrides)
    return Want(**values)


class FixtureTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def asyncTearDown(self) -> None:
        await self.browser.close()
        await self.playwright.stop()

    async def open_fixture(self, name: str) -> Any:
        page = await self.browser.new_page()
        await page.goto((FIXTURES / name).as_uri())
        return page

    async def test_single_product_jsonld(self) -> None:
        page = await self.open_fixture("single.html")
        try:
            products = await read_jsonld(page)
        finally:
            await page.close()
        self.assertEqual(len(products), 1)
        product, why = choose_product(products, make_want(), Adapter(), True)
        self.assertEqual(why, "")
        assert product is not None
        self.assertEqual((product.name, product.price, product.currency), (
            "EcoTank ET-2951", 239.99, "GBP",
        ))
        self.assertIn("InStock", product.availability)

    async def test_jsonld_match_picks_the_recorded_product(self) -> None:
        page = await self.open_fixture("graph.html")
        try:
            products = await read_jsonld(page)
        finally:
            await page.close()
        self.assertEqual(len(products), 2)
        product, why = choose_product(
            products, make_want(), Adapter(match="ET-2951"), False
        )
        self.assertEqual(why, "")
        assert product is not None
        self.assertEqual(product.price, 239.99)

    async def test_css_is_the_fallback(self) -> None:
        page = await self.open_fixture("css.html")
        try:
            products = await read_jsonld(page)
            values = await read_css(page, (".product-price",))
        finally:
            await page.close()
        self.assertEqual(products, [])
        self.assertEqual(first_price(values), (189.99, "GBP"))

    async def test_no_numeric_price_is_unreadable(self) -> None:
        page = await self.open_fixture("unreadable.html")
        try:
            values = await read_css(page, (".product-price",))
        finally:
            await page.close()
        self.assertIsNone(first_price(values))

    async def test_aggregate_offer_reads_low_price(self) -> None:
        page = await self.open_fixture("aggregate.html")
        try:
            products = await read_jsonld(page)
        finally:
            await page.close()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].price, 399.00)
        self.assertEqual(products[0].currency, "GBP")

    def test_price_parser_handles_a_grouped_price(self) -> None:
        self.assertEqual(parse_money("£1,234.56"), (1234.56, "GBP"))
        self.assertEqual(parse_money("from 239.99"), (239.99, ""))
        self.assertIsNone(parse_money("Price on request"))

    def test_every_recorded_figure_has_an_adapter(self) -> None:
        for want in wants():
            adapter = adapter_for(want)
            self.assertTrue(adapter.css or adapter.match, want.source)

    def test_all_six_categories_are_covered(self) -> None:
        self.assertEqual(
            {want.category for want in wants()},
            {str(cat["slug"]) for cat in CATEGORIES},
        )

    def test_listing_rows_get_their_own_product_match(self) -> None:
        want = next(item for item in wants() if item.row_id == "reo-rlc820a")
        self.assertEqual(adapter_for(want).match, "RLC-820A")
        weenect = next(item for item in wants() if item.row_id == "weenect-xt")
        self.assertEqual(adapter_for(weenect).match, "GPS dog tracker")

    def test_amazon_uses_the_host_css_without_a_source_override(self) -> None:
        want = next(item for item in wants() if item.source == "amz_blink")
        self.assertEqual(
            adapter_for(want).css,
            ("#corePrice_feature_div .a-price .a-offscreen", ".a-price .a-offscreen"),
        )

    async def test_listing_cards_read_the_named_product(self) -> None:
        page = await self.open_fixture("listing.html")
        try:
            cards = await read_listing_cards(page, (".product-card",))
        finally:
            await page.close()
        self.assertEqual(len(cards), 3)
        rlc = make_want(
            row_id="reo-rlc820a", source="reo_gb_home", model="RLC-820A"
        )
        self.assertEqual(
            [
                card
                for card in cards
                if card_matches(rlc, Adapter(match="RLC-820A"), card)
            ],
            [cards[0]],
        )
        self.assertEqual(card_price(cards[0]), 63.99)
        wifi = make_want(
            row_id="reo-wifi", source="reo_store", model="Video Doorbell WiFi"
        )
        self.assertEqual(
            [
                card
                for card in cards
                if card_matches(
                    wifi, Adapter(match="Reolink Video Doorbell WiFi"), card
                )
            ],
            [cards[1]],
        )
        self.assertEqual(card_price(cards[1]), 82.49)

    def test_a_blocked_page_retries_in_the_fallback_browser(self) -> None:
        blocked = Observation(want=make_want(), status=BLOCKED, detail="HTTP 403")
        read = Observation(
            want=make_want(), status=READ, observed=239.99, method="JSON-LD"
        )
        self.assertTrue(needs_fallback([blocked]))
        self.assertFalse(needs_fallback([read]))
        self.assertTrue(fallback_is_better([blocked], [read]))
        self.assertFalse(fallback_is_better([read], [read]))
        self.assertEqual(mark_fallback([read])[0].method, "JSON-LD (Firefox)")
        self.assertEqual(mark_fallback([blocked])[0].method, "")

    def test_listing_card_needs_the_exact_model(self) -> None:
        hp = make_want(
            row_id="hp-envy-6520e", source="hp_envy6520e", model="Envy 6520e"
        )
        self.assertFalse(
            card_matches(
                hp,
                Adapter(match="6520e"),
                "HP Envy 6520 All-in-One Wireless Colour Printer £115.00",
            )
        )

    def test_a_listing_product_still_needs_its_name(self) -> None:
        product, why = choose_product(
            [Product("Envy 6530e", 89.99, "GBP")],
            make_want(source="hp_envy6520e", model="Envy 6520e"),
            Adapter(match="6520e"),
            False,
        )
        self.assertIsNone(product)
        self.assertIn("no product matches", why)

    def test_report_names_a_change_and_an_unreadable_page(self) -> None:
        changed = Observation(
            want=make_want(),
            status=READ,
            observed=249.99,
            method="JSON-LD",
        )
        blocked = Observation(
            want=make_want(row_id="canon-pixma-g3590", model="PIXMA G3590"),
            status=BLOCKED,
            detail="HTTP 403",
        )
        text = report(
            [changed, blocked], datetime(2026, 11, 16, 8, 30, tzinfo=timezone.utc)
        )
        self.assertIn("<!-- price-watch changed=1 unreadable=1 -->", text)
        self.assertIn("1 read, 1 changed", text)
        self.assertIn("### Changed", text)
        self.assertIn("£249.99", text)
        self.assertIn("+£10.00", text)
        self.assertIn("HTTP 403", text)
        self.assertIn("Prices were not edited.", text)


if __name__ == "__main__":
    unittest.main()
