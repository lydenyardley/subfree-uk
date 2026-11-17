#!/usr/bin/env python3
"""The weekly re-check list: every page a category's prices and plans rest on.

GitHub runs this on a schedule (`.github/workflows/refresh.yml`) and files what
it prints as an issue, which is the nudge to do the work. This file reads no
vendor page and writes no data. The separate browser probe, `price_watch.py`,
reads the recorded prices and reports changes; whether a displayed price is the
right product, in stock and at the stated configuration remains a person's job,
because the vendors draw prices client-side and answer a script with a bot
wall. What this can do is say which categories are a week past their check and
list the pages behind every figure, so the job arrives as links rather than as
archaeology.

Exit status is 1 when any category is a week or more past its checked date, or
when any wanted price or offer is missing from the ledger or older than the
coverage window. That is the run that opens the issue.

    python build/refresh.py
    python build/refresh.py --list          # one page per line, for a diff
"""
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from catalog import CATEGORIES
from price_watch import coverage, coverage_lines, wants

import rows

WEEK = 7
LEDGER_LIMIT = 8


def pages(cat):
    """The cited pages behind one category's prices and plans, without repeats."""
    seen = {}
    for row in rows.ROWS:
        if row["cat"] != cat["slug"]:
            continue
        for key, label in (("price_src", "price"), ("plan_src", "plan")):
            source = row.get(key)
            if not source:
                continue
            name, url = rows.S[source]
            seen.setdefault(url, (name, label, []))[2].append(row["model"])
    return seen


def main():
    flat = "--list" in sys.argv[1:]
    late = []
    cov = coverage(wants(), rows.PRICE_LEDGER)
    if rows.PRICE_LEDGER.updated:
        seen = datetime.fromisoformat(rows.PRICE_LEDGER.updated).date()
        ledger_age = (date.today() - seen).days
    else:
        seen, ledger_age = None, LEDGER_LIMIT + 1
    if ledger_age >= LEDGER_LIMIT:
        late.append("price ledger")
    if flat:
        print(f"price ledger\t{seen or '-'}\t{ledger_age}d\tlast local refresh")
    else:
        where = f"last updated {seen.day} {seen:%B %Y}" if seen else "has never been written"
        print(f"### Price ledger, {where}, {ledger_age} days ago\n")
        print("Run `python build/price_refresh.py` on the local machine.\n")
    if flat:
        print(
            f"coverage\t{cov.fresh_count}/{cov.total}\t"
            f"{cov.stale_count} stale\t{cov.missing_count} missing"
        )
        for entry in cov.entries:
            if entry.fresh:
                continue
            age = "-" if entry.age is None else f"{entry.age}d"
            state = "missing" if entry.checked is None else "stale"
            print(
                f"{state}\t{entry.want.category}\t{entry.want.label}\t"
                f"{entry.checked or '-'}\t{age}"
            )
    else:
        print("\n".join(coverage_lines(cov)) + "\n")
    if not cov.healthy:
        late.append("coverage")
    for cat in CATEGORIES:
        checked = date.fromisoformat(cat["checked_iso"])
        age = (date.today() - checked).days
        if age >= WEEK:
            late.append(cat["slug"])
        if flat:
            print(f"{cat['slug']}\t{cat['checked_iso']}\t{age}d\t{cat['nouns']}")
        else:
            heading = f"### {cat['nouns'].title()}, checked {checked.day} {checked:%B %Y}"
            print(f"{heading}, {age} days ago\n")
        for url, (name, label, models) in pages(cat).items():
            if flat:
                print(f"{cat['slug']}\t{label}\t{url}")
            else:
                print(f"- [ ] {label}: [{name}]({url})")
                print(f"  {', '.join(models)}")
        if not flat:
            print()
    if not flat:
        if late:
            print(f"Due: {', '.join(late)}.")
        else:
            print("Nothing is due yet.")
    return 1 if late else 0


if __name__ == "__main__":
    sys.exit(main())
