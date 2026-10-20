# Full audit, 20 October 2026

Read-only. Nothing here is implemented; each recommendation says what it would
change and what would prove it.

## Method

Measured on the built site (`python build/build.py` output, 14 rows) served on
loopback and driven with Playwright's Chromium 156, at 390px and 1280px unless
stated. Machine: a Windows desktop also running cloud-drive, a torrent client
and an editor, which matters for the timings below and is why the performance
checks in `build/check.py` gate ratios as well as absolutes.

What was run:

- `python build/check.py`: 64 passes, exit 0, on the committed tree.
- `python build/check.py --external`: 60 of the 67 external links requested,
  all reachable on this date.
- Data recomputation from `ROWS`: price + kit, price + 36 × plan, score sums,
  source keys, and the CSV.
- Fresh-page vitals at 390 and 1280 (LCP, CLS, requests, transfer), 320px and
  360px reflow, 125% root text, find-in-page against contained rows, the
  comparison panel by keyboard at 390, and the table's roles in the
  accessibility tree.
- Reading `build/build.py` (1,148 lines, 7 functions) and `build/check.py`
  (2,498 lines, 33 functions) end to end.

Not tested: a real screen reader, Firefox, Safari, a phone, and a host with
caching or compression. Every a11y statement here is browser-level.

## Scorecard

| Dimension | State | Evidence |
|---|---|---|
| Data correctness | Strong | Every derived figure matches a recomputation; no unknown source keys |
| Sourcing | Good, with a known gap | 52 sources, 2 rows still open, each naming its blocker |
| Accessibility | Strong at the DOM level | axe clean at 3 widths × 2 themes; roles survive the grid layout |
| Performance | Strong | 5 requests and 6KB at 390; LCP 152 to 332ms; CLS 0 |
| Verification | Weak outside one command | No CI job runs the audit; 33 check functions in one 2,498-line file |
| Architecture | Workable, with one sharp edge | Page CSS and JS live inside a Python f-string |
| Content freshness | Two open facts | 2 of 14 plan figures are EU prices; the check date is a hand-typed string |
| Design | Settled | Phone-first answer above the fold; desktop table aligns to the pixel |

## 1. Data correctness

**Measured.** `keep3`, `sub3`, `nosub3`, `score_total` and `keep3 = min(free,
plan)` all recompute exactly from `price`, `extra`, `sub` and `score`. All 52
source keys used by rows exist in `S`, no row has an empty `src`, and the CSV
matches the page's 14 rows. Score totals run 2 to 7 out of 8, and every part is
within its declared maximum.

**Finding 1.1 (P2). The arithmetic has no test.** `check.py` never recomputes a
figure; it audits the page's structure and behaviour. Changing `min` to
`max`, or dropping the £10 card from `nosub3`, would ship a wrong headline
number and still pass the other 63 checks. *Recommendation:* add a `data_check` that
imports `ROWS`, recomputes the four derived figures and fails on any difference
from the CSV, then asserts every `src` key resolves and every `unverified`
sentence names its blocker.

**Finding 1.2 (P1). The check date is a literal.** `CHECKED = "19 October
2026"` is typed by hand and printed twice on the page as "Last checked", and
again in the shortlist copy.
Nothing fails when prices age: the page can claim a date months old while the
budget and ADRs say the data was verified. *Recommendation:* move the date to
the dataset, refuse to build if it is in the future, and make the check warn
after 30 days and fail after 60.

**Finding 1.3 (P3). One card price for every device.** `CARD = 10.00` is a
single assumption applied to every row that needs microSD or USB. It is
disclosed ("that last figure isn't from a cited source"), and it moves no
ranking by more than a few pounds, but a device that needs two cards (doorbell
plus chime) is charged for one. *Recommendation:* leave the figure, and add
`cards` to the row if a product needs more than one.

## 2. Sourcing

**Measured.** 14 rows, 52 sources, 3 to 9 sources per row (median 4), 13
distinct price sources for 14 rows. Two rows carry an unverified note, both
EZVIZ, both naming the same blocker: CloudPlay shows UK pricing only inside its
app, so the £4.99 in the plan column is the published EU price. That is the
form AGENTS.md asks for. The method paragraph discloses it too.

**Finding 2.1 (P2). Sources are per row, not per claim.** The price has its own
key (`price_src`) and its own link, but "Records free?", "Storage", "Live view"
and "Home Assistant" all rely on the row's undifferentiated list. A reader
checking "cloud optional" has four to nine links and no way to know which one
supports it. *Recommendation:* give the four decision fields their own source
keys, the way price already has one. Start with the fields where a wrong claim
costs money: `rec`, `history`, `ha`.

**Finding 2.2 (P1). Two of fourteen plan figures are not UK prices.** They are
labelled as EU prices in the row, the method and the CSV, so nothing is
misrepresented, but "3 years, with plan" cannot be compared like for like
across the table. `keep3` is unaffected, because both EZVIZ models record free.
*Recommendation:* close the two facts from the app or EZVIZ support, or add a
`plan_price_region` field so the comparison can mark the row instead of relying
on a footnote sentence.

**Finding 2.3 (P3). Nothing enforces "name the blocker".** AGENTS.md's rule is
prose. A future row could ship "Not confirmed" and pass. *Recommendation:* a
check that every non-empty `unverified` matches a blocker phrase, or a
`blocker` field with a required value.

## 3. Accessibility

**Measured.** axe-core reports no WCAG 2.2 A or AA violations at 390, 820 and
1280px in both themes. After the desktop layout became grid tracks, the
accessibility tree still carries all 14 row headers and 8 column headers at
1280px, the same as the table did. Find-in-page finds and reveals a contained
row at 390, 900 and 1280px (`window.find('Hikvision')` scrolled to the row and
exposed it). One trap for future audits: CDP's `Accessibility.getFullAXTree`
reports only the rows that have been laid out (5 at 390px, all 14 at 1280px),
while Playwright's `aria_snapshot` reports the whole tree, so a CDP-only audit
will read containment as missing content.

320px and 360px have no horizontal overflow. The skip link is the first Tab
stop. Target sizes, the type floor, the live region and reduced motion are all
asserted by the check.

**Finding 3.1 (P2). The comparison table cannot be read by keyboard alone at
390px.** With three models the scroll container is 516px of content in 356px,
focusable at `tabIndex -1` and unnamed. Tabbing into the third column does
scroll it (scrollLeft 160 when a zoom button takes focus), but the text of that
column, which is most of the panel's meaning, has no focusable target, so a
keyboard user reads one vertical strip. Not a WCAG failure: a data table is
allowed two-dimensional layout for meaning. *Recommendation:* make the scroll
container focusable with a name ("Comparison, scrolls sideways"), or at 390px
show two models side by side with the third stacked beneath.

**Finding 3.2 (P3). One engine.** Every accessibility claim above is Chromium's.
Firefox and WebKit never run, and `content-visibility` plus `animation-timeline`
are exactly the features whose fallbacks differ there. *Recommendation:* add a
second Playwright project for Firefox to the existing check and run the
structural half against it.

**Finding 3.3 (P3). The header is hidden from the eye at 390px but present in
the tree.** That is deliberate and asserted, and it is the right call; note it
because a screen-reader user meets column names the visual reader does not.

## 4. Performance

**Measured.** At 390px: 5 requests, 6KB transferred, LCP 152 to 332ms, CLS 0,
1,294 DOM nodes, page 6,573px. At 1280px: 13 requests, 15KB, LCP 200 to 216ms,
CLS 0. The document is 123KB, of which 27.5KB is JavaScript in three inline
blocks and 25.4KB is one inline stylesheet. All 26 images total 121KB, every one
lazy. Sort and compare budgets are met at both widths (9.6 to 21ms at 1280,
9 to 15ms at 390, compare 84 to 150ms).

**Finding 4.1 (P2). The script is inline, so it is re-sent and uncacheable.**
27.5KB of JavaScript and 25.4KB of CSS sit inside the HTML. For a one-page site
with no router that is a reasonable trade, but it means every repeat visit
downloads them again and no cache header can help. *Recommendation:* emit
`build/page.css` and `build/page.js` as separate hashed files unless the host
proves excellent gzip on the HTML; measure with compression on before deciding.

**Finding 4.2 (P3). The same 123KB is committed twice.** `index.html` and
`doorbells.html` are byte-identical and the check asserts they stay identical.
The duplicate only earns its place if a host or a link depends on the second
name. *Recommendation:* keep one file and let the host rewrite, or make the
second a redirect, and note which name is canonical.

**Finding 4.3 (P3). The budget only exists locally.** `docs/performance-budget.md`
is enforced by a command nobody is required to run. *Recommendation:* the CI job
in 5.1 should run `build/check.py`, which already contains the budget gates.

## 5. Verification

**Measured.** `build/check.py` is 2,498 lines and 33 check functions, each returning a
list of problem strings, printing an `ok` line when empty. It rebuilds first and
fails on a stale generated file, drives one browser, and covers structure,
a11y, behaviour and performance. `build/check_commits.py` checks message format
and is the only thing CI runs.

**Finding 5.1 (P1). No CI job runs the audit.** `.github/workflows/commits.yml`
checks commit messages on pull requests and nothing else. A push that breaks
the phone layout, a contrast pair or the sort budget is green. *Recommendation:*
add a workflow that installs `build/requirements.txt`, installs Chromium, runs
`build/build.py`, fails on a dirty tree, and runs `build/check.py`. Budget 3
minutes with a cached Playwright browser.

**Finding 5.2 (P2). A failure means a two-minute run.** 33 checks share one page
and one script; there is no `--only`, no per-check timing, and a failure names
a string rather than a test. *Recommendation:* name each check, allow
`--only <name>`, and print the slowest three checks so the audit stays usable
as it grows.

**Finding 5.3 (P3). The audit's own assumptions are undocumented.** The check
depends on exact strings ("Only briefly (3 hrs)"), on 14 rows, on 52 footnotes
and on two unverified rows. A content change fails checks that read like
regressions. *Recommendation:* derive counts from `ROWS` in the check, and
assert the label map instead of the rendered count.

## 6. Architecture and code

**Measured.** `build/build.py` is the only source: 1,148 lines, 7 functions, the
dataset in `ROWS`, the page assembled in one f-string with `{{` escaping, and
the CSV plus markdown emitted from the same data. `build/check.py` is a
standalone driver. The page has no dependencies, no framework, no build step
beyond one Python file.

**Finding 6.1 (P2). The page's JavaScript and CSS are Python string literals.**
No editor parses them, no linter checks them, `node --check` cannot see them,
and a typo is caught only when the browser loads the page. That is a real,
working safety net (the check listens for `pageerror`), but it is a slow one.
*Recommendation:* keep `build/build.py` as the assembler and move the static
CSS and JS into `build/page.css` and `build/page.js`, inlined at build time. The
generated page stays identical; the sources become lintable.

**Finding 6.2 (P2). Rows are untyped dictionaries with 34 to 35 keys.** A missing
required key fails loudly at build time, which is good, but an optional one
(`unverified`, `power_note`) and a misspelt one read differently: one raises,
the other can render "None" or skip a sentence. *Recommendation:* a
`REQUIRED_ROW_KEYS` tuple asserted per row at the top of the build, or a
`TypedDict`. The first is five lines and catches the case that matters.

**Finding 6.3 (P3). Two money formatters.** `money()` prints `£1,234.50` and
`gbp()` prints the table's shorter style. Both are used in the same build.
*Recommendation:* one function with a `decimals` argument when the file is next
touched.

## 7. Content and design

**Measured.** At 390px the H1 sits at 73px, the short answer at 314px and the
filter panel at 372px, so the answer is above the fold and the table starts
below it. The longest "Best for" line is 72 characters and the longest catch is
98. The page ends in the method and a closing line with a way back to the table.
ADR 5 records the deliberate declines: no counted line, no shorter "Best for",
no hidden Home Assistant filter, no closing trade line, no plan-price slider.

**Finding 7.1 (P3). The compare panel at 390px is the one place the design asks
for horizontal scrolling.** It is disclosed by the cut-off third column and the
first column is sticky, so the pattern is legible; the keyboard gap is finding
3.1. *Recommendation:* no change unless 3.1 is fixed by stacking, in which case
two models side by side is the version to prototype.

**Finding 7.2 (P3). The page promises "no cookies" and ships a theme in
localStorage.** The claim is accurate (no cookies, no tracking) and `localStorage`
is not a cookie, but a reader may read the sentence as "stores nothing".
*Recommendation:* "no cookies, no tracking" is already the strongest true claim;
leave it, and keep the sentence in view when any storage is added.

## What to keep

- One generated page from one source, with the CSV and markdown derived from the
  same rows. Nothing in this audit wants a second source of truth.
- The decision records. ADR 4, 5 and 6 stop the page being redesigned around
  ideas already measured and declined.
- The check's habit of asserting the mechanism (containment removed fails at
  128.3ms, sticky header removed fails the scroll check), not just the outcome.
- The sourcing shape: every fact on the page traced to a row, and open facts
  stated in the row that carries them.

## Suggested order

1. 5.1, the CI job. It makes every other finding cheaper to fix and is the only
   P1 that protects the whole suite.
2. 1.1 and 1.2, the arithmetic check and the dated freshness guard. Both are
   small and they protect the page's main claim.
3. 2.2, close the two EU plan prices, or mark the region as data.
4. 3.1, the comparison panel at 390px.
5. 6.1 and 6.2, lintable page sources and a required-keys assertion.
6. 5.2, 3.2, 2.1 and 4.1 on the next pass; none of them is urgent.
