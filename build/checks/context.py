"""What every check is given, and the figures the page is measured against.

A check asks for `phone`, `snapshot` or `lightbox` and the measurement is taken
once, by the first check that needs it, at the point in the run where the
sequential audit used to take it. Nothing here writes a file.

The fixtures are chosen from the dataset by the property a check needs, not by
product id, so adding a product cannot break a check that is not about it, and
no count is typed in that a fifteenth row would turn into a weaker test.
"""
import os

from catalog import CATEGORIES
from .js import AUDIT_JS, COST_JS, HEADER_JS, PHONE_JS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAGES = [cat["page"] for cat in CATEGORIES] + [cat["alias"] for cat in CATEGORIES]
GENERATED = PAGES + [
    cat[name] for cat in CATEGORIES for name in ("csv", "md")
] + [
    "assets/page.css",
    "assets/page.js",
    "404.html",
]
WIDTHS = [1440, 1280, 1100, 1000, 900, 820, 390, 320]
AXE_WIDTHS = [1280, 820, 390]
WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
BEST_PRACTICE_TAG = "best-practice"


def pick(rows, predicate, chosen):
    """The first row that fits, if it is not already in the fixture."""
    for row in rows:
        if row["id"] not in chosen and predicate(row):
            return row["id"]
    return None


def shortlist(rows):
    """Three rows that between them carry the decision the comparison draws out.

    One that records nothing without a plan, one with nothing to buy, and one
    that records free for a fee, so the comparison always has a marked "None"
    and an unmarked one to tell apart. Filled from the cheapest rows if the
    dataset is too thin for all three.
    """
    chosen = []
    for predicate in (
        lambda r: r["rec"] == "no" and r["sub"] is not None,
        lambda r: r["sub"] is None,
        lambda r: r["free_records"] and r["sub"] is not None,
    ):
        found = pick(rows, predicate, chosen)
        if found:
            chosen.append(found)
    for row in sorted(rows, key=lambda r: (r["keep3"] is None, r["keep3"] or 0)):
        if len(chosen) >= 3:
            break
        if row["id"] not in chosen:
            chosen.append(row["id"])
    return tuple(chosen[:3])


def family(rows):
    """Three rows of one brand, for the view that hides identical rows.

    The brand with the most rows is the one whose models have anything in
    common to hide, so it is the busiest brand's three rather than a named one.
    """
    counts = {}
    for row in rows:
        counts.setdefault(row["brand"], []).append(row["id"])
    brand = max(counts, key=lambda name: len(counts[name]))
    return tuple(counts[brand][:3])


def cheapest(rows, count=3):
    """The cheapest rows, for the checks that only need a comparison to open."""
    ordered = sorted(rows, key=lambda r: (r["keep3"] is None, r["keep3"] or 0))
    return tuple(row["id"] for row in ordered[:count])


def open_compare(page, ids=None):
    """Open every detail row and the comparison for three datasets rows."""
    ids = list(ids or THREE)
    page.eval_on_selector_all(
        "button.more",
        "els => els.forEach(el => { if (el.getAttribute('aria-expanded') !== 'true') el.click() })",
    )
    page.evaluate(
        """(ids) => {
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }""",
        ids,
    )
    page.wait_for_timeout(250)
    if page.evaluate("() => document.getElementById('compare').hidden"):
        page.click("#tray-go")
        page.wait_for_timeout(350)


# The default trio is read from the dataset at import, so the checks below can
# name a fixture before any of them has run.
def _from_dataset():
    import rows as module

    return shortlist(module.ROWS), family(module.ROWS), cheapest(module.ROWS)


try:
    THREE, FAMILY, CHEAPEST = _from_dataset()
except Exception:                    # the dataset itself is the failure to report
    THREE, FAMILY, CHEAPEST = (), (), ()


class Context:
    """The page under test, the data behind it, and what this run has measured."""

    def __init__(self, audit, dataset, dataset_problems, pages, external=False):
        self.audit = audit
        self.dataset = dataset
        self.dataset_problems = dataset_problems
        self.pages = pages
        self.external = external
        self.rebuild_problems = []
        self.console_errors = []
        self.page = None
        self.browser = None
        self.playwright = None
        self.url = None
        self._phone = None
        self._snapshot = None
        self._lightbox = None
        self._compare = False

    @property
    def rows(self):
        return self.dataset.ROWS if self.dataset else []

    @property
    def row_count(self):
        """The rows the page should render, read from the data it was built from."""
        return len(self.rows)

    @property
    def source_count(self):
        return len(self.dataset.FN) if self.dataset else 0

    @property
    def checked(self):
        return self.dataset.CHECKED if self.dataset else None

    @property
    def three(self):
        return self.dataset and shortlist(self.rows) or ()

    @property
    def family(self):
        return self.dataset and family(self.rows) or ()

    @property
    def cheapest(self):
        return self.dataset and cheapest(self.rows) or ()

    def note(self, text):
        self.audit.note(text)

    @property
    def phone(self):
        screen = self.page
        if self._phone is None:
            self._phone = {
                "first paint": screen.evaluate(PHONE_JS),
                "cost": screen.evaluate(COST_JS),
                "page": screen.evaluate(AUDIT_JS),
                "header": screen.evaluate(HEADER_JS),
                "roles": "columnheader" in screen.locator("#tbl").aria_snapshot(),
            }
        return self._phone

    @property
    def snapshot(self):
        if self._snapshot is None:
            self._snapshot = self.page.evaluate(AUDIT_JS)
        return self._snapshot

    @property
    def lightbox(self):
        if self._lightbox is None:
            from .behaviour import lightbox_check

            self._lightbox = lightbox_check(self.page)
        return self._lightbox

    def ensure_compare(self):
        """Open the comparison once, however many checks ask for it."""
        if not self._compare:
            open_compare(self.page, self.three)
            self._compare = True
