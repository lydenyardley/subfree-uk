# 26. The sundries carry their own price

- Status: Accepted
- Date: 26 October 2026
- Source: the owner's request of 26 October 2026 — find a citable page for the
  £10 card or USB stick in the 3-year sums, or price each row from its own
  vendor, and close the assumption note; and, when told which product to price,
  the card has to be SanDisk and may come from any reputable supplier at the
  best price on the right product.

## Context

Every no-plan 3-year total adds the card or stick the doorbell records on:
£10.00, typed into `build/rows.py` as `CARD` and confessed wherever the figure
showed. The sum's source card carried "The card or USB stick in that sum is an
assumption at £10.00, not a figure from a cited source", the method paragraph
under the table and `data/doorbells.md` said the same, and ADR 1 lists the
confession as one of the page's five guardrails. It was honest, and it was the
one figure on the page that no reader could check.

The price is no longer what it was. The cheapest 64 GB card that would work
here, from the line the vendor builds for the job, now costs more than twice
the assumption on the cheapest UK listing found, so the confession was also
understating the sums it sat in.

## Decision

**A sundry in a 3-year sum is a price from a cited page.** Two figures, both
read in a browser on 26 October 2026 at the best delivered UK price found for
the leading brand's right product:

| Sundry | Product | Price | Cited page |
|---|---|---:|---|
| `CARD` | SanDisk High Endurance 64 GB microSDXC, SDSQQNR-064G-GN6IA | £25.37 | Amazon UK, `sandisk_card` |
| `STICK` | SanDisk Ultra Curve 64 GB USB-A flash drive, SDCZ550 | £11.99 | Amazon UK, `sandisk_stick` |

The High Endurance line is the one SanDisk makes for dash cams and home
monitoring, so it is the right product for a doorbell or its chime; the Ultra
Curve is a plain USB-A drive, which is what an Arlo SmartHub and a Blink Sync
Module 2 both take (Sync Module 2: 1–256 GB; SmartHub: 16 GB or more).

**What was compared.** For the card: Senetic £23.92 plus £15.31 delivery
(dearer delivered, £39.23), Amazon UK £25.37, SanDisk's own store £25.99,
Argos £26.99, 7DayShop £27.99, Currys £43.99. A price-comparison page showed
"from £17.00" with no seller attached to it, and Argos, Currys, Insight and Wex
refused the fetch or failed, so none of those went in. For the stick: Ultra
Curve £11.99, Ultra Flair £16.97 at Amazon and £16.99 at John Lewis, Ultra Fit
£17.99. Amazon was the cheapest UK shop that publishes a price a reader can
open and check, and its delivery is free to a UK address; the cheaper Senetic
figure was not the cheaper purchase.

**Each row names the page in `extra_src`.** It works like a claim key: the key
has to be in `S`, it has to appear in that row's `src` list, and `row_problems`
fails either half by name. Seven rows buy the card (Reolink WiFi and PoE, Tapo
D230S1 and TD21, Aqara G4, EZVIZ DB2 Pro, Hikvision) and two buy the stick
(Arlo, Blink). The other kit a sum adds gets the same treatment through
`kit_src`, so Arlo's SmartHub and Blink's Sync Module 2 are priced on a page
just as the card and the stick are. The sum's source card now lists those pages
beside the doorbell's, so the arithmetic on the card can be checked line by
line, and `UNSOURCED_CARD` is deleted from `build.py` along with the note it
printed.

**The date does not move.** `CHECKED_ISO` stays 19 October 2026. The two
sundries were read a week later, and the date line on the page is about the
whole dataset: moving it would claim a re-check of fourteen doorbell prices and
their plans that has not happened. The next full re-check should fold the
sundries into the same day.

## Consequences

- The ranking moves, as a corrected input should. The cheapest three years on
  the page are now Tapo TD21 £70.36, EZVIZ EP3x Pro £79.99 and Reolink Video
  Doorbell PoE £95.36; Arlo, with a SmartHub and a stick, is £202.05 and Blink
  £121.97.
- Checks that had a figure or a position typed into them now read it from the
  dataset, so the next price change is a data edit rather than a test edit.
  `compare cost row` compares by model id instead of by column position, the
  jump announcement counts the row's position on the page, the shortlist's
  words and money come from `ROWS`, and the shared link compares the set of
  models rather than their order. The compare cost row failed on the re-priced
  data before this, reporting only that the columns had moved.
- `derived figures` now also proves that both files that print the method carry
  the figures the sums were built from, and that the assumption sentence cannot
  come back.
- Both checks were shown to fail on a real fault. Typing £10.00 back into the
  method paragraph fails `derived figures` with "the index.html method note does
  not price the microSD card at £25.37"; adding £1 to the expected cells fails
  `compare cost row` naming each model it disagrees about.
- The three years of a sum are still a lower bound: the card is bought once and
  lasts the period, but a reader who adds batteries, an SD adapter or delivery
  will pay more. The method paragraph says what it leaves out.
