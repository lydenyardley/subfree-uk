"""Every wanted figure is measured against its own ledger check date."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from ledger import Ledger, PriceEntry, RowEntry
from price_watch import Want, coverage, coverage_lines, parse_args


def want(row_id: str, kind: str, source: str, shop: str = "") -> Want:
    return Want(
        row_id=row_id,
        category="rings",
        brand="Oura",
        model="Ring 4",
        kind=kind,
        expected=100.0,
        source=source,
        source_name=source,
        url=f"https://example.test/{source}",
        shop=shop,
    )


def wanted() -> list[Want]:
    return [
        want("oura-4", "price", "direct"),
        want("oura-4", "offer", "argos", "Argos"),
        want("oura-4", "offer", "missing", "Currys"),
    ]


def sample_ledger(
    price_checked: str = "2026-11-16",
    offer_checked: str = "2026-11-01",
) -> Ledger:
    return Ledger(
        rows={
            "oura-4": RowEntry(
                price=PriceEntry(100.0, None, price_checked),
                offers={"argos": PriceEntry(100.0, None, offer_checked)},
            )
        },
        updated="",
    )


class CoverageTests(unittest.TestCase):
    def test_each_wanted_entry_uses_its_own_ledger_date(self) -> None:
        day = date(2026, 11, 16)
        cov = coverage(wanted(), sample_ledger(), day)

        self.assertEqual(cov.total, 3)
        self.assertEqual(cov.fresh_count, 1)
        self.assertEqual(cov.stale_count, 1)
        self.assertEqual(cov.missing_count, 1)
        self.assertEqual(
            [entry.checked for entry in cov.entries],
            ["2026-11-16", "2026-11-01", None],
        )
        self.assertEqual([entry.age for entry in cov.entries], [0, 15, None])
        self.assertFalse(cov.healthy)

    def test_the_coverage_window_is_per_entry(self) -> None:
        day = date(2026, 11, 16)
        cov = coverage(wanted(), sample_ledger(), day, max_age=30)

        self.assertEqual(cov.fresh_count, 2)
        self.assertEqual(cov.stale_count, 0)
        self.assertEqual(cov.missing_count, 1)
        self.assertFalse(cov.healthy)

    def test_a_fully_fresh_ledger_is_healthy(self) -> None:
        day = date(2026, 11, 16)
        cov = coverage(
            wanted()[:2],
            sample_ledger(offer_checked="2026-11-15"),
            day,
        )

        self.assertTrue(cov.healthy)
        self.assertEqual(
            cov.summary(),
            "2 of 2 wanted prices and offers were checked within 7 days (100%).",
        )

    def test_the_report_names_the_stale_source(self) -> None:
        day = date(2026, 11, 16)
        text = "\n".join(
            coverage_lines(coverage(wanted()[:2], sample_ledger(), day))
        )

        self.assertIn("1 of 2 wanted prices and offers", text)
        self.assertIn("Oura Ring 4 (Argos offer)", text)
        self.assertIn("2026-11-01", text)
        self.assertIn("15d", text)

    def test_coverage_is_an_explicit_mode(self) -> None:
        self.assertTrue(parse_args(["--coverage"]).coverage)
        self.assertFalse(parse_args([]).coverage)


if __name__ == "__main__":
    unittest.main()
