# 29. The architecture audit's six findings

- Status: Accepted
- Date: 12 November 2026
- Source: the owner's request of 12 November 2026 to implement the six items
  in `docs/audits/2026-11-11-architecture-audit.md`, update the project docs and
  delete the audit.

The audit itself is gone. This records what was built and why, including the
two open questions it left for the owner.

## A page carries only its own rows

`build/build.py` used to put every category's rows into the one
`assets/page.js`. The script measured 33,971 bytes gzipped, and adding a printer
moved the doorbell page's first visit. Each page now embeds its own rows in
`<script type="application/json" id="rows">`; the browser never runs that
block, and `page.js` parses it once at the top. The shared script is logic
only, so one content hash still serves every route.

The page budget is 33,000 bytes and a first visit is 70,000. The doorbell page
is 30,240 bytes and a first visit is 62,652; the other pages are between 45,235
and 54,779. `page data` reads each page's JSON back, checks its slug and its
row ids, and fails if a page carries another category's rows. The detailed
numbers are in `docs/performance-budget.md`.

## The read path is a frozen record

`build/rows.py` still authors each product as a dict, because the source
comment belongs beside the row. Those dicts are validated and derived as
before, then `Row.from_raw()` parses each one once into the frozen records in
`build/model.py`:

- `Row` and `Figures`, so authored input and derived sums are different types;
- `Source` and `Offer` for the register and a row's shops;
- `Current` or `Absent` for a lineup entry, instead of an overloaded
  positional tuple.

Every page, CSV and check reads `Row`; no reader can add a field to a shared
row dict. `RowKey` is a literal whitelist, so mypy catches a misspelt `r[...]`
key in `build.py`, which a plain dict could not. The row guard still names a
vocabulary error before the parse, so its existing messages and the build's
refusal are preserved. `row model` seeds a missing price and a malformed
current lineup; both fail by field and by brand.

A previous pair is `(None, reason)` while its absence is a to-do, and
`(None, reason, True)` once a person has verified it. A bare pair is valid data,
not a parse error. Only the pair's shape can be checked; whether the absence
was meant to be verified is not something a parser can infer.

`types` runs mypy over `build/` with a zero-error baseline.

## One desktop grid template

The five copies of the eight-track desktop grid are one
`grid-template-columns` reading `--trk-*` custom properties. `grid tracks`
fails if the full template appears more than once or a track has no variable.
At 821 to 900 pixels the catch track is zero width and the catch spans the row
on a second line; the header hides its eighth cell with the same clip. The
first track stays at 47 pixels, which the CSS comment records as a 44 pixel
target plus the 3 pixel verdict border. This answers the audit's 40 pixel
question: the 47 is deliberate.

## A browser-free fast gate

`python build/check.py --fast` runs the 22 static checks without importing
Playwright or starting a browser. `.githooks/pre-commit` runs it, so a commit
without its regenerated files fails before it exists. The full suite stays in
CI and still runs the browser checks in Chromium and Firefox. The pre-commit
hook is enabled with the same `git config core.hooksPath .githooks` as the
message hook.

## The Monday product feeds

`build/lineup_feed.py` reads the Ring and Tapo UK Shopify feeds in
`refresh.yml` and appends a report to the weekly issue. It lists whole products
whose titles name the category and that are neither a row, a lineup entry nor
an entry in `build/lineup_ignore.json`. Accessories and bundles are omitted,
because a chime or a mount is not a model a reader chooses between. The first
run finds Ring's Battery Video Doorbell 2K Plus, Wired Video Doorbell 2K and
Wired Video Doorbell 2K Plus, and Tapo's TD23 and D235L. This answers the
audit's accessories question: the report is for models, and a person still
decides whether one belongs. The ignore file records the reason beside each
dismissed product.

The report reads product titles, not prices, and edits no data. A feed that
cannot be read is printed as unavailable and does not stop the price issue.
The full store walk remains a person's job because a title is not enough to
prove a model is current.

## The Lineup section keeps the rule

`AGENTS.md` now states the current and previous rules, names the checks that
enforce them and points at the feed report. The stories of the D230S1, Ring 5,
Blink 2K+ and the 4K models remain in the git history and the earlier ADRs.

## Consequences

- The six pages are generated from frozen records, and the build output is
  byte-identical to the pre-refactor output.
- `build/check.py --fast` is 22 checks; the full audit adds the browser
  families. Mypy is pinned in `build/requirements.txt`.
- `build/lineup_ignore.json` starts empty. It is a brand-to-title-to-reason
  map, for example `{"Ring": {"Product title": "Why it is not a lineup row"}}`.
  A product added to it needs the reason in the value.
- The untracked audits and research notes outside this one were left alone.
