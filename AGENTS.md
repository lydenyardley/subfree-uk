# Working notes for agents

This repo is one generated page plus its dataset. `build/build.py` is the only
source: `index.html`, `doorbells.html`, `data/doorbells.csv` and
`data/doorbells.md` are generated from `ROWS`. Run `python build/check.py`
before committing.

## Sourcing rules

Each row in `ROWS` has a `src` list of footnote keys and an optional
`unverified` sentence.

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
  app". "Not confirmed" on its own is not acceptable.
- Preferred order: vendor UK page, vendor support docs, UK retailer, then a UK
  review. Never present an EU or US price as a UK price. If only an EU price
  exists, say so in the same sentence.
- Re-check the derived figures after any price change. `keep3` and `sub3` are
  computed in `build/build.py`, so a corrected input moves the ranking.

## Change checks

- CSS lives in the `page` f-string in `build/build.py`. A change there needs a
  matching assertion in `build/check.py`, or the audit will not catch a
  regression.
- `build/check.py` rebuilds and fails if the committed pages are stale. Commit
  the regenerated files in the same commit as the source change.
