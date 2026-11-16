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
    availability_state,
    card_matches,
    card_price,
    choose_product,
    configuration_matches,
    fallback_is_better,
    first_price,
    mark_fallback,
    needs_fallback,
    parse_args,
    parse_money,
    products_from_jsonld,
    read_css,
    read_jsonld,
    read_listing_cards,
    read_stock,
    report,
    same_reading,
    stock_label,
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

    def test_availability_reads_schema_names(self) -> None:
        self.assertFalse(availability_state("https://schema.org/OutOfStock"))
        self.assertTrue(availability_state("https://schema.org/InStock"))
        self.assertIsNone(availability_state(""))

    def test_product_availability_is_a_fallback(self) -> None:
        products = products_from_jsonld([
            '{"@type":"Product","name":"X",'
            '"availability":"https://schema.org/OutOfStock",'
            '"offers":{"price":"10.00","priceCurrency":"GBP"}}'
        ])
        self.assertEqual(products[0].availability, "https://schema.org/OutOfStock")

    def test_stock_changes_belong_to_offers(self) -> None:
        offer = Observation(
            want=make_want(kind="offer", shop="Argos"),
            status=READ, observed=239.99, available=True,
        )
        self.assertTrue(offer.changed)
        price = Observation(
            want=make_want(), status=READ, observed=239.99, available=True
        )
        self.assertFalse(price.changed)
        unknown = Observation(
            want=make_want(kind="offer", shop="Argos", in_stock=False),
            status=READ, observed=239.99, available=None,
        )
        self.assertFalse(unknown.changed)

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
            (
                "#corePrice_feature_div .a-price .a-offscreen",
                "#tp_price_block_total_price_ww .a-offscreen",
            ),
        )

    async def test_amazon_stock_is_read_from_the_availability_area(self) -> None:
        page = await self.open_fixture("stock-amazon.html")
        try:
            rule = adapter_for(make_want(url="https://www.amazon.co.uk/dp/X")).stock
            assert rule is not None
            self.assertIs(await read_stock(page, rule), True)
        finally:
            await page.close()

    async def test_argos_stock_negative_message_beats_the_button(self) -> None:
        page = await self.open_fixture("stock-argos.html")
        try:
            rule = adapter_for(make_want(url="https://www.argos.co.uk/product/1")).stock
            assert rule is not None
            self.assertIs(await read_stock(page, rule), False)
        finally:
            await page.close()

    async def test_currys_stock_is_read_from_the_status_area(self) -> None:
        page = await self.open_fixture("stock-currys.html")
        try:
            rule = adapter_for(
                make_want(url="https://www.currys.co.uk/products/x.html")
            ).stock
            assert rule is not None
            self.assertIs(await read_stock(page, rule), True)
        finally:
            await page.close()

    async def test_stock_ignores_a_related_products_out_of_stock_text(self) -> None:
        page = await self.open_fixture("stock-ambiguous.html")
        try:
            rule = adapter_for(
                make_want(url="https://www.currys.co.uk/products/x.html")
            ).stock
            assert rule is not None
            self.assertIsNone(await read_stock(page, rule))
        finally:
            await page.close()

    async def test_conflicting_stock_signals_read_as_out_of_stock(self) -> None:
        page = await self.open_fixture("stock-conflict.html")
        try:
            rule = adapter_for(make_want(url="https://www.amazon.co.uk/dp/X")).stock
            assert rule is not None
            self.assertIs(await read_stock(page, rule), False)
        finally:
            await page.close()

    def test_a_second_read_must_match_price_and_stock(self) -> None:
        first = Observation(
            want=make_want(kind="offer", shop="Argos"),
            status=READ, observed=239.99, available=False,
        )
        same = Observation(
            want=first.want, status=READ, observed=239.99, available=False
        )
        price_moved = Observation(
            want=first.want, status=READ, observed=249.99, available=False
        )
        stock_moved = Observation(
            want=first.want, status=READ, observed=239.99, available=True
        )
        self.assertTrue(same_reading(first, same))
        self.assertFalse(same_reading(first, price_moved))
        self.assertFalse(same_reading(first, stock_moved))

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

    def test_the_fallback_is_opt_out_for_the_runner(self) -> None:
        self.assertFalse(parse_args([]).no_fallback)
        self.assertTrue(parse_args(["--no-fallback"]).no_fallback)

    def test_apply_is_opt_in(self) -> None:
        self.assertFalse(parse_args([]).apply)
        self.assertTrue(parse_args(["--apply"]).apply)

    def test_a_css_page_has_to_name_the_offer_configuration(self) -> None:
        samsung = make_want(
            source="amz_samsung",
            configuration="Titanium Black, size 7",
        )
        self.assertTrue(
            configuration_matches(
                samsung,
                "Samsung Galaxy Ring, Size 7, Titanium Black, 2 Year Warranty",
            )
        )
        self.assertFalse(
            configuration_matches(
                samsung,
                "Samsung Galaxy Ring, Size 8, Titanium Black, 2 Year Warranty",
            )
        )
        self.assertTrue(configuration_matches(make_want(configuration="as listed"), "anything"))

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

    def test_report_names_a_stock_change(self) -> None:
        gone = Observation(
            want=make_want(kind="offer", shop="Currys", in_stock=True),
            status=READ,
            observed=239.99,
            method="JSON-LD",
            available=False,
        )
        text = report(
            [gone], datetime(2026, 11, 16, 8, 30, tzinfo=timezone.utc)
        )
        self.assertIn("out of stock", text)
        self.assertIn("£0.00", text)
        self.assertEqual(stock_label(gone), "out of stock")


if __name__ == "__main__":
    unittest.main()
