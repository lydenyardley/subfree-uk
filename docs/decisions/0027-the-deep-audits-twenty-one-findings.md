# 27. The deep audit's twenty-one findings

- Status: Accepted
- Date: 28 October 2026
- Source: the owner's request of 28 October 2026 — implement R1 to R21 of the
  deep audit, keep what is durable, delete the audit, review the result and
  commit it; and the goal stated with it, that another category or product can
  be brought online without reworking the build.

The audit itself is gone. This records what was decided, so the reasons survive
it, and where the rule now lives in code rather than in a document.

## The build can render a category, not just this page

**R18.** `build/catalog.py` holds `CATEGORIES`, one record per category: its
slug and route, its output filenames, its nouns, its title, description, `h1`,
dek, masthead and skip link, the period's written forms, the row keys it needs,
its facets, its power and record vocabularies, its score parts, its verdict
vocabulary, the claims a figure can carry, the comparison's rows and pinned
count, the sort options, the method copy and the CSV and markdown headers.
`build.build(cat)` renders one record and `write()` loops over them, so the page
is a function of the record.

What used to be keyed by product id is now the row's own: `VERDICT` and `PLAIN`
are authored beside the rows in `rows.py` and attached to them as `verdict` and
`plain`, so a product is written in one file and `build.py` knows no product.
`row_problems()` validates a row against its category: an unknown key, a
missing facet, a `rec` or `power` outside the vocabulary, a score part outside
its maximum, an `ha` outside 0 to 2 and a verdict outside the record's
vocabulary all fail by name.

**R19.** A category's facets are the record's, so a camera category declares
its own decisions instead of borrowing a doorbell's. `build/checks/category.py`
keeps expansion honest with two checks. `category records` renders every record
and reads it back: the copy's count is the count of rows, the headline verdict
is one a row carries, the output files are the category's own, and every asset
link resolves from that category's route — which is the rule that makes a page
at `/cameras/` work without a second stylesheet. `category words` reads each
page for another category's nouns, which is what a copy-pasted page looks like
when the second one lands.

**R20.** The checks choose their fixtures from the data by property, not by
product id, and the comparison's pinned rows are the record's list of keys
rather than the first four of its rows — which is how the two cost rows stayed
pinned when the free-feature row moved into the record's comparison list.
The kit price a method note prints is authored in `kit_price` and checked
against the row's `extra`, because a figure recovered by subtraction is a
figure with a second way to be wrong. Fixtures: `shortlist()` (one row that records nothing without a plan, one with
nothing to buy, one that records for a fee), `family()` (the busiest brand's
three, for the view that hides identical rows), `cheapest()`, and `lead_ids()`
(the rows the category's own short answer links to). The comparison's row count
is the record's, the table and skip-link names are the record's, and the
expected marks are computed from the rows the comparison shows. A fifteenth row
no longer needs a check edited, and the check that used to assert "14" now
asserts the count against the data it came from.

**R21.** The route shape is decided in the record. `route` is `""` for a page at
the site root and `"cameras/"` for one below it; asset links are emitted with
one `../` per directory and `category records` resolves them, so a nested page
cannot ask for an asset that is not there. The 404 page links every category
from the site root. Each category is a page, and each page keeps one `h1`.

## The guard rails, in the order they bite

**R1.** A row with no free recording and no plan has no 3-year total, so
`keep3` is `None` and `row_problems()` rejects the row in words: "no route keeps
recordings (free_records is false and sub is None)". The build used to raise
`ValueError: min() iterable argument is empty` from inside a module-level loop,
naming nothing.

**R2.** `score_total` is still a sum, but the score is now checked part by part
against the record's maxima, and `rec`, `power` and `ha` against their
vocabularies. A typo fails by name instead of raising a `KeyError` in the CSV
writer or printing "9/8" on the page.

**R3.** The price slider's floor is the data's: `MINP = int(min(price) // 10 *
10)`, and `MAXP` follows the dearest row. The room below the cheapest product
used to be a typed-in £40 with a comment; the first product under it vanished
from the default view of the page it was added to. A static check now proves
every price sits inside the range the page renders.

**R4.** A euro plan price in a pound order is disclosed in the sort note, where
the order is named: "One plan price is in euros." The note is only shown when a
visible row is EU and the sort mixes currencies, and the sentence is short
enough to cost no extra line on a phone.

**R5.** The social preview is the row the page recommends: the first row with
the record's headline verdict and a real photo, and its name for the alt text.
A renamed or removed row can no longer leave the page claiming a picture it no
longer shows.

**R6.** The theme button carries both names and the stylesheet shows the one the
theme needs, so a page that is already dark offers "Light mode" in its first
frame, before any script runs.

**R7.** The markdown export escapes a pipe and collapses a newline in every
free-text cell. A sentence with a `|` in it used to add a column to that row and
shift every cell after it, while the build still reported success.

**R8.** The byte budget is a check: the page, its CSS and its script are
measured gzipped against fixed ceilings, and each has headroom over today's
figure. `docs/performance-budget.md` carries the numbers. The comparison's data
stays in the script: a JSON block would be the same bytes on the wire, one more
parse, and one more place for the two copies to disagree, so the budget is what
holds the duplication down.

**R9.** The compare cue's scroll handler runs through `requestAnimationFrame`
and writes nothing when its answer has not changed. It read four rectangles per
event and wrote between them.

**R10.** `esc()` escapes `&`, `<`, `>`, `"` and `'`. It writes into
double-quoted attributes in the comparison, so a model name with a quote in it —
a 5" screen — used to end the attribute and put the rest of the name into
markup. A static check fails if a character drops out of the function again.

**R11.** The page carries a Content Security Policy in a meta tag: no
third-party script, no inline script except the two that are hashed at build
time, no form action, no object, no plugins. The inline `onsubmit` handler moved
into the script, because a policy that blocks inline handlers would have blocked
it. `style-src` allows inline styles, which the pages use for the fill bar, the
score bars and the card's position.

**R12.** Every URL in `S` must be https, checked once over the whole register.
The escaping on the way out keeps the markup intact; it does not keep the scheme
honest, and a `javascript:` URL pasted into a source would have shipped as a
working link.

**R13.** The audit's own dependencies are pinned to the versions the checks were
run with, and the workflow actions are pinned by commit with their tag in a
comment. A release of axe or a moved tag can no longer change what "the checks
passed" means without a commit here.

**R14.** The two price handles are one named group: a `fieldset` with the legend
"Price", each handle carrying an `aria-valuetext` of pounds that `apply()`
updates, and both described by the two outputs. A screen reader used to hear
"Lowest price, 40".

**R15.** The tray is a named region, and the back-to-top button sits in one.
Both are outside `<main>`, so a landmark user could not jump to either. The axe
pass now includes one run with a model ticked and the page scrolled, which is
the only state in which those two controls are on screen.

**R16.** Closing a source card hands focus back to the figure it opened from,
unless the filters have hidden that row since — then it goes to the control the
reader last changed, or Reset. It used to fall to `<body>`, which sends the next
Tab to the top of the document.

**R17.** 320px is in the width list the layout and overflow checks measure.
WCAG 2.2 asks for a 320 CSS pixel reflow; the page did not overflow there, but
nothing would have caught it if it had.

## Consequences

- The page weighs 53,848 bytes gzipped on a first visit (18,868 + 15,298 +
  19,682), and the budget fails at 60,000 or at any of the three per-file
  ceilings.
- `build/check.py` is 88 checks. The new ones are `price range`, `attribute
  escaping`, `transfer budget`, `content policy`, `category records` and
  `category words`, and `axe WCAG` gained a page state.
- `build/catalog.py` is the file to read before adding a category, and
  `AGENTS.md` carries the steps. `build/rows.py` is still where a product is
  written: its row, its verdict and its plain sentences.
- Nothing here re-prices a product or moves `CHECKED_ISO`. The figures and the
  day they were checked are still 19 October 2026 for the doorbells and 26
  October 2026 for the two sundries, as ADR 26 records.
