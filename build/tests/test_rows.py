"""Offer selection against the row's check date."""

from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import rows


def offer(shop: str, price: float, pay: int, **extra: object) -> dict[str, object]:
    return dict(
        shop=shop, src=shop.lower(), price=price, pay=pay, note="one size",
        **extra,
    )


class StaleOfferTests(unittest.TestCase):
    def test_an_offer_with_no_ledger_date_uses_the_row_check_date(self) -> None:
        today = date(2026, 11, 16)
        old = (today - timedelta(days=31)).isoformat()
        unread = offer("Argos", 95.0, rows.PAY_RETAIL)
        live = offer("Amazon UK", 100.0, rows.PAY_AMAZON,
                     checked_iso=today.isoformat())

        self.assertTrue(rows.offer_is_stale(unread, today, old))
        self.assertEqual(
            rows.offer_winner([unread, live], today, old)["shop"], "Amazon UK"
        )
        self.assertEqual(
            rows.offer_shown([unread, live], today, old)["shop"], "Amazon UK"
        )

        self.assertFalse(rows.offer_is_stale(unread, today, today.isoformat()))
        self.assertEqual(
            rows.offer_winner([unread], today, today.isoformat())["shop"], "Argos"
        )


if __name__ == "__main__":
    unittest.main()
