"""The ledger boundary: apply observed prices, reject stale bases, round-trip."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from ledger import (
    Ledger,
    PriceEntry,
    Reading,
    RowEntry,
    apply_to_rows,
    load,
    note_with_date,
    write,
)


def price_row(**overrides):
    row = {
        "id": "epson-et-2951",
        "cat": "printers",
        "price": 319.99,
        "price_src": "epson_et2951",
        "price_note": "Epson UK, checked 1 January 2026",
    }
    row.update(overrides)
    return row


def offer_row():
    return {
        "id": "oura-ring-4",
        "cat": "rings",
        "offers": [
            {"shop": "Argos", "src": "argos_oura4", "price": 329.0, "pay": 1,
             "note": "Silver, size 10"},
        ],
    }


class NoteTests(unittest.TestCase):
    def test_a_date_in_the_note_moves(self) -> None:
        self.assertEqual(
            note_with_date("Epson UK, checked 1 January 2026", "2026-11-16"),
            "Epson UK, checked 16 November 2026",
        )

    def test_a_note_without_a_date_gets_one(self) -> None:
        self.assertEqual(
            note_with_date("Amazon UK, without the Sync Module", "2026-11-16"),
            "Amazon UK, without the Sync Module, checked 16 November 2026",
        )

    def test_an_empty_note_is_a_date(self) -> None:
        self.assertEqual(note_with_date("", "2026-11-16"), "checked 16 November 2026")


class ApplyTests(unittest.TestCase):
    def test_an_override_replaces_the_price_and_moves_the_date(self) -> None:
        row = price_row()
        ledger = Ledger(
            rows={"epson-et-2951": RowEntry(price=PriceEntry(319.99, 299.99, "2026-11-16"))},
            updated="",
        )
        problems = apply_to_rows(ledger, [row], {"epson_et2951": ("Epson", "https://e")})
        self.assertEqual(problems, [])
        self.assertEqual(row["price"], 299.99)
        self.assertEqual(row["checked_iso"], "2026-11-16")
        self.assertEqual(row["price_note"], "Epson UK, checked 16 November 2026")

    def test_a_stale_base_does_not_apply(self) -> None:
        row = price_row(price=309.99)
        ledger = Ledger(
            rows={"epson-et-2951": RowEntry(price=PriceEntry(319.99, 299.99, "2026-11-16"))},
            updated="",
        )
        problems = apply_to_rows(ledger, [row], {"epson_et2951": ("Epson", "https://e")})
        self.assertEqual(row["price"], 309.99)
        self.assertNotIn("checked_iso", row)
        self.assertIn("base is 319.99", problems[0])
        self.assertIn("authored price is 309.99", problems[0])

    def test_an_offer_override_uses_the_offer_price(self) -> None:
        row = offer_row()
        ledger = Ledger(
            rows={"oura-ring-4": RowEntry(offers={"argos_oura4": PriceEntry(329.0, 319.0, "2026-11-16")})},
            updated="",
        )
        problems = apply_to_rows(ledger, [row], {"argos_oura4": ("Argos", "https://a")})
        self.assertEqual(problems, [])
        self.assertEqual(row["offers"][0]["price"], 319.0)
        self.assertNotIn("checked_iso", row)

    def test_a_price_entry_on_an_offer_row_is_refused(self) -> None:
        ledger = Ledger(
            rows={"oura-ring-4": RowEntry(price=PriceEntry(329.0, 319.0, "2026-11-16"))},
            updated="",
        )
        problems = apply_to_rows(ledger, [offer_row()], {"argos_oura4": ("Argos", "https://a")})
        self.assertIn("its offers are the price", problems[0])

    def test_an_unknown_row_is_refused(self) -> None:
        ledger = Ledger(
            rows={"gone": RowEntry(price=PriceEntry(1.0, 2.0, "2026-11-16"))},
            updated="",
        )
        self.assertEqual(
            apply_to_rows(ledger, [price_row()], {}),
            ["price ledger: gone is not a row"],
        )


class RecordTests(unittest.TestCase):
    def test_a_change_is_stored_and_a_return_to_base_clears_it(self) -> None:
        changed, written = Ledger(rows={}, updated="").record(
            [Reading("epson-et-2951", "price", "epson_et2951", 319.99, 299.99)],
            "2026-11-16",
        )
        self.assertEqual(written, 1)
        self.assertEqual(changed.rows["epson-et-2951"].price,
                         PriceEntry(319.99, 299.99, "2026-11-16"))
        back, written = changed.record(
            [Reading("epson-et-2951", "price", "epson_et2951", 319.99, 319.99)],
            "2026-11-17",
        )
        self.assertEqual(written, 1)
        self.assertEqual(back.rows["epson-et-2951"].price,
                         PriceEntry(319.99, None, "2026-11-17"))

    def test_a_same_day_repeat_writes_nothing(self) -> None:
        reading = Reading("epson-et-2951", "price", "epson_et2951", 319.99, 299.99)
        first, _ = Ledger(rows={}, updated="").record([reading], "2026-11-16")
        again, written = first.record([reading], "2026-11-16")
        self.assertEqual(written, 0)
        self.assertEqual(again.rows, first.rows)

    def test_an_offer_keeps_its_siblings(self) -> None:
        first, _ = Ledger(rows={}, updated="").record(
            [
                Reading("oura-ring-4", "offer", "argos_oura4", 329.0, 319.0),
                Reading("oura-ring-4", "offer", "currys_oura5", 349.0, 349.0),
            ],
            "2026-11-16",
        )
        self.assertEqual(set(first.rows["oura-ring-4"].offers or {}),
                         {"argos_oura4", "currys_oura5"})


class FileTests(unittest.TestCase):
    def test_a_written_ledger_reads_back(self) -> None:
        ledger = Ledger(
            rows={"epson-et-2951": RowEntry(price=PriceEntry(319.99, 299.99, "2026-11-16"))},
            updated="",
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "price_ledger.json"
            write(ledger, path, updated="2026-11-16T18:00:00+00:00")
            loaded, problems = load(path)
        self.assertEqual(problems, [])
        self.assertEqual(loaded.rows, ledger.rows)
        self.assertEqual(loaded.updated, "2026-11-16T18:00:00+00:00")

    def test_a_bad_entry_is_named_not_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "price_ledger.json"
            path.write_text(json.dumps({
                "version": 1,
                "rows": {"epson-et-2951": {"price": {"base": 319.99, "checked": "soon"}}},
            }), encoding="utf-8")
            loaded, problems = load(path)
        self.assertEqual(loaded.rows, {})
        self.assertIn("not an ISO date", problems[0])

    def test_a_future_date_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "price_ledger.json"
            path.write_text(json.dumps({
                "version": 1,
                "rows": {"epson-et-2951": {"price": {"base": 319.99, "checked": "2999-01-01"}}},
            }), encoding="utf-8")
            _, problems = load(path)
        self.assertIn("in the future", problems[0])


if __name__ == "__main__":
    unittest.main()
