"""The dataset behind the page: it loads, its figures recompute, and every open fact names its blocker."""
from datetime import date
import csv
import os
import sys

from .context import ROOT
from .registry import Check, Skip


BLOCKER_CUES = (
    "app", "support", "docs", "page", "terms", "datasheet", "retailer",
    "listing", "pdf", "faq", "manual", "release notes",
)

WEAK_UNVERIFIED = {"not confirmed", "unknown", "tbc", "pending", "not yet verified"}

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
    problems = list(rows.row_problems()) + unverified_problems(rows.ROWS)
    with open(os.path.join(ROOT, "data", "doorbells.csv"), newline="", encoding="utf-8") as handle:
        shipped = list(csv.DictReader(handle))
    if len(shipped) != len(rows.ROWS):
        return problems + [f"the CSV has {len(shipped)} rows for {len(rows.ROWS)} in ROWS"]
    for row, out in zip(rows.ROWS, shipped):
        price, extra, sub = row["price"], row["extra"], row["sub"]
        nosub3 = round(price + extra, 2)
        sub3 = round(price + rows.MONTHS * sub, 2) if sub is not None else None
        options = ([] if not row["free_records"] else [nosub3]) + ([] if sub3 is None else [sub3])
        keep3 = min(options)
        wanted = {
            "Brand": row["brand"],
            "Model": row["model"],
            "UK price (£)": f"{price:.2f}",
            "Free-feature score (/8)": str(sum(row["score"].values())),
            "3-yr cost without subscription (£)": f"{nosub3:.2f}",
            "3-yr cost with cheapest plan, monthly (£)": "" if sub3 is None else f"{sub3:.2f}",
            "Cheapest 3-yr cost to keep recordings (£)": f"{keep3:.2f}",
            "Plan price region": row["plan_region"],
            "Last checked": rows.CHECKED,
        }
        for key, value in wanted.items():
            if out[key] != value:
                problems.append(f"{row['id']}: CSV {key} is {out[key]!r}, recomputed {value!r}")
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
    index = pages["index.html"]
    table_rows = index.count('<tbody class="item"')
    if table_rows != len(rows.ROWS):
        problems.append(f"the page has {table_rows} rows for {len(rows.ROWS)} in ROWS")
    eu = sum(1 for row in rows.ROWS if row["plan_region"] == "EU")
    if index.count('data-region="EU"') != eu:
        problems.append("the EU plan rows are not marked as data on the page")
    return problems

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


def freshness(ctx):
    if ctx.dataset is None:
        raise Skip("the dataset did not load")
    problems, note = freshness_problems(ctx.dataset)
    if note:
        ctx.note(note)
    return problems


def note_pending(ctx):
    path = os.path.join(ROOT, "data", "doorbells.csv")
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    pending = [row for row in rows if row["Unverified / re-check"].strip()]
    ctx.note(f"{len(pending)} of {len(rows)} rows still carry an unverified note")
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
]

