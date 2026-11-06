# Working notes for agents

This repo is generated pages plus their dataset. `build/rows.py` holds the
data (`ROWS`, `S`) and every derived figure; `build/build.py` turns it into
files. `index.html`, `cameras/index.html`, `rings/index.html`,
`printers/index.html`, the `doorbells.html` redirect, `404.html`, `assets/page.css`, `assets/page.js`,
the CSVs and Markdown in `data/`, plus the photos and `IMAGE_SOURCES.md`, are
generated from `ROWS`.
Run `python build/check.py` before committing.

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
2. add its rows to `ROWS`, each carrying a `cat` and facets drawn from that
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

Every brand a category covers must be on the page in the **newest** model its
vendor sells now, and each record says which row that is in its `current` map.
Not merely a model still on sale: the doorbells page carried the Tapo D230S1
after Tapo's UK store had stopped listing it, and named it as the brand's
current doorbell. A brand with no entry fails `category records`, so the
question cannot be skipped, and the entry has to name a row of that brand.
Where a brand sells more than one newest model, the entry names the one the
table covers. A brand with no consumer product in that category carries a pair
instead, the last model and the reason, so the gap is recorded rather than
hidden: Hikvision's two Wi-Fi doorbells are both end of life and its UK
catalogue now sells wired intercom door stations.

The older model matters as much as the newest, because it is usually the
cheaper way in. Every brand names the row it sold last in a `previous` map: the
model the current one replaced that the vendor still sells, which is Oura's
Ring 4 beside the Ring 5 and Tapo's C660 KIT beside the C675D KIT. The page
labels that row, and where the older model is the cheaper of the two it says by
how much. A brand with no older model to carry, or whose row has not been added
yet, carries a pair with the reason, and `category records` names every brand
still waiting for its row. That gap is a to-do with a page to read, not a
settled fact: the next price check adds the row, priced and photographed like
any other.

A launch is a new row, not a rewrite of `current`. Walking a brand's own store
collection page, rather than the one product page already in the table, is what
finds it: the 4K models, the S4 and the D260 were all missing while an older
model of the same brand sat in the table looking current. Prices for those new
rows are checked on the day they are added, and a model the store lists but has
sold out still gets its row, with the stock state in `price_note`.

The map asks one question per brand, so it cannot see a newer model beside a
row that is still on sale, and no check can browse a vendor's store. Re-read
the collections for every brand whenever you move `checked_iso`: the rings page
spent a week offering Ring 4 as the current Oura. A row that names a withdrawn
product is a data edit: rename it if the vendor renamed the same product
(Ring's Stick Up Cam Pro became the Outdoor Camera 4K Pro), and replace it if
the product is gone (the D230S1's row became the D235).

A brand that sells through a marketplace instead of a UK shop of its own is the
blind spot. Blink has no store, so its collection page is
`blinkforhome.com/products` and the Amazon listing the table already cites is
not it: the Outdoor 4 stayed the page's current Blink after Blink had put the
Outdoor 2K+ on sale beside it, and the 2K+ was found on the listing's own
family menu, one click from the row that was already there. Read the brand's
devices page first, then the listing's navigation for the models that page does
not carry.

A placeholder photo is the same warning from the other side. `make_images.py`
records a placeholder only where the vendor's own site has no picture of the
model, and a model still on sale always has one, so the row named in `current`
is not allowed to be a placeholder: `lineup photo` fails with the brand and the
row. The Outdoor 4's placeholder said its successor was the 2K+ in so many
words, and was read past at the price check.

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
page and edits no data — a scheduled runner cannot see a price a page draws in
the browser, and moving `checked_iso` for a page nobody opened would be a lie —
so the issue is the trigger and the reading stays a person's job. The same
job then runs `build/links.py` over every category page: blocked pages are
listed and pass, while a dead page or server error fails the run.

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
