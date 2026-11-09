# 28. Two more categories: GPS pet trackers and baby monitors

- Status: Accepted
- Date: 9 November 2026
- Source: the owner's request of 9 November 2026, to build both pages from
  `docs/research/pet-trackers-page-outline.md` and
  `docs/research/baby-monitors-page-outline.md`, run every check, review the
  result and commit it.

## What was added

Thirteen rows: seven GPS pet trackers (PitPat, PAWVA, two Tractive models,
Weenect, Pawfit and an AirTag) and six baby monitors (VTech, two Philips
models, eufy, Nanit and Owlet). The Philips SCD971 from the outline was
dropped: no UK shop publishes a price for it. Each page is a category record
in `build/catalog.py` and its rows in `build/rows.py`, so neither page needed
a second renderer.

## The connection is the pet tracker's model

A "no subscription" pet tracker is one of three things, and the row's `power`
says which. `included` means the data comes with the hardware for its life
(PitPat). `fixed` means a prepaid term that will expire (PAWVA's five-year
SIM). `tag` means there is no GPS at all (AirTag). `plan` means the tracker
does nothing until a subscription starts (Tractive, Weenect, Pawfit). The
no-plan figure is the price plus any holder; the with-plan figure is the
price plus 36 monthly payments, and the method names the yearly price where
it is cheaper.

`rec` follows the same split: `yes` for included or fixed data, `tag` for a
Bluetooth tag, `no` for a required plan. `ha` is cat suitability, which is
what the "Suits cats" filter reads.

## The baby monitor's model is the connection too

A local radio monitor sends nothing outside the house, a hybrid adds an
optional app, and a Wi-Fi monitor has no parent unit. That is `power`:
`radio`, `hybrid`, `wifi`. Every row here works without a subscription for
live viewing, so the free tier is the no-plan figure and `rec` is `yes` or
`part`, never `no`. `ha` is account dependence, which the "Works without an
account" filter reads.

Owlet360's UK price is shown only in the Dream App, so its row has no plan
figure and says why. Nanit's Memories plan is £10 a month, or £120 a year;
its Sleep plan is £9 a month on the Breathing Band page, after three free
months.

## Prices were corrected against the pages

The outline's figures were drafts and several did not survive the read:

- PitPat is £149, not £99. Saved walks are free; LIFE adds Video Vet and loss
  replacement, so the row does not claim walks are paywalled.
- PAWVA's X01+ ships with a five-year SIM. The ten-year claim is the X02's,
  so the X01+ row carries five.
- The Philips SCD951 is £157.99 on Amazon, not at Currys, which lists
  £213.99. The row cites the page its price is on.
- The eufy C10 is £114.99 from eufy for the full kit. The £99 Amazon listing
  is the camera-only variant, so it is not the row's price.
- Nanit and Owlet are priced from their own UK pages, £299 and £299.99. The
  Amazon listings the outline used could not be matched to those prices.
- The Philips SCD881 is the UK /05 variant at Currys, £109.99; the /26 is the
  same monitor with an EU plug.

## The byte budget follows the rows

The script carries every row of every category for the filters and the
comparison. Thirteen rows took it from 29,379 to 33,732 gzipped, and a first
visit from 70,443 to 74,826. The ceilings move to 36,000 for the script and
80,000 for a first visit, with the measurement recorded in
`docs/performance-budget.md`. Nothing was trimmed to fit: the copy is the
product.

## Consequences

- `build/check.py` now renders six pages. `category records`, `category
  words` and `category page behaviour` cover both new routes, and the lineup
  checks require a `current` row and a `previous` entry (or a recorded gap)
  for every brand.
- The shared navigation, 404 page and assets changed for all six pages in the
  same commit as the new records.
- The next category is still a record, its rows and its photos. The build
  knows no product.
