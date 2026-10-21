# 7. The audit's twenty findings

- Status: Accepted
- Date: 21 October 2026
- Source: `docs/audits/2026-10-20-full-audit.md`, now removed, items 1.1 to
  7.2. The measurements are in `docs/performance-budget.md` and in the checks
  named below.

## Context

The 20 October audit found the page correct and fast, and the process around it
weak. Nothing recomputed a price, the last-checked date was typed by hand, one
claim could lose its source without a check noticing, one plan column was not a
UK price, one panel could not be read by keyboard, the audit only ran locally,
and the page's CSS and JavaScript were Python string literals. This record
covers the twenty findings in one pass; the audit document is deleted because
each finding now has either a check or a recorded decision.

## Data and sourcing

**The figures are recomputed, not trusted (1.1).** `data_problems` imports
`ROWS`, recomputes `score_total`, `nosub3`, `sub3` and `keep3` from `price`,
`extra`, `sub` and `free_records`, and compares each with the CSV that ships.
It also resolves every source key and fails on a duplicate. Changing `min` to
`max` in the build now fails the audit with the model and column named.

**The date is data (1.2).** `CHECKED_ISO` is the one hand-typed fact. The build
refuses a future date, the page prints it, and the check warns at 30 days and
fails at 60. The CSV and shortlist read the same value, so the three printed
dates cannot drift.

**A second card is counted (1.3).** A row may set `cards`; the derived extra
adds `CARD` for each card beyond the one already in the base figure. No product
needs two today, so no number moved, but the assumption is now a field rather
than a line of prose.

**Claims carry their own sources (2.1).** `rec_src`, `history_src` and
`ha_src` are required keys and must also appear in the row's `src` list. The
record cell and the two detail lines print their own footnote, so the reader
checking "cloud optional" follows one link instead of four to nine. The eufy
and Arlo Home Assistant claims got the community integrations' own pages, which
also corrected the eufy sentence to the live `ha-eufy-sdk` project.

**The plan region is data (2.2).** The two EZVIZ rows carry
`plan_price_region="EU"`. The CSV has a region column, the table's plan cell
carries `data-region` and a visually hidden "EU price, not a UK quote", and the
comparison appends the same caveat to the Plans row. The facts stay open with
their blocker because CloudPlay publishes UK pricing only in its app; nothing
claims otherwise.

**An open fact must name its blocker (2.3).** The check rejects a bare "Not
confirmed", "unknown", "TBC", "pending" or "not yet verified", and requires a
word naming where the answer lives: app, support, docs, page, terms, datasheet,
retailer, listing, PDF, FAQ or manual. The two EZVIZ sentences pass on "app".

## Verification

**CI runs the audit (5.1, 4.3).** `.github/workflows/audit.yml` installs the
requirements, Chromium and Firefox, then runs `build/check.py` on every pull
request and push to `main`. The check rebuilds first and fails if a generated
file is stale, so a green run means the committed page is the page that passed.

**Each check is named and timed (5.2).** Every result is one name, printed with
its duration, and the three slowest are reported. `--only "<name>"` runs just
the matching checks and skips the page phases nothing in them needs; `--list`
prints the names. A failure now starts with the name of the check.

**Counts come from `ROWS` (5.3).** Row, source, bar and compare counts are
derived, not typed; the two label strings the check used to hardcode come from
`REC_LABEL`. The compare table's 18 rows are named as its 17 spec rows plus the
cost row, because that count belongs to the table rather than the dataset.

**Firefox runs the structural half (3.2).** `firefox_check` loads the same page
and repeats the structure audit, the phone containment and desktop grid
measurements, overflow, and axe at 390 and 1280px in both themes. It found no
difference. Chromium-only claims about `content-visibility` or the grid rows
are now observations about two engines.

## Architecture

**The page's CSS and JavaScript are files (6.1).** `build/page.css` and
`build/page.js` are readable, lintable and syntax-checkable; `node --check
build/page.js` passes on the source because the data placeholder sits in a
comment. The build substitutes the JSON and date, then emits both as hashed
assets.

**The assets ship separately (4.1).** The audit said to measure before deciding.
With `gzip -9`, the inlined page was 29,020 bytes; the split is 29,840 bytes on
a first visit and 13,516 on a repeat. The split costs 820 bytes on a cold cache
and halves every visit after it, which is the reader's second visit onward, so
the build emits `assets/page.css` and `assets/page.js`, linked with a content
version in the query. The check fails if the page loads a different URL or a
stale copy.

A hashed filename was the audit's wording, and the first version used one. It
broke a cached visitor: GitHub Pages serves HTML with a ten-minute cache, and a
deploy that deleted the old hash left that cached copy requesting a file that
no longer existed. A query version keeps every old URL resolvable while still
busting the cache. The measurements are in
`docs/performance-budget.md`.

**One page, one name (4.2).** `index.html` is canonical and `doorbells.html` is
a 377-byte redirect with a canonical link, instead of a second 130KB copy. The
check asserts the redirect, its small size, and that the two are no longer
identical.

**Rows are checked before they are read (6.2).** `REQUIRED_ROW_KEYS` is
asserted per row, and an unknown key fails the build too, so a misspelling
cannot pass as an optional field. Optional keys are named: `power_note`,
`cards`, `plan_price_region`. Derived keys are excluded because the check calls
the same function after derivation.

**One money formatter (6.3).** `money(x, decimals=2)` replaces `money` and
`gbp`; `decimals=None` keeps whole pounds whole.

## Accessibility and content

**The comparison scrolls for a keyboard user (3.1).** `.cmp-scroll` is a
`role="region"` with a `tabindex="0"` and the name "Comparison table, scrolls
sideways", plus a focus ring. `scroller_check` opens three models at 390px,
confirms the content overflows, focuses the region and asserts ArrowRight moves
it. This is the audit's preferred fix; the alternative, stacking the third
model, was not taken.

## Deliberately unchanged

**The phone header stays in the tree (3.3).** At 390px the visual header is
clipped but the eight column headers remain available to a screen reader. That
is the right trade for a data table, and the check asserts it. A screen-reader
user meets column names a visual reader does not; the same is true of the
`data-label` text in every card.

**The comparison keeps its sideways scroll (7.1).** With 3.1 fixed by a named,
focusable region, stacking is no longer needed. Two models side by side and the
third below would make the three-way comparison harder to read at the moment
the reader is comparing three things.

**"No cookies" stays (7.2).** The sentence is accurate: no cookies, no
tracking. The theme preference is in `localStorage`, which is not a cookie, and
the page adds no storage beyond it. If storage is ever added, the sentence has
to move with it.

## Consequences

- The audit document is gone. Its findings live here, in the check names above,
  and in `docs/performance-budget.md`.
- `build/check.py` is one command with 64 named checks; a full run including
  Firefox is about a minute.
- The page is now four HTTP requests (HTML, CSS, JavaScript, favicon) plus
  images, with the CSS and JavaScript versioned by content.
- The two EZVIZ plan figures remain EU prices. Closing them needs a UK price
  from the app or EZVIZ support; until then the region is data and the row says
  so.
