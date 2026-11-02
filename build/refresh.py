#!/usr/bin/env python3
"""The weekly re-check list: every page a category's prices and plans rest on.

GitHub runs this on a schedule (`.github/workflows/refresh.yml`) and files what
it prints as an issue, which is the nudge to do the work. It reads no vendor
page and writes no data: whether a page still shows a price is a person's job,
because the vendors draw prices client-side, answer a script with a bot wall,
and sell through shops that do the same. What this can do is say which
categories are a week past their check and list the pages behind every figure,
so the job arrives as links rather than as archaeology.

Exit status is 1 when any category is a week or more past its checked date,
which is the run that opens the issue.

    python build/refresh.py
    python build/refresh.py --list          # one page per line, for a diff
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from catalog import CATEGORIES

import rows

WEEK = 7


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
