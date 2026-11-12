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
from html import escape as html_escape

from catalog import CATEGORIES
from .context import ROOT
from .data import BLOCKER_CUES
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
    "previous",
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
        # The power filter is a short list of choices, not the data's whole
        # vocabulary. A category with more than four exact values groups them;
        # every value is covered once so no row can fall out of the filter.
        bands = cat.get("power_filters")
        options = bands or cat["powers"]
        if len(options) > 4:
            problems.append(
                f"{slug}: the power filter offers {len(options)} choices, so it needs power_filters"
            )
        if bands:
            vocab = sorted(key for key, _ in cat["powers"])
            covered = sorted(member for _, members in bands for member in members)
            if covered != vocab:
                problems.append(
                    f"{slug}: power_filters cover {covered} but the vocabulary is {vocab}"
                )
            if len({label for label, _ in bands}) != len(bands):
                problems.append(f"{slug}: two power_filters bands share a label")
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
        # A paid link is disclosed on the page that carries it, and the old
        # no-affiliate promise cannot survive in a stale template.
        text = re.sub(r"\s+", " ", html)
        # The filter group is named by the record's own power facet. The
        # printers page shipped headed "Power", the doorbells' word, over three
        # groups of ink choices, because the template held the word for every
        # category rather than reading it from the record.
        legend = dict(cat["facets"]).get("power")
        if not legend:
            problems.append(f"{slug}: no power facet names its filter group")
        elif html_escape(legend) not in re.findall(
            r"<fieldset><legend>([^<]+)</legend>", html
        ):
            problems.append(
                f"{slug}: the filter group is not headed its own power facet {legend!r}"
            )
        if "No affiliate links" in text:
            problems.append(f"{slug}: the page still claims there are no affiliate links")
        if "Some links are paid links" not in text:
            problems.append(f"{slug}: the page does not name its paid links")
        if "No cookies" not in text:
            problems.append(f"{slug}: the page no longer says it sets no cookie")
        if "As an Amazon Associate I earn from qualifying purchases" not in text:
            problems.append(f"{slug}: the page does not carry the Amazon Associates statement")
        # One disclosure holds every category, and it names this page as current.
        menu = re.search(r'<nav class="cats".*?</nav>', html, re.S)
        if not menu:
            problems.append(f"{slug}: the page has no category menu")
        else:
            markup = menu.group(0)
            if markup.count('<details class="catmenu">') != 1:
                problems.append(f"{slug}: the category menu is not one disclosure")
            if markup.count('aria-current="page"') != 1:
                problems.append(f"{slug}: the category menu does not mark one current page")
            if len(re.findall(r"<a ", markup)) != len(CATEGORIES):
                problems.append(f"{slug}: the category menu does not link every category")
        # A lineup is checked, not assumed. Every brand in a table names the
        # model it is selling now, and that model is one of the brand's rows: the
        # rings page shipped a generation behind, with Ring 5 already on sale,
        # because nothing ever asked the question per brand. The parse boundary
        # has already named a malformed entry by brand; these are the editorial
        # questions the record still asks over the typed maps.
        problems.extend(cat.get("lineup_problems", ()))
        current = cat.get("current")
        if current is not None:
            unasked = sorted({row["brand"] for row in rows} - set(current))
            if unasked:
                problems.append(
                    f"{slug}: no current model named for {', '.join(unasked)}"
                )
            for brand, named in current.items():
                if isinstance(named, tuple):
                    model, why = named
                    if not str(why).strip():
                        problems.append(
                            f"{slug}: {brand} is marked as having no current model "
                            "without saying why"
                        )
                    continue
                found = [row for row in rows if row["id"] == named]
                if not found:
                    problems.append(
                        f"{slug}: {brand}'s current model {named!r} is not a row"
                    )
                elif found[0]["brand"] != brand:
                    problems.append(
                        f"{slug}: {brand}'s current model {named!r} belongs to "
                        f"{found[0]['brand']}"
                    )
        # A brand's older model is usually the cheaper way in, so it is asked
        # for as deliberately as the newest one. The printers page carried four
        # brands and no last-generation row at all, because only `current` was
        # ever asked, and the saving a reader would notice was never priced.
        previous = cat.get("previous") or {}
        unasked = sorted({row["brand"] for row in rows} - set(previous))
        if unasked:
            problems.append(
                f"{slug}: no last-generation model named for {', '.join(unasked)}"
            )
        for brand, named in previous.items():
            if isinstance(named, tuple):
                if (
                    len(named) not in (2, 3)
                    or named[0] is not None
                    or (len(named) == 3 and named[2] is not True)
                ):
                    problems.append(
                        f"{slug}: {brand}'s pair must be (None, reason) or "
                        "(None, reason, True)"
                    )
                    continue
                _, why = named[:2]
                reason = str(why or "").strip()
                if not reason:
                    problems.append(
                        f"{slug}: {brand} is marked as having no last-generation "
                        "row without saying why"
                    )
                elif not any(cue in reason.lower() for cue in BLOCKER_CUES):
                    problems.append(
                        f"{slug}: {brand}'s reason {reason!r} names no page or "
                        "listing to read"
                    )
                continue
            found = [row for row in rows if row["id"] == named]
            if not found:
                problems.append(
                    f"{slug}: {brand}'s last-generation model {named!r} is not a row"
                )
                continue
            if found[0]["brand"] != brand:
                problems.append(
                    f"{slug}: {brand}'s last-generation model {named!r} belongs "
                    f"to {found[0]['brand']}"
                )
            if (cat.get("current") or {}).get(brand) == named:
                problems.append(
                    f"{slug}: {brand}'s last-generation model {named!r} is also "
                    "its current one"
                )
        # An editorial jump goes to a row that is on the page. The rings page
        # shipped two links keyed to a name that was not a row id, so a reader
        # clicking "RingConn Gen 3" in the lead landed nowhere at all.
        on_page = set(re.findall(r'id="(m-[a-z0-9-]+)"', html))
        for target in set(re.findall(r'class="jump" href="#(m-[a-z0-9-]+)"', html)):
            if target not in on_page:
                problems.append(
                    f"{slug}: a link jumps to #{target}, which is not a row on the page"
                )
        # A row that lists its shops shows one of them, and the page says how
        # that one was chosen: the link on the price goes to the winning shop,
        # and the method states the window it may have cost the reader.
        offered = [row for row in rows if row.get("offers")]
        if offered and ("Where to buy." not in text or "within £5" not in text):
            problems.append(
                f"{slug}: rows list offers but the method never states the rule"
            )
        for row in offered:
            block = re.search(
                rf'<tbody class="item" id="m-{re.escape(row["id"])}".*?</tbody>',
                html, re.S,
            )
            if not block:
                problems.append(f"{row['id']}: has no row on the page to read its offer from")
                continue
            markup = block.group(0)
            if f'data-price="{row["price"]}"' not in markup:
                problems.append(
                    f"{row['id']}: the table does not show the price the offers pick"
                )
            if markup.count(row["offer_at"]) < 1:
                problems.append(
                    f"{row['id']}: the table does not name {row['offer_at']!r} as where the price is"
                )
            # Escaped, because an Awin deep link carries `&` between its
            # parameters and the markup cannot.
            winning = html_escape(cat["sources"][row["price_src"]][1])
            if winning not in markup:
                problems.append(
                    f"{row['id']}: the price does not link to the shop it came from"
                )
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


SUMMARY_JS = """() => {
    const summary = document.querySelector('nav.cats details summary');
    const css = getComputedStyle(summary);
    const arrow = getComputedStyle(summary, '::after').transform;
    const parts = arrow === 'none' ? null
        : arrow.slice(arrow.indexOf('(') + 1, -1).split(',').map(Number);
    return {
        pad: css.paddingTop + ' ' + css.paddingRight,
        // The chevron is a turned square: its angle says which way it points
        // and the length of its offset says how far it is nudged from the
        // word. A rotation turns the offset too, so the two are read apart.
        angle: parts ? Math.round(Math.atan2(parts[1], parts[0]) * 180 / Math.PI) : null,
        nudge: parts ? Math.round(Math.hypot(parts[4], parts[5]) * 10) / 10 : null
    };
}"""

def records(ctx):
    problems = record_problems(ctx.pages)
    # A category that never audited its brands' lineups is not failed, because
    # the fix is a human reading three shops, but it is not allowed to pass
    # silently either: the note names it on every run until it is done.
    for cat in CATEGORIES:
        if cat.get("current") is None:
            ctx.note(
                f"{cat['slug']}: its brands' current models have not been audited; "
                "add a `current` map at the next price check"
            )
        # A bare pair is still waiting for a row. A pair with a third element,
        # True, is a verified absence and is left out of the note.
        waiting = [
            brand
            for brand, named in (cat.get("previous") or {}).items()
            if isinstance(named, tuple) and len(named) == 2
        ]
        if waiting:
            ctx.note(
                f"{cat['slug']}: no last-generation row yet for "
                f"{', '.join(sorted(waiting))}"
            )
    return problems


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
        # The visitor counter is a third-party request. The audit runs without
        # outbound network, so stub it rather than report its DNS failure as a
        # page error.
        page.route("https://gc.zgo.at/**", lambda route: route.fulfill(status=204, body=""))
        page.route("https://subfreeuk.goatcounter.com/**", lambda route: route.fulfill(status=204, body=""))
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
        # The category switcher is one disclosure that opens, lists every page
        # and marks this one. A native details needs no script to pass.
        if page.locator("nav.cats details.catmenu").count() != 1:
            problems.append(f"{cat['page']} has no single category menu")
        else:
            if page.evaluate("() => document.querySelector('nav.cats details').open"):
                problems.append(f"{cat['page']} opens its category menu before a click")
            # The switcher's own metrics: a summary that reaches its text and a
            # chevron that turns on the diagonal it closes back along.
            closed = page.evaluate(SUMMARY_JS)
            page.click("nav.cats summary")
            if not page.evaluate("() => document.querySelector('nav.cats details').open"):
                problems.append(f"{cat['page']} does not open its category menu")
            page.wait_for_timeout(250)
            opened = page.evaluate(SUMMARY_JS)
            if closed["pad"] != "0px 8px":
                problems.append(
                    f"{cat['page']} pads the category menu {closed['pad']!r}, expected 0px 8px"
                )
            if (closed["angle"], closed["nudge"]) != (45, 3):
                problems.append(f"{cat['page']} points the closed chevron {closed}")
            if (opened["angle"], opened["nudge"]) != (-135, 3):
                problems.append(f"{cat['page']} points the open chevron {opened}")
            if page.locator("nav.cats details a").count() != len(CATEGORIES):
                problems.append(f"{cat['page']} does not list every category")
            if page.locator("nav.cats details a[aria-current=page]").count() != 1:
                problems.append(f"{cat['page']} does not mark the current category")
            page.click("h1")
            if page.evaluate("() => document.querySelector('nav.cats details').open"):
                problems.append(f"{cat['page']} keeps its category menu open on an outside click")
            page.click("nav.cats summary")
            page.keyboard.press("Escape")
            if page.evaluate("() => document.querySelector('nav.cats details').open"):
                problems.append(f"{cat['page']} keeps its category menu open on Escape")
            if page.evaluate("() => document.activeElement.tagName") != "SUMMARY":
                problems.append(f"{cat['page']} does not return focus to the menu on Escape")
        # A banded power filter still selects by the row's exact values: every
        # ticked band shows its rows and hides the rest.
        bands = cat.get("power_filters")
        if bands:
            boxes = page.locator("input.f-pw")
            if boxes.count() != len(bands):
                problems.append(
                    f"{cat['page']} offers {boxes.count()} power filters for {len(bands)} bands"
                )
            else:
                for i, (_, members) in enumerate(bands):
                    boxes.nth(i).check()
                    page.wait_for_timeout(100)
                    shown_ids = set(page.eval_on_selector_all(
                        "tbody.item:not([hidden])", "els => els.map(e => e.dataset.id)"))
                    want = {r["id"] for r in rows if set(r["power"]) & set(members)}
                    if shown_ids != want:
                        problems.append(
                            f"{cat['page']} band {i + 1} shows {sorted(shown_ids)}, not {sorted(want)}"
                        )
                    boxes.nth(i).uncheck()
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
        "category page behaviour", "post", 94,
        "every non-root page renders its own rows, sorts, compares, opens a source card and loads every asset",
        page_behaviour,
    ),
]
