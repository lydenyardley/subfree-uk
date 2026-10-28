# Working notes for agents

This repo is one generated page plus its dataset. `build/rows.py` holds the
data (`ROWS`, `S`) and every derived figure; `build/build.py` turns it into
files. `index.html`, the `doorbells.html` redirect, `404.html`,
`assets/page.css`, `assets/page.js`, `data/doorbells.csv` and
`data/doorbells.md` are generated from `ROWS`. Run `python build/check.py`
before committing.

## Categories

`build/catalog.py` holds `CATEGORIES`, one record per category: its route and
file names, its nouns and copy, the row keys it needs, its facets and the
vocabularies of its record, power and verdicts, its score parts, the claims a
figure can carry, the comparison's rows and pinned count, its sort options, and
the method, CSV and markdown words. `build.py` renders a record and knows no
product; `rows.py` authors every product, including its verdict and its plain
sentences, so a product is written in one file.

To bring a second category online:

1. add its record to `CATEGORIES`, with `route="cameras/"` for a page below the
   site root (`""` is the root). Asset links take one `../` per directory;
2. add its rows to `ROWS`, each carrying a `cat` and facets drawn from that
   record;
3. run `python build/build.py` and `python build/check.py`. `category records`
   reads the new page back and fails on a count that misses its rows, a headline
   verdict no row carries, a file name the record does not own, an asset link
   that does not resolve from its route, or two `h1`s; `category words` fails if
   the copy still speaks another category's nouns.

`row_problems()` validates every row against its category and stops the build
with the row's id and the reason: an unknown key, a missing facet, a `rec`,
`power` or `ha` outside the vocabulary, a score part over its maximum, and a row
with no route to recordings at all.

## Sourcing rules

Each row in `ROWS` has a `src` list of footnote keys, five claim keys
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
  arithmetic. `build/check.py` fails if the method note in `index.html` or
  `data/doorbells.md` stops printing either sundry's figure.
- Re-check the derived figures after any price change. `keep3` and `sub3` are
  computed in `build/rows.py`, and `build/check.py` recomputes them from
  `price`, `extra` and `sub`; a corrected input moves the ranking.
- A claim key is what a figure's source card reads. The card opens from the
  figure in the table and in the comparison, and prints the source's name, its
  URL, the day the prices were checked, the row's own sentence for that claim
  and, for a 3-year total, the sum it is made of. The sentence has to answer
  the question the card's own title asks: the recording claim prints the row's
  `history` words, and a 3-year total prints the kit's storage words where its
  sum buys kit and the history words where it does not. A figure with no claim
  key behind it cannot carry its own source, so adding one means adding a key
  here first. The numbered register and the markers stay in the markup for the
  printed sheet and the reader without a script, and the script hides both: the
  card is where a reader with a browser finds the page behind a number.

## Dates

`CHECKED_ISO` in `build/rows.py` is the one hand-typed fact. It is the day the
prices and plans were checked, it is printed on the page, and the build refuses
a date in the future. `build/check.py` warns after 30 days and fails after 60.
Move it only after re-checking the data.

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
  comma-separated list of name fragments); `--list` prints them. The run also
  starts Firefox and does the structural audit there.
- The checks take their fixtures from the data by property (`shortlist()`,
  `family()`, `cheapest()`, `lead_ids()`) and their columns, names and counts
  from the category record, so a new row or a new category does not mean editing
  an expected value. A check that names a product id or a count of rows is a bug.
- The byte budget is a check too (`transfer budget`): the page, the stylesheet
  and the script are gzipped and measured against the ceilings in
  `docs/performance-budget.md`. Raising one is a design decision, not a fix.
