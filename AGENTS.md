# Working notes for agents

This repo is generated pages plus their dataset. `build/rows.py` holds the
data (`RAW_ROWS`, `S`) and every derived figure; `build/model.py` parses it once
into frozen `Row`, `Figures`, `Source` and lineup records; `build/build.py`
turns those records into files. `index.html`, `cameras/index.html`,
`rings/index.html`, `printers/index.html`, `pet-trackers/index.html`,
`baby-monitors/index.html`, the `doorbells.html` redirect, `404.html`,
`assets/page.css`, `assets/page.js`, the CSVs and Markdown in `data/`, plus the
photos and `IMAGE_SOURCES.md`, are generated from those rows.
Run `python build/check.py --fast` before every commit. `.githooks/pre-commit`
runs the same checks once the hooks are enabled; the steps are under Change
checks. Run the full `python build/check.py` before pushing.

## Categories

`build/catalog.py` holds `CATEGORIES`, one record per category: its route and
file names, its nouns and copy, the row keys it needs, its facets and the
vocabularies of its record, power and verdicts, its score parts, the claims a
figure can carry, the comparison's rows and pinned count, its sort options, and
the method, CSV and markdown words. `build.py` renders a record and knows no
product; `rows.py` authors every product, including its verdict and its plain
sentences, so a product is written in one file.

To bring another category online:

1. add its record to `CATEGORIES`, with `route="cameras/"` for a page below the
   site root (`""` is the root). Asset links take one `../` per directory;
2. add its rows to `RAW_ROWS`, each carrying a `cat` and facets drawn from that
   record;
3. add its photos to `build/make_images.py` and run it, or record an honest
   placeholder where no official image survives;
4. run `python build/build.py` and `python build/check.py`. `category records`
   reads the new page back and fails on a count that misses its rows, a headline
   verdict no row carries, a file name the record does not own, an asset link
   that does not resolve from its route, or two `h1`s; `category words` fails if
   the copy still speaks another category's nouns; `category page behaviour`
   opens every non-root page and fails if its script reads the wrong rows, a
   sort, the comparison, a source card, an asset or the console breaks.

`row_problems()` validates every row against its category and stops the build
with the row's id and the reason: an unknown key, a missing facet, a `rec`,
`power` or `ha` outside the vocabulary, a score part over its maximum, and a row
with no route to recordings at all. A row becomes a frozen `Row` only after
that validation; `types` runs mypy over `build/` and `row model` exercises the
parse errors.

## Sourcing rules

Each row in `RAW_ROWS` has a `src` list of footnote keys, five claim keys
(`price_src`, `rec_src`, `history_src`, `ha_src`, `plan_src`), an optional
`extra_src` for the sundry its no-plan sum buys and an optional `unverified`
sentence. A claim key must also appear in that row's `src` list, so the reader
can check the record claim, the history claim, the plan claim and the Home
Assistant claim on their own. `plan_src` is the page that publishes the plan's
price, or, where the row has no plan, the page that says none is needed.

- Close a fact before you flag it. Open the vendor's own UK page for the
  product or plan first. If the price, limit or feature is published there,
  put the URL in `src` and delete the sentence from `unverified`.
- Vendor price widgets are often rendered client-side and region-gated.
  `read_url` fetches static HTML, which can be an old shell with no prices.
  Open the page in a real browser, confirm the region selector says United
  Kingdom, and read the rendered text. Reolink's cloud-plan page is the
  standing example: the static page shows no prices, the rendered page lists
  GBP plans.
- An empty `unverified` is the goal. The page and the markdown only print an
  unverified line when the sentence is non-empty.
- A fact that stays open must name its blocker, for example "only shown in the
  app". "Not confirmed" on its own is not acceptable, and `build/check.py`
  fails it: the sentence has to contain a word such as app, support, docs,
  page, terms, datasheet, retailer, listing, PDF, FAQ or manual.
- Never present an EU or US price as a UK price. If only an EU price exists,
  say so in the same sentence and set `plan_price_region="EU"` on the row, so
  the CSV and the comparison carry the region as data. Re-check the fact
  before removing the region.
- Preferred order: vendor UK page, vendor support docs, UK retailer, then a UK
  review.
- Every figure in a 3-year sum is a price from a cited page, never an assumed
  one. The sundries those sums buy — the microSD card `CARD` and the USB stick
  `STICK` — are priced on the leading brand's right product, at the cheapest
  price found among reputable UK suppliers that publish it, and the row names
  that page in `extra_src`; other kit a sum adds, such as Arlo's SmartHub or
  Blink's Sync Module 2, is named in `kit_src` and priced in `kit_price`, which
  plus the sundry and any extra cards has to come to the row's `extra` — the
  method note prints that price, so it is authored, not recovered by
  subtraction. Either key must also be in the
  row's `src` list, so the sum's own source card can show every line of its
  arithmetic. `build/check.py` fails if a category whose rows buy a sundry
  stops printing its figure in that category's page or Markdown.
- Re-check the derived figures after any price change. `keep3` and `sub3` are
  computed in `build/rows.py`, and `build/check.py` recomputes them from
  `price`, `extra` and `sub`; a corrected input moves the ranking.
- A row sold by more than one shop carries `offers` instead of a price, and
  each offer is a shop, the page behind its price, the price, the
  configuration that price is for and a `pay` rank. `offer_winner()` shows the
  cheapest, unless another offer is within `OFFER_WINDOW` (£5) of it and pays
  more; ties go to the cheaper offer and then to the shop's name. The winner
  sets `price`, `price_src` and `price_note`, so a row with offers must not
  author any of the three. `pay` is a rank and not a rate, and it is per shop
  rather than per row, so a new shop is one entry. Adding a shop whose price
  you have not opened is worse than leaving the row with one offer.
- A paid link is a fact about the source, not about its address. `rows.py`
  builds `SPONSORED` where it tags the links, `rel()` and the source card read
  it, and the footer's "Some links are paid links" is checked. Do not re-derive
  "is this sponsored" from a URL pattern: that is how an Awin click shipped as
  an ordinary `nofollow`.
- An editorial jump (`{v:ID:Words}`) takes a row id. A name that is not an id
  renders a link to an anchor that does not exist and scrolls nowhere, so the
  category check reads every `class="jump"` target back against the page's own
  row ids.
- A claim key is what a figure's source card reads. The card opens from the
  figure in the table and in the comparison, and prints the source's name, its
  URL, the day the prices were checked, the row's own sentence for that claim
  and, for a 3-year total, the sum it is made of. The sentence has to answer
  the question the card's own title asks: the recording claim prints the row's
  `history` words, and a 3-year total prints the kit's storage words where its
  sum buys kit, the history words where it does not, or the row's own
  `nosub_say` / `plan_say` where the category supplies one. A figure with no claim
  key behind it cannot carry its own source, so adding one means adding a key
  here first. The numbered register and the markers stay in the markup for the
  printed sheet and the reader without a script, and the script hides both: the
  card is where a reader with a browser finds the page behind a number.

## Lineup

Every brand must be on the page in the newest model its vendor sells now. The
category's `current` map names that row; a missing entry fails `category
records`. A brand with no consumer product carries `(last model, reason)` so
the gap is recorded. A brand that sells more than one newest model names the
one the table covers.

Every brand also names the older row it still sells in `previous`, because the
older model is usually the cheaper way in. The page labels it and states the
saving. A brand with no older row carries `(None, reason)`; add `True` once the
absence is verified. A bare pair is a to-do, and `category records` notes every
brand still waiting for its row.

The newest model can change without any row changing. `build/lineup_feed.py`
reads the Ring and Tapo UK product feeds every Monday and lists whole products
that are neither a row, a lineup entry nor in `build/lineup_ignore.json`.
Accessories and bundles are omitted. The report is a nudge, not a gate: a
person decides whether a model belongs, and the next price check either adds
the row or records the reason in the ignore file.

A marketplace brand has no store of its own. Read its devices page, then the
listing's family menu; Blink's 2K+ was found one click from the Outdoor 4 row.
A placeholder photo is the same warning from the other side. `lineup photo`
fails if the row named in `current` has no vendor picture, and a model still on
sale always has one.

## Dates

Each record's `checked_iso` in `build/catalog.py` is the one hand-typed date
for that category. It is the day its prices and plans were checked, it is
printed on the page, and the build refuses a date in the future.
`build/check.py` warns after 30 days and fails after 60. Move it only after
re-checking the data.

`build/refresh.py` is the weekly nudge. It prints every page behind a row's
price and plan, grouped by category, and exits non-zero once a category is seven
days past its check; `.github/workflows/refresh.yml` runs it every Monday and
files the list as an issue, adding to the one already open. It reads no vendor
price and edits no data: a scheduled runner cannot see a price a page draws in
the browser, and moving `checked_iso` for a page nobody opened would be a lie.
The issue is the trigger and the reading stays a person's job. The same job
adds the `lineup_feed.py` report, then runs `build/links.py` over every category
page: blocked pages are listed and pass, while a dead page or server error
fails the run.

## Change checks

- The page's CSS and JavaScript are `build/page.css` and `build/page.js`. They
  are emitted as `assets/page.css` and `assets/page.js`, linked with a content
  version in the URL, not inlined. A change there needs a matching assertion in
  the family that owns it under `build/checks/` (`structure`, `behaviour`,
  `compare`, `accessibility`, `performance`, `browsers` or `data`), or the
  audit will not catch a regression. `build/check.py` is the runner.
- `build/check.py` rebuilds and fails if a committed generated file is stale.
  Commit the regenerated files in the same commit as the source change.
- `python build/check.py --only "<name>"` runs one named check (or a
  comma-separated list of name fragments); `--list` prints them. `--fast` runs
  only the browser-free static checks, and it is what `.githooks/pre-commit`
  runs. A normal run also starts Firefox for the structural audit.
- Enable both hooks once per clone with `git config core.hooksPath .githooks`.
  The pre-commit hook refuses a stale generated file before the commit exists.
- The checks take their fixtures from the data by property (`shortlist()`,
  `family()`, `cheapest()`, `lead_ids()`) and their columns, names and counts
  from the category record, so a new row or a new category does not mean editing
  an expected value. A check that names a product id or a count of rows is a bug.
- The byte budget is a check too (`transfer budget`): the page, the stylesheet
  and the script are gzipped and measured against the ceilings in
  `docs/performance-budget.md`. Raising one is a design decision, not a fix.
