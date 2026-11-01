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
from .registry import Check, Skip

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
        # `alias` is optional: a category that never had an old filename has
        # no redirect to write, and a None there is not a missing record field.
        missing = [
            key for key in REQUIRED
            if key not in cat or (cat[key] is None and key != "alias")
        ]
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
        for key in ("page", "csv", "md") + (("alias",) if cat.get("alias") else ()):
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
        # The category switcher must name the other pages, so it is not copy
        # about this category and is left out of the vocabulary test.
        text = re.sub(r'<nav class="cats".*?</nav>', "", text, flags=re.S)
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


def page_behaviour(ctx):
    """Every non-root category's page renders and its controls read its own data.

    The rest of the browser audit drives the first category's page. A second
    page shares the script but has its own rows, so this opens each other
    route and proves the script picked that category up: the row count, a sort
    over the data's own prices, the comparison, a source card, every asset it
    asked for and a clean console.
    """
    if ctx.browser is None:
        raise Skip("no browser in this run")
    base = ctx.url.rsplit("/", 1)[0] + "/"
    problems = []
    for cat in CATEGORIES[1:]:
        page = ctx.browser.new_page(viewport={"width": 1280, "height": 900})
        errors, refused = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.on(
            "response",
            lambda response: refused.append(f"{response.status} {response.url}")
            if response.status >= 400
            else None,
        )
        url = base + cat["route"]
        response = page.goto(url, wait_until="load")
        page.wait_for_timeout(250)
        if response is None or response.status != 200:
            problems.append(f"{url} did not load (status {getattr(response, 'status', None)})")
            page.close()
            continue
        rows = cat["rows"]
        shown = page.locator("tbody.item").count()
        if shown != len(rows):
            problems.append(f"{cat['page']} shows {shown} rows for {len(rows)} in the data")
            page.close()
            continue
        page.select_option("#sort", "price")
        page.wait_for_timeout(200)
        first = page.locator("tbody.item:not([hidden])").first.get_attribute("data-price")
        cheapest = min(row["price"] for row in rows)
        if first is None or abs(float(first) - cheapest) > 0.005:
            problems.append(
                f"{cat['page']} sorts by price to {first!r}, not the row at {cheapest:.2f}"
            )
        boxes = page.locator("input.cmp")
        wanted = min(2, len(rows))
        for i in range(wanted):
            boxes.nth(i).check()
        page.wait_for_timeout(200)
        if page.locator("#tray-go").is_visible():
            page.click("#tray-go")
        else:
            page.click("#cmp-inline")
        page.wait_for_timeout(300)
        if page.locator("#compare").is_hidden():
            problems.append(f"{cat['page']} did not open its comparison")
        else:
            columns = page.locator("#cmp-table thead th[data-id]").count()
            if columns != wanted:
                problems.append(
                    f"{cat['page']} compares {columns} columns for {wanted} ticked"
                )
        page.locator("tbody.item:not([hidden]) a.src").first.click()
        page.wait_for_timeout(200)
        if not page.evaluate("() => document.getElementById('card').open"):
            problems.append(f"{cat['page']} did not open a source card")
        if errors:
            problems.append(f"{cat['page']} console: {'; '.join(errors[:3])}")
        if refused:
            problems.append(f"{cat['page']} refused: {'; '.join(refused[:3])}")
        page.close()
    return problems


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
    Check(
        "category page behaviour", "post", 93,
        "every non-root page renders its own rows, sorts, compares, opens a source card and loads every asset",
        page_behaviour,
    ),
]
