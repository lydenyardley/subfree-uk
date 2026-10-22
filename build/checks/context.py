"""What every check is given, and the figures the page is measured against.

A check asks for `phone`, `snapshot` or `lightbox` and the measurement is taken
once, by the first check that needs it, at the point in the run where the
sequential audit used to take it. Nothing here writes a file.
"""
import os

from .js import AUDIT_JS, COST_JS, HEADER_JS, PHONE_JS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAGES = ["index.html", "doorbells.html"]
GENERATED = PAGES + [
    "data/doorbells.csv",
    "data/doorbells.md",
    "assets/page.css",
    "assets/page.js",
    "404.html",
]
WIDTHS = [1440, 1280, 1100, 1000, 900, 820, 390]
AXE_WIDTHS = [1280, 820, 390]
WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
BEST_PRACTICE_TAG = "best-practice"
SHORTLIST_IDS = ("tapo-td21", "reo-poe", "ezviz-ep3x")


def open_compare(page, ids=SHORTLIST_IDS):
    """Open every detail row and the comparison for three known models."""
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
        list(ids),
    )
    page.wait_for_timeout(250)
    if page.evaluate("() => document.getElementById('compare').hidden"):
        page.click("#tray-go")
        page.wait_for_timeout(350)


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
        """The rows the page should render; the page's own count when the data did not load."""
        return len(self.rows) or 14

    @property
    def source_count(self):
        return len(self.dataset.FN) if self.dataset else 0

    @property
    def checked(self):
        return self.dataset.CHECKED if self.dataset else None

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
            open_compare(self.page)
            self._compare = True
