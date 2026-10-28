"""The dataset behind the page: it loads, its figures recompute, and every open fact names its blocker."""
from datetime import date
import base64
import csv
import gzip
import hashlib
import os
import re
import sys

from catalog import CATEGORIES
from .context import ROOT
from .registry import Check, Skip


BLOCKER_CUES = (
    "app", "support", "docs", "page", "terms", "datasheet", "retailer",
    "listing", "pdf", "faq", "manual", "release notes",
)

WEAK_UNVERIFIED = {"not confirmed", "unknown", "tbc", "pending", "not yet verified"}

# What the three files a first visit reads may weigh, gzipped. The budget is in
# docs/performance-budget.md; each line has headroom over today's figure, and a
# change that doubles the page cannot pass by being a little over.
TRANSFER_BUDGET = {
    "index.html": 24_000,
    "assets/page.css": 18_000,
    "assets/page.js": 24_000,
}
TRANSFER_TOTAL = 60_000


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
        wanted = {
            "Brand": row["brand"],
            "Model": row["model"],
            "UK price (£)": f"{price:.2f}",
            f"Free-feature score (/{cat['score_max']})": str(sum(row["score"].values())),
            "3-yr cost without subscription (£)": f"{nosub3:.2f}",
            "3-yr cost with cheapest plan, monthly (£)": "" if sub3 is None else f"{sub3:.2f}",
            "Cheapest 3-yr cost to keep recordings (£)": "" if keep3 is None else f"{keep3:.2f}",
            "Plan price region": row["plan_region"],
            "Last checked": rows.CHECKED,
        }
        for key, value in wanted.items():
            if out.get(key) != value:
                problems.append(
                    f"{row['id']}: CSV {key} is {out.get(key)!r}, recomputed {value!r}"
                )
        if (row["keep3"], row["nosub3"], row["sub3"]) != (keep3, nosub3, sub3):
            problems.append(f"{row['id']}: a derived figure drifted from price, extra and plan")
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
    for name, text in ((cat["page"], index), (cat["md"], markdown)):
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
    """What the three files a first visit reads weigh over the wire."""
    problems = []
    total = 0
    for name, budget in TRANSFER_BUDGET.items():
        raw = open(os.path.join(ROOT, name), "rb").read()
        size = len(gzip.compress(raw, 9))
        total += size
        if size > budget:
            problems.append(
                f"{name} is {size:,} bytes gzipped, over its {budget:,}-byte budget"
            )
    if total > TRANSFER_TOTAL:
        problems.append(
            f"a first visit is {total:,} bytes gzipped, over the {TRANSFER_TOTAL:,}-byte budget"
        )
    return problems, total


def freshness_problems(rows):
    age = (date.today() - rows._CHECKED_DATE).days
    if age < 0:
        return [f"CHECKED_ISO {rows.CHECKED_ISO} is {-age} days in the future"], None
    if age > 60:
        return (
            [f"the data was last checked {age} days ago (limit 60); re-check it and move CHECKED_ISO"],
            None,
        )
    if age > 30:
        return [], f"the data was last checked {age} days ago; re-check it soon"
    return [], None


def derived_figures(ctx):
    if ctx.dataset is None:
        raise Skip("the dataset did not load")
    return data_problems(ctx.dataset, ctx.pages)


def slider(ctx):
    if ctx.dataset is None:
        raise Skip("the dataset did not load")
    return slider_problems(ctx.dataset, ctx.pages)


def transfer(ctx):
    problems, total = transfer_problems()
    ctx.note(f"a first visit is {total:,} bytes gzipped across the page, its CSS and its script")
    return problems


def freshness(ctx):
    if ctx.dataset is None:
        raise Skip("the dataset did not load")
    problems, note = freshness_problems(ctx.dataset)
    if note:
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
        lambda ctx: f"the data is dated {ctx.checked} and is inside its 60-day limit",
        freshness,
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
        "the page, its CSS and its script stay inside their gzipped byte budgets",
        transfer,
    ),
    Check(
        "content policy", "static", 6,
        "the page's Content-Security-Policy hashes its own inline scripts and leaves no inline handler",
        lambda ctx: policy_problems(ctx.pages),
    ),
]
