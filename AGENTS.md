# Working notes for agents

This repo is one generated page plus its dataset. `build/rows.py` holds the
data (`ROWS`, `S`) and every derived figure; `build/build.py` turns it into
files. `index.html`, the `doorbells.html` redirect, `404.html`,
`assets/page.css`, `assets/page.js`, `data/doorbells.csv` and
`data/doorbells.md` are generated from `ROWS`. Run `python build/check.py`
before committing.

## Sourcing rules

Each row in `ROWS` has a `src` list of footnote keys, five claim keys
(`price_src`, `rec_src`, `history_src`, `ha_src`, `plan_src`) and an optional
`unverified` sentence. A claim key must also appear in that row's `src` list, so
the reader can check the record claim, the history claim, the plan claim and the
Home Assistant claim on their own. `plan_src` is the page that publishes the
plan's price, or, where the row has no plan, the page that says none is needed.

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
- A claim key is what a figure's source card reads. The card opens from the
  figure in the table and in the comparison, and prints the source's name, its
  URL, the day the prices were checked, the row's own sentence for that claim
  and, for a 3-year total, the sum it is made of. A figure with no claim key
  behind it cannot carry its own source, so adding one means adding a key here
  first. The numbered register and the markers stay in the markup for the
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
