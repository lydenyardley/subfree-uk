"""Every category is a record the build can render, and no page borrows another's words.

Two checks keep expansion honest. The first builds each category from its
record and reads the figures back: the count in the copy is the count of rows,
the verdict the page recommends is one a row carries, and the files it writes
are its own. The second reads each rendered page for another category's noun,
which is what a copy-pasted page looks like when the second category lands.
"""
import os
import posixpath
import re

from catalog import CATEGORIES
from .context import ROOT
from .registry import Check

# What `build.build(cat)` reads. A record missing one of these is a category
# that fails at the first render rather than at the first reader.
REQUIRED = (
    "slug", "route", "page", "alias", "csv", "md", "noun", "nouns",
    "title", "description", "h1", "dek", "mast", "mast_long", "skip",
    "table_name", "table_caption", "cmp_caption", "count_line", "empty_line",
    "no_match", "shown", "months", "period", "period_adj", "period_short",
    "cap", "score_max", "score_parts", "rec", "required_keys", "facets",
    "powers", "power_hint", "filters", "verdicts", "headline", "claims",
    "compare", "pin", "sort", "method", "csv_head", "md_head", "not_found",
)


def record_problems(pages):
    problems = []
    seen = {}
    for cat in CATEGORIES:
        slug = cat.get("slug", "(no slug)")
        # `route` is "" for a page at the site root, so presence is the test.
        missing = [key for key in REQUIRED if key not in cat or cat[key] is None]
        if missing:
            problems.append(f"{slug}: the record is missing {', '.join(missing)}")
            continue
        rows = cat.get("rows")
        if not rows:
            problems.append(f"{slug}: no rows are attached to the record")
            continue
        # The copy's own figures are the data's, so a category that grew a row
        # cannot keep claiming the old count.
        n = len(rows)
        for key in ("description", "dek"):
            text = cat[key].format(n=n, period=cat["period_adj"])
            if str(n) not in text:
                problems.append(f"{slug}: {key} does not name the {n} rows the data has")
        if not any(row.get("verdict") == cat["headline"] for row in rows):
            problems.append(
                f"{slug}: no row carries the headline verdict {cat['headline']!r}"
            )
        # The score the page prints as "/8" is the sum of the parts it explains,
        # and the pins are rows of the table it pins.
        parts = sum(maximum for _, _, maximum in cat["score_parts"])
        if parts != cat["score_max"]:
            problems.append(
                f"{slug}: score_max is {cat['score_max']}, its parts add to {parts}"
            )
        keys = {key for _, key in cat["compare"]}
        stray = [key for key in cat["pin"] if key not in keys]
        if stray:
            problems.append(f"{slug}: pinned rows {', '.join(stray)} are not in the comparison")
        for key in ("page", "alias", "csv", "md"):
            path = cat[key]
            if path in seen:
                problems.append(f"{slug}: {path} is also {seen[path]}'s {key}")
            seen[path] = f"{slug}'s"
        if pages.get(cat["page"]) is None:
            problems.append(f"{slug}: {cat['page']} was not written")
        # A page at a nested route reaches the shared assets one level up; this
        # is the rule that makes `/cameras/` work without a second stylesheet.
        html = pages.get(cat["page"], "")
        for name in ("assets/page.css", "assets/page.js"):
            found = re.search(rf'(?:href|src)="([^"]*{re.escape(name)}[^"]*)"', html)
            if not found:
                problems.append(f"{slug}: {cat['page']} does not load {name}")
                continue
            href = found.group(1).split("?")[0]
            resolved = posixpath.normpath(posixpath.join(cat["route"], href))
            if resolved != name:
                problems.append(
                    f"{slug}: {cat['page']} asks for {name} as {href!r}, which resolves to "
                    f"{resolved!r} from {cat['route'] or './'}"
                )
    return problems


def own_words(pages):
    """Each page speaks its own category's nouns and no other's."""
    problems = []
    for cat in CATEGORIES:
        text = pages.get(cat["page"], "")
        for other in CATEGORIES:
            if other is cat:
                continue
            for word in {other["noun"], other["nouns"]}:
                if re.search(rf"\b{re.escape(word)}\b", text, re.I):
                    problems.append(
                        f"{cat['page']} mentions {word!r}, which is {other['slug']}'s word"
                    )
        if cat["nouns"] not in text:
            problems.append(f"{cat['page']} never says {cat['nouns']!r}")
    return problems


def records(ctx):
    return record_problems(ctx.pages)


def words(ctx):
    return own_words(ctx.pages)


CHECKS = [
    Check(
        "category records", "static", 91,
        "every category record renders, its copy counts its rows, and its files and asset paths are its own",
        records,
    ),
    Check(
        "category words", "static", 92,
        "each page speaks its own category's nouns, and no other category's",
        words,
    ),
]
