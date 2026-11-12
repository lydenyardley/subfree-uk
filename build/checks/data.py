"""The dataset behind the page: it loads, its figures recompute, and every open fact names its blocker."""
from datetime import date
import base64
import csv
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys

from catalog import CATEGORIES, CSV_KEYS
from model import Current
from .context import ROOT
from .registry import Check, Skip


BLOCKER_CUES = (
    "app", "support", "docs", "page", "terms", "datasheet", "retailer",
    "listing", "pdf", "faq", "manual", "release notes",
)

WEAK_UNVERIFIED = {"not confirmed", "unknown", "tbc", "pending", "not yet verified"}

# What a first visit reads may weigh, gzipped. The script is shared logic only,
# and each page carries its own rows in the JSON block, so the page's own data
# is the variable. The budgets are in docs/performance-budget.md; each has
# headroom over today's figure, and a change that doubles a page cannot pass by
# being a little over.
TRANSFER_BUDGET = {
    "assets/page.css": 18_000,
    "assets/page.js": 18_000,
}
PAGE_BUDGET = 33_000
TRANSFER_TOTAL = 70_000


def load_rows():
    """The dataset module, imported on its own.

    `rows.py` writes nothing and exits for nothing, so importing it cannot
    disturb the tree the rebuild check has just compared. The page assembly is
    only ever run as a subprocess, by `rebuild()`.
    """
    build_dir = os.path.join(ROOT, "build")
    if build_dir not in sys.path:
        sys.path.insert(0, build_dir)
    try:
        import rows as module
    except Exception as error:
        return None, f"build/rows.py did not import: {type(error).__name__}: {error}"
    return module, None


def unverified_problems(rows):
    problems = []
    for row in rows:
        sentence = (row["unverified"] or "").strip()
        if not sentence:
            continue
        lowered = sentence.lower().strip(" .")
        if lowered in WEAK_UNVERIFIED:
            problems.append(f"{row['id']}: {sentence!r} names no blocker")
        elif not any(cue in lowered for cue in BLOCKER_CUES):
            problems.append(
                f"{row['id']}: {sentence!r} names no blocker (an app, support docs, a retailer)"
            )
    return problems


def data_problems(rows, pages):
    """Recompute every derived figure and compare it with the files that ship."""
    problems = []
    for cat in CATEGORIES:
        problems += rows.row_problems(cat)
        problems += unverified_problems(cat["rows"])
        problems += category_problems(rows, pages, cat)
    return problems


def category_problems(rows, pages, cat):
    """One category's CSV, markdown and page against the rows it was built from."""
    problems = []
    table = cat["rows"]
    if not table:
        return [f"{cat['slug']}: the record has no rows attached"]
    with open(os.path.join(ROOT, cat["csv"]), newline="", encoding="utf-8") as handle:
        shipped = list(csv.DictReader(handle))
    if len(shipped) != len(table):
        return [f"{cat['slug']}: the CSV has {len(shipped)} rows for {len(table)} in the data"]
    for row, out in zip(table, shipped):
        price, extra, sub, months = row["price"], row["extra"], row["sub"], cat["months"]
        nosub3 = round(price + extra, 2)
        sub3 = round(price + months * sub, 2) if sub is not None else None
        options = ([] if not row["free_records"] else [nosub3]) + ([] if sub3 is None else [sub3])
        # A row with neither route has no total; `row_problems()` has already
        # named it, so the recompute does not raise a second time.
        keep3 = min(options) if options else None
        values = {
            "brand": row["brand"], "model": row["model"],
            "rec": cat["rec_label"][row["rec"]],
            "power": "/".join(cat["power_label"][p] for p in row["power"]),
            "price": f"{price:.2f}", "price_note": row["price_note"],
            "price_src": rows.S[row["price_src"]][1], "best": row["best"],
            "catch": row["catch"], "score_total": str(sum(row["score"].values())),
            "nosub3": f"{nosub3:.2f}",
            "sub3": "" if sub3 is None else f"{sub3:.2f}",
            "keep3": "" if keep3 is None else f"{keep3:.2f}",
        }
        # A row with no shop but Amazon prints no figure built on Amazon's price.
        if row.get("price_check"):
            for key in ("price", "nosub3", "keep3") + (("sub3",) if sub3 is not None else ()):
                values[key] = "Check price"
        values = {**values,
            "maths_free": row["maths_free"], "maths_sub": row["maths_sub"],
            "storage": row["storage"], "live": row["live"],
            "alerts": row["alerts"], "ai": row["ai"],
            "history": row["history"], "paywalled": row["paywalled"],
            "sub_text": row["sub_text"], "plan_region": row["plan_region"],
            "ha_text": row["ha_text"], "wifi": row["wifi"],
            "sources": " ; ".join(rows.S[k][1] for k in row["src"]),
            "unverified": row["unverified"], "checked": cat["checked"],
        }
        if len(cat["csv_head"]) != len(CSV_KEYS):
            problems.append(
                f"{cat['slug']}: the CSV has {len(cat['csv_head'])} columns, "
                f"but its rows carry {len(CSV_KEYS)}"
            )
            continue
        shown = [head.format(score_max=cat["score_max"]) for head in cat["csv_head"]]
        for label, key in zip(shown, CSV_KEYS):
            want = values[key]
            if out.get(label) != want:
                problems.append(
                    f"{row['id']}: CSV {label!r} is {out.get(label)!r}, recomputed {want!r}"
                )
        if (row["keep3"], row["nosub3"], row["sub3"]) != (keep3, nosub3, sub3):
            problems.append(f"{row['id']}: a derived figure drifted from price, extra and plan")
        # A row that lists its shops shows the one the rule picks, and names the
        # configuration that shop's price is for. Both are re-derived here, so a
        # hand-edited price or an offers list that moved without a rebuild is
        # caught against the rule the method note prints.
        if row.get("offers"):
            won = rows.offer_shown(row["offers"])
            if (row["price"], row["price_src"]) != (won["price"], won["src"]):
                problems.append(
                    f"{row['id']}: the shown price is not the offer the rule picks"
                )
            want_note = (
                f'{won["shop"]}, {won["note"]}' if won.get("note") else won["shop"]
            )
            if row["price_note"] != want_note:
                problems.append(
                    f"{row['id']}: price_note {row['price_note']!r} does not name the "
                    f"winning shop and its configuration ({want_note!r})"
                )
        for key in ("price_src", "rec_src", "history_src", "ha_src", "plan_src"):
            if row[key] not in rows.S:
                problems.append(f"{row['id']}: {key} {row[key]!r} is not in S")
        for key in row["src"]:
            if key not in rows.S:
                problems.append(f"{row['id']}: source {key!r} is not in S")
        if len(set(row["src"])) != len(row["src"]):
            problems.append(f"{row['id']}: duplicate source keys")
    index = pages[cat["page"]]
    table_rows = index.count('<tbody class="item"')
    if table_rows != len(table):
        problems.append(f"{cat['page']} has {table_rows} rows for {len(table)} in the data")
    for row in table:
        if row["plan_region"] == "EU" and not re.search(
            rf'<tbody class="item" id="m-{row["id"]}"[^>]*data-region="EU"', index
        ):
            problems.append(f"{row['id']}: the EU plan price is not marked as data on the page")
    # A sundry in a 3-year sum is a price from a cited page, not a figure typed
    # into the note. Both places that print the method have to carry the figure
    # the sums were built from, so a re-priced card cannot leave a sentence
    # behind, and the assumption it replaced cannot come back.
    with open(os.path.join(ROOT, cat["md"]), encoding="utf-8") as handle:
        markdown = handle.read()
    # A category whose rows buy a card or a hub has to price it in the method.
    # A ring buys neither, and a printer's extra is ink rather than a sundry, so
    # neither note is made to print a figure its sums never use.
    buys_sundries = any(
        row.get("kit_src") or row.get("extra_src") in ("sandisk_card", "sandisk_stick")
        for row in table
    )
    for name, text in ((cat["page"], index), (cat["md"], markdown)):
        if buys_sundries:
            for sundry, figure in (("microSD card", rows.CARD), ("USB stick", rows.STICK)):
                if f"{sundry} at {rows.money(figure)}" not in text:
                    problems.append(
                        f"the {name} method note does not price the {sundry} "
                        f"at {rows.money(figure)}"
                    )
        if "not from a cited source" in text:
            problems.append(f"the {name} method note still calls a sundry an assumption")
    return problems


def slider_problems(rows, pages):
    """The price slider reaches every price on the page.

    The floor used to be typed in at £40 with a comment about the cheapest
    product; the first doorbell priced below it vanished from the default view
    of the page it was added to. The ends are the data's own now, and a ceiling
    off the handle's step grid would snap the dearest row out of range just as
    quietly, so both are read back from the page.
    """
    problems = []
    for cat in CATEGORIES:
        table = cat["rows"]
        prices = [row["price"] for row in table]
        if not prices:
            problems.append(f"{cat['slug']}: no prices to put on the slider")
            continue
        page = pages[cat["page"]]
        handle = re.search(r'id="f-min"([^>]*)>', page)
        if not handle:
            problems.append(f"{cat['page']}: the price range has no handle to read")
            continue
        attrs = dict(re.findall(r'(min|max|step)="(\d+)"', handle.group(1)))
        if set(attrs) != {"min", "max", "step"}:
            problems.append(f"{cat['page']}: the price range is {attrs}")
            continue
        floor, ceiling, step = int(attrs["min"]), int(attrs["max"]), int(attrs["step"])
        if step < 1:
            problems.append(f"{cat['page']}: the price step is {step}")
        if floor > min(prices):
            problems.append(
                f"{cat['page']}: the slider floor is £{floor}, above the cheapest "
                f"row at £{min(prices):.2f}"
            )
        if ceiling < max(prices):
            problems.append(
                f"{cat['page']}: the slider ceiling is £{ceiling}, below the dearest "
                f"row at £{max(prices):.2f}"
            )
        # A range input snaps a value to its own grid, so an off-grid end is an
        # end the reader cannot actually set.
        if step > 0 and (ceiling - floor) % step:
            problems.append(
                f"{cat['page']}: the slider runs {floor} to {ceiling} in steps of "
                f"{step}, so its own ceiling is not on the grid"
            )
    return problems


def page_data_problems(pages):
    """A page ships its own rows, once, in the block its script reads."""
    problems = []
    for cat in CATEGORIES:
        page = pages[cat["page"]]
        match = re.search(
            r'<script type="application/json" id="rows">(.*?)</script>', page, re.S
        )
        if not match:
            problems.append(f"{cat['page']}: no per-page rows block")
            continue
        try:
            block = json.loads(match.group(1))
        except ValueError as error:
            problems.append(f"{cat['page']}: rows block is not JSON ({error})")
            continue
        if block.get("slug") != cat["slug"]:
            problems.append(
                f"{cat['page']}: rows block names {block.get('slug')!r}, not {cat['slug']!r}"
            )
        rows = block.get("rows")
        if not isinstance(rows, dict):
            problems.append(f"{cat['page']}: rows block has no row map")
            continue
        want = {row["id"] for row in cat["rows"]}
        extra = sorted(set(rows) - want)
        missing = sorted(want - set(rows))
        if extra:
            problems.append(
                f"{cat['page']}: rows block carries rows from another category: {', '.join(extra)}"
            )
        if missing:
            problems.append(
                f"{cat['page']}: rows block is missing {', '.join(missing)}"
            )
        if not isinstance(block.get("cat"), dict):
            problems.append(f"{cat['page']}: rows block has no category words")
    return problems


def policy_problems(pages):
    """The page's policy is the one the markup obeys.

    Every inline script is hashed in the policy, no inline handler is left for
    the policy to block, and script-src allows no inline script at all. The
    build writes the hashes from the same strings it emits, so this is the check
    that a hand-added inline script cannot land ahead of the policy.
    """
    problems = []
    for cat in CATEGORIES:
        page = pages[cat["page"]]
        meta = re.search(
            r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', page
        )
        if not meta:
            problems.append(f"{cat['page']}: no Content-Security-Policy")
            continue
        policy = meta.group(1)
        directive = re.search(r"script-src([^;]*)", policy)
        if not directive:
            problems.append(f"{cat['page']}: the policy says nothing about script-src")
        elif "unsafe-inline" in directive.group(1):
            problems.append(f"{cat['page']}: script-src allows inline script")
        if "default-src 'self'" not in policy:
            problems.append(f"{cat['page']}: the policy has no default-src 'self'")
        hashes = set(re.findall(r"'sha256-([A-Za-z0-9+/=]+)'", policy))
        for body in re.findall(r"<script>([^<]*)</script>", page):
            digest = base64.b64encode(
                hashlib.sha256(body.encode("utf-8")).digest()
            ).decode()
            if digest not in hashes:
                problems.append(
                    f"{cat['page']}: an inline script is not one of the policy's hashes"
                )
        if re.search(r"\son[a-z]+=", page):
            problems.append(
                f"{cat['page']}: an inline event handler would be blocked by the policy"
            )
    return problems


ESCAPED = ("&amp;", "&lt;", "&gt;", "&quot;", "&#39;")


def escaping_problems(pages):
    """Every character that can end an attribute is escaped.

    `esc()` writes into double-quoted attributes in the comparison, so a model
    name with a quote in it (`5" screen`) would end the attribute and put the
    rest of the name into markup. The function escapes all five; this check
    fails if one of them is dropped again.
    """
    path = os.path.join(ROOT, "assets", "page.js")
    if not os.path.exists(path):
        return ["assets/page.js is missing"]
    js = open(path, encoding="utf-8").read()
    if not re.search(r"function esc\(s\)\{", js):
        return ["assets/page.js has no esc() to read"]
    missing = [code for code in ESCAPED if code not in js]
    if missing:
        return [f"esc() does not escape {', '.join(missing)}"]
    return []


def transfer_problems():
    """What each page's own first visit weighs over the wire."""
    problems = []
    shared = 0
    for name, budget in TRANSFER_BUDGET.items():
        raw = open(os.path.join(ROOT, name), "rb").read()
        size = len(gzip.compress(raw, 9))
        shared += size
        if size > budget:
            problems.append(
                f"{name} is {size:,} bytes gzipped, over its {budget:,}-byte budget"
            )
    pages = {}
    for cat in CATEGORIES:
        raw = open(os.path.join(ROOT, cat["page"]), "rb").read()
        size = len(gzip.compress(raw, 9))
        pages[cat["page"]] = size
        if size > PAGE_BUDGET:
            problems.append(
                f"{cat['page']} is {size:,} bytes gzipped, over its {PAGE_BUDGET:,}-byte budget"
            )
    biggest = max(pages, key=pages.get) if pages else "none"
    total = shared + (pages[biggest] if pages else 0)
    if total > TRANSFER_TOTAL:
        problems.append(
            f"{biggest} first visit is {total:,} bytes gzipped, over the {TRANSFER_TOTAL:,}-byte budget"
        )
    return problems, pages, shared


def freshness_problems():
    """Each category's own check date, so a new page cannot borrow an old one's."""
    problems, notes = [], []
    for cat in CATEGORIES:
        day = date.fromisoformat(cat["checked_iso"])
        age = (date.today() - day).days
        if age < 0:
            problems.append(
                f"{cat['slug']}: checked_iso {cat['checked_iso']} is {-age} days in the future"
            )
        elif age > 60:
            problems.append(
                f"{cat['slug']}: the data was last checked {age} days ago (limit 60); "
                "re-check it and move checked_iso"
            )
        elif age > 30:
            notes.append(
                f"{cat['slug']}: the data was last checked {age} days ago; re-check it soon"
            )
    return problems, notes


def derived_figures(ctx):
    if ctx.module is None:
        raise Skip("the dataset did not load")
    return data_problems(ctx.module, ctx.pages)


def slider(ctx):
    if ctx.module is None:
        raise Skip("the dataset did not load")
    return slider_problems(ctx.module, ctx.pages)


def offer_rule_problems(module):
    """The routing rule on fixtures, so the promise the page prints is the rule.

    A shop that pays us more may add at most the window to a price, and one
    further away than that never wins however well it pays. The reader is told
    both halves, so both are checked: the cheapest offer, then the better payer
    inside the window, then the cheaper offer and the shop's name on a tie.
    """
    if not hasattr(module, "offer_winner"):
        return ["rows.py has no offer_winner, so no offer can be chosen"]
    C, R, A, B = 100.0, module.PAY_RETAIL, module.PAY_AMAZON, module.PAY_BRAND

    def offer(shop, price, pay):
        return dict(shop=shop, src=shop.lower(), price=price, pay=pay, note="one size")

    cases = [
        ([offer("Cheap", C, R), offer("Dear", C + 20, B)], C,
         "a shop £20 dearer won on pay"),
        ([offer("Cheap", C, R), offer("Near", C + 5, B)], C + 5,
         "a shop exactly £5 dearer did not win on pay"),
        ([offer("Cheap", C, R), offer("Far", C + 5.01, B)], C,
         "a shop £5.01 dearer won on pay"),
        ([offer("Amazon", C, A), offer("Brand", C, B)], C,
         "an equal price did not go to the better payer"),
        ([offer("Alpha", C, A), offer("Beta", C, A), offer("Gamma", C + 20, B)], C,
         "a tie fell to something other than the name"),
        ([offer("Only", C + 40, B)], C + 40,
         "a row with one offer did not show it"),
    ]
    problems = []
    for offers, want, why in cases:
        got = module.offer_winner(offers)["price"]
        if got != want:
            problems.append(f"{why}: picked £{got:,.2f} instead of £{want:,.2f}")
    if module.offer_winner([offer("Alpha", C, A), offer("Beta", C, A)])["shop"] != "Alpha":
        problems.append("a full tie is not settled by the shop's name")
    return problems


def offer_rule(ctx):
    if ctx.module is None:
        raise Skip("the dataset did not load")
    return offer_rule_problems(ctx.module)


def paid_link_problems(module):
    """Every price that links to a paying shop says so, and the networks agree.

    The regression this encodes is real: `rel` used to be decided by matching
    `tag=` and `amazon.co.uk` against the URL, so the first Awin click would
    have shipped as an ordinary `nofollow` link. A price link now has to be in
    the set built where the tagging happens, and the Awin helper has to produce
    the shape Awin documents.
    """
    problems = []
    for cat in CATEGORIES:
        for row in cat["rows"]:
            keys = [row["price_src"]] + [o["src"] for o in row.get("offers", ())]
            for key in keys:
                url = module.S[key][1]
                if "amazon.co.uk" not in url:
                    continue
                if "tag=" not in url:
                    problems.append(
                        f"{row['id']}: the price links to Amazon without our tag"
                    )
                elif url not in module.SPONSORED:
                    problems.append(
                        f"{row['id']}: an Amazon price link is not marked as paid"
                    )
    if module.awin_tagged("https://example.com/p", 69428) != (
        "https://www.awin1.com/cread.php?awinmid=69428&awinaffid=3141383"
        "&ued=https%3A%2F%2Fexample.com%2Fp"
    ):
        problems.append(
            "the Awin deep link is not the documented shape: "
            + module.awin_tagged("https://example.com/p", 69428)
        )
    return problems


def paid_links(ctx):
    if ctx.module is None:
        raise Skip("the dataset did not load")
    return paid_link_problems(ctx.module)


def lineup_photo_problems(meta):
    """A row called a brand's current model is a model the vendor still shows.

    The photo is the trace left behind when it stops. `make_images.py` records a
    placeholder only where the vendor's own site has no image of the model, and
    a model still on sale always has one: Blink's devices page kept a card for
    the Outdoor 2K+ after dropping the Outdoor 4, and the placeholder on the row
    named as current was the only warning, read past at the price check.
    """
    problems = []
    for cat in CATEGORIES:
        for brand, entry in (cat.get("lineup") or {}).get("current", {}).items():
            if not isinstance(entry, Current):
                continue
            named = entry.row_id
            photo = meta.get(named) or {}
            if not photo or photo.get("placeholder"):
                problems.append(
                    f"{cat['slug']}: {brand}'s current model {named} has no photo of "
                    "its own, so its vendor's site no longer shows it, or "
                    "make_images.py has not been run since the row was added; read "
                    "the brand's devices page for the model that replaced it"
                )
    return problems


def lineup_photo(ctx):
    path = os.path.join(ROOT, "build", "images.json")
    with open(path, encoding="utf-8") as handle:
        return lineup_photo_problems(json.load(handle))


def transfer(ctx):
    problems, pages, shared = transfer_problems()
    ctx.note(
        "first visits, page data + shared CSS/JS: "
        + ", ".join(f"{name} {size + shared:,}" for name, size in pages.items())
    )
    return problems


def freshness(ctx):
    if ctx.module is None:
        raise Skip("the dataset did not load")
    problems, notes = freshness_problems()
    for note in notes:
        ctx.note(note)
    return problems


def note_pending(ctx):
    for cat in CATEGORIES:
        path = os.path.join(ROOT, cat["csv"])
        with open(path, newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        pending = [row for row in rows if row["Unverified / re-check"].strip()]
        ctx.note(f"{len(pending)} of {len(rows)} {cat['nouns']} still carry an unverified note")
        for row in pending:
            why = row["Unverified / re-check"].replace("\u00a3", "GBP ")
            ctx.note(f"{row['Brand']} {row['Model']}: {why}")


def type_problems():
    """The build's Python modules under the project's mypy baseline."""
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "build", "--ignore-missing-imports", "--no-error-summary"],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    if result.returncode == 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()] or [
        result.stderr.strip() or "mypy failed without a message"
    ]


def row_model_problems():
    """The parse boundary names a bad row and a bad lineup by field and brand."""
    from model import Row, parse_lineup

    problems = []
    raw = (CATEGORIES[0].get("raw_rows") or [{}])[0]
    raw.pop("price", None)
    try:
        Row.from_raw(raw)
    except KeyError as error:
        if "price" not in str(error):
            problems.append(f"a row missing price failed on {error}, not price")
    else:
        problems.append("a row missing price parsed without an error")

    _, lineup_problems = parse_lineup(
        {"slug": "fixture", "current": {"Brand": None}, "previous": {}}, {}
    )
    if not any("Brand" in problem for problem in lineup_problems):
        problems.append("a malformed current lineup did not name its brand")
    return problems


CHECKS = [
    Check(
        "rebuild", "static", 0, "rebuild reproduces the committed pages",
        lambda ctx: ctx.rebuild_problems,
    ),
    Check(
        "dataset", "static", 1, "the dataset loads and every row has the keys it needs",
        lambda ctx: ctx.dataset_problems,
    ),
    Check(
        "derived figures", "static", 2,
        "every derived figure recomputes, every source resolves, every open fact names its blocker",
        derived_figures,
    ),
    Check(
        "data freshness", "static", 3,
        "every category's prices are dated and inside their 60-day limit",
        freshness,
    ),
    Check(
        "offer rule", "static", 21,
        "the cheapest offer wins, and a better payer only inside the £5 window",
        offer_rule,
    ),
    Check(
        "paid links", "static", 26,
        "every price that links to a paying shop carries our tag and says it is paid",
        paid_links,
    ),
    Check(
        "lineup photo", "static", 96,
        "a brand's current model is one its vendor still shows, not a row carrying a placeholder photo",
        lineup_photo,
    ),
    Check(
        "price range", "static", 7,
        "the price slider's floor and ceiling come from the data and reach every price",
        slider,
    ),
    Check(
        "attribute escaping", "static", 8,
        "every character that can end a quoted attribute is escaped",
        lambda ctx: escaping_problems(ctx.pages),
    ),
    Check(
        "transfer budget", "static", 9,
        "each page, its CSS and its script stay inside their gzipped byte budgets",
        transfer,
    ),
    Check(
        "page data", "static", 27,
        "every page ships only its own rows, in the JSON block its script reads",
        lambda ctx: page_data_problems(ctx.pages),
    ),
    Check(
        "content policy", "static", 6,
        "the page's Content-Security-Policy hashes its own inline scripts and leaves no inline handler",
        lambda ctx: policy_problems(ctx.pages),
    ),
    Check(
        "types", "static", 99,
        "every build module type-checks under the project's mypy baseline",
        lambda ctx: type_problems(),
    ),
    Check(
        "row model", "static", 100,
        "a malformed row and a malformed lineup fail by field and by brand",
        lambda ctx: row_model_problems(),
    ),
]
