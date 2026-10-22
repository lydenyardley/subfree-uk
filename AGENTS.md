# Working notes for agents

This repo is one generated page plus its dataset. `build/rows.py` holds the
data (`ROWS`, `S`) and every derived figure; `build/build.py` turns it into
files. `index.html`, the `doorbells.html` redirect, `404.html`,
`assets/page.css`, `assets/page.js`, `data/doorbells.csv` and
`data/doorbells.md` are generated from `ROWS`. Run `python build/check.py`
before committing.

## Sourcing rules

Each row in `ROWS` has a `src` list of footnote keys, four claim keys
(`price_src`, `rec_src`, `history_src`, `ha_src`) and an optional `unverified`
sentence. A claim key must also appear in that row's `src` list, so the reader
can check the record claim, the history claim and the Home Assistant claim on
their own.

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
- Re-check the derived figures after any price change. `keep3` and `sub3` are
  computed in `build/rows.py`, and `build/check.py` recomputes them from
  `price`, `extra` and `sub`; a corrected input moves the ranking.

## Dates

`CHECKED_ISO` in `build/rows.py` is the one hand-typed fact. It is the day the
prices and plans were checked, it is printed on the page, and the build refuses
a date in the future. `build/check.py` warns after 30 days and fails after 60.
Move it only after re-checking the data.

## Change checks

- The page's CSS and JavaScript are `build/page.css` and `build/page.js`. They
  are emitted as `assets/page.css` and `assets/page.js`, linked with a content
  version in the URL, not inlined. A change there needs a
  matching assertion in `build/check.py`, or the audit will not catch a
  regression.
- `build/check.py` rebuilds and fails if a committed generated file is stale.
  Commit the regenerated files in the same commit as the source change.
- `python build/check.py --only "<name>"` runs one named check (or a
  comma-separated list of name fragments); `--list` prints them. The run also
  starts Firefox and does the structural audit there.
