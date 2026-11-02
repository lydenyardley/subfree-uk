# Affiliate links: what is available and what it would cost us

Research done 18 October 2026, before the first affiliate tag shipped. This page
records what we found and what changed when the tag went live on 1 November
2026, because the site's no-affiliate claim depended on it.

**Status: live. Every row's Amazon UK price and buy links carry
`tag=subfreeuk-21`, and Awin is joined as publisher 3141383. Webgains declined
the application on 2 November 2026.** The intro says
"Some links are paid links. No cookies." and every category page's footer
carries "As an Amazon Associate I earn from qualifying purchases."

Which links are paid is now data, not a pattern over the URL: `rows.py` builds
`SPONSORED` where it tags the links, and the markup and the script read `rel`
from that. A paid link that is not Amazon was previously emitted as an ordinary
`nofollow`, which is both a Google and an ASA problem.

Nothing here is legal advice. Commission rates, network terms and Amazon's
operating agreement change; re-check each one before signing up.

## Short version

- We can realistically join first-party programmes for **eufy, Reolink, Arlo
  and Aqara**, through Awin or Impact. **Tapo** only had a Webgains listing, and
  Webgains declined the application; its links stay plain until that changes.
- **Ring, Google Nest, Blink and Hikvision** have no publisher-facing UK
  programme we could find. For those, retailer programmes are the route:
  **Amazon Associates UK**, **Currys via Awin**, or **eBay Partner Network**.
- Every programme can reject small publishers. Applying is not the same as
  being accepted.
- **Amazon is the awkward one.** Doorbell and camera prices come from the
  vendor or another UK shop, and their Amazon link is only where to buy. The
  ring rows are different: most are priced from Amazon UK listings, so those
  are the rows where Amazon's rule that a price must come through a link or
  the Product Advertising API still needs checking. A hard-coded Amazon price
  in a static page is a terms problem, not just a freshness problem.
- **Rings now list offers.** Each ring row carries the shops that sell it and
  the page shows one of them, chosen by the rule below. RingConn Gen 2 moved to
  Argos at £159, which is £100 under the Amazon listing, and the Galaxy Ring to
  Currys at £150.97, £82 under it. The rows with no second GBP-priced shop still
  show an Amazon price: Oura Ring 4 and Ultrahuman Ring AIR (both tied on price,
  so Amazon's higher pay rank keeps it), and RingConn Gen 2 Air and Gen 3, which
  no UK retailer stocks in GBP at all. The rule reduces Amazon's share of the
  table; it does not remove it, and only a GBP price at another shop or the
  Product Advertising API does.
- The claim is changed, not quietly kept. The old "No affiliate links" line is
gone from the intro, the footers and the Markdown, and the replacement names
the paid links.

## Brand programmes

| Brand | Programme | Network | Approval | Published rate | Apply |
|---|---|---|---|---|---|
| eufy | Yes, UK programme | Awin | "Select affiliates"; apply, acceptance not assured | 7% standard, 30-day cookie; eufy's own UK page says 7-15% for approved sales | [Awin listing](https://ui.awin.com/merchant-profile/36326), [eufy UK](https://www.eufy.com/uk/affiliate) |
| Reolink | Yes | Awin or Impact (own page does not say which serves the UK) | Apply and be approved; invites sites, blogs, YouTube | 6-20% in tiers by volume | [reolink.com/affiliate](https://reolink.com/us/affiliate/), affiliate@reolink.com |
| Arlo | Yes, UK | Awin | Apply; no published minimum audience | 10%, 30-day cookie, validated 30 days after sale | [Awin listing](https://ui.awin.com/merchant-profile/122884) |
| Aqara | Yes, UK | Awin | Apply; higher rates mentioned for content sites | 5%, 30-day cookie | [Awin listing](https://ui.awin.com/merchant-profile/99139) |
| TP-Link Tapo | UK listing exists | Webgains | **Declined** 2 Nov 2026: "no data insights via our third-party tracking tool indicating low/no traffic" | Reported 5%, up to 14 days; not confirmed from the listing page itself | [Webgains listing](https://www.webgains.com/front/publisher/program/view/programID/296930) (page did not load when checked). Reapply only when traffic can be shown |
| EZVIZ | Yes | Impact | Apply; UK availability not confirmed | Not published on the page we read | [EZVIZ affiliates](https://www.ezviz.com/ca/page/affiliate-program) (Canada locale) |
| Ring | None found for publishers | - | - | - | Use Amazon UK or Currys instead |
| Google Nest | None found for hardware (Workspace only) | - | - | - | Use Amazon UK or Currys instead |
| Blink | None current (FlexOffers says not currently offered) | - | - | - | Use Amazon UK or Currys instead |
| Hikvision | None found; partner programme is for installers | - | - | - | Use Amazon UK or eBay instead |

Unconfirmed and worth a direct email before building anything: Reolink's UK
network, EZVIZ UK availability, and whether any programme will accept a
one-page site now that Webgains has said no to it.

## Awin

Joined 2 November 2026. **Publisher ID 3141383.** A deep link is a plain URL;
nothing loads on this site:

```
https://www.awin1.com/cread.php?awinmid=<advertiser>&awinaffid=3141383&ued=<encoded destination>
```

`ued` is percent-encoded. `clickref` is real and accepted in practice but is not
in Awin's published parameter table, so we do not rely on it. The redirect sets
Awin's own cookie on `awin1.com` and forwards to the shop; the page we serve
still sets none, which is why the footer says "No cookies" and no longer claims
"no tracking". Awin's Publisher MasterTag is an enhancement (bounceless
tracking, Convert-a-Link), not a prerequisite, and we do not load it.

Advertiser ids taken from Awin's own merchant-profile pages or a live affiliate
link, never guessed:

| Merchant | `awinmid` | Where |
|---|---|---|
| Ultrahuman | 69428 | [Awin profile](https://ui.awin.com/merchant-profile/69428). 7% to $10k, 10% to $35k, 15% after; 45-day cookie |
| Currys | 1599 | [Awin profile](https://ui.awin.com/merchant-profile/1599). 3% for editorial; carries the Galaxy Ring and RingConn Gen 2 offers |
| Very | 3090 | [Awin profile](https://ui.awin.com/merchant-profile/3090) |
| John Lewis | 1203 | One third-party affiliate link only; confirm in the account before use |
| Argos | none found | Argos links elsewhere run through `anrdoezrs.net` (CJ), not Awin |
| Samsung UK, Oura, RingConn, Amazfit | none found | No UK advertiser id located |

`AWIN_MERCHANTS` in `build/rows.py` maps a source key to its advertiser id, and
the tagging loop rewrites those sources into `cread.php` links. It carries
Currys (1599) for the Galaxy Ring and the RingConn Gen 2, whose offers are the
live part of the integration. Argos sells four of these rings and has no
programme we are in, so its links stay plain, and a shop whose id is not
confirmed stays plain too: a wrong id credits another advertiser.

## Webgains

**Declined 2 November 2026.** The application was refused with one reason:
"No data insights via our third-party tracking tool indicating low/no traffic."
Webgains judges an applicant's audience through a third-party traffic tool,
and its message says that tool found no traffic to review.

That is a statement about how the site is measured, not about the site. This
site runs no analytics, no pixels and no consent banner, so there is nothing
for a traffic-verification tool to find on it: nothing to detect on the page,
and no dashboard history in a provider that was never installed. Whatever a
network's tool would count, it cannot count a page that measures nothing.

What it changes here:

- **No Webgains advertiser id is wired, so no code changes.** `AWIN_MERCHANTS`
  remains the only paid-link map on this site, and Tapo's links were already
  plain because no id was confirmed.
- **Tapo has no route.** Its programme was listed only through Webgains, so it
  joins Ring, Google Nest, Blink and Hikvision in the plain-link column. The
  table above is updated to say so.
- **Reapplying needs evidence, not a better pitch.** Either a traffic source a
  network can read (an analytics provider, or Search Console access shared
  with them), or a network that accepts a manual audience summary. Any choice
  that puts a script on the page touches the "No cookies" footer and the
  privacy line in the intro, so it is a decision to take deliberately, not a
  side effect of an affiliate form.

## How a price is chosen

A ring is sold by several UK shops and its price moves with size and finish, so
a ring row lists `offers`: a shop, the page behind its price, the price, the
configuration that price is for, and a `pay` rank. `offer_winner()` shows the
cheapest, unless another offer is within **£5** of it and pays more; a tie goes
to the cheaper offer and then to the shop's name. The winner sets the price, the
link on it and the note beside it, so the three cannot disagree.

`pay` is a rank rather than a rate because only Amazon publishes a fixed
percentage: 2 for Amazon UK Associates, 1 for a UK shop with no programme we are
in, 3 for a brand programme that pays more (Ultrahuman's Awin rate). Every offer
names its configuration, because a size-7 sale price and a size-9 list price are
not a comparison.

`build/check.py` re-derives the winner from `offers`, compares it with the CSV
and the table (`derived figures`, `category records`), and runs the rule itself
on fixtures (`offer rule`), including the boundary at exactly £5 and £5.01. The
page's method note prints the rule and the £5 bound, so the reader can see why
the link goes where it does.

## Retailer fallbacks

| Route | Rate | Notes |
|---|---|---|
| [Amazon Associates UK](https://affiliate-program.amazon.co.uk/) | Category based: 5% Home Improvement, 2.5% Mobile Electronics, 3% All Other | Applied per product category; doorbell classification not confirmed. See the price rule below before using it. |
| [Currys via Awin](https://ui.awin.com/merchant-profile/1599) | 3% for Editorial Content, Communities & UGC and Content Creators | 30-day attribution. Sells Ring, Nest, Blink and Tapo. |
| [eBay Partner Network](https://partnernetwork.ebay.com/) | Rate card, not a single percentage | Application reviewed. Useful for Hikvision and used kit. |

The current price links point at brand stores (Ring UK, Google Store, eufy UK,
Reolink UK, Tapo UK, Argos). Those are the links that would carry a brand
programme tag, or an Awin/Webgains deep link where the brand uses one.

## What the rules require us to change

### Disclosure

The ASA treats an affiliate publisher as a secondary advertiser. Two things
matter for us:

- On a page that is mostly affiliate-linked product content, the commercial
  nature has to be clear **before** the reader engages, not in the footer.
  "Ad" or "Advertisement" is clearer than "affiliate" or "sponsored" alone.
- On a mixed page, the specific affiliate links need marking where they appear.
  A single site-wide disclosure is not enough.

The CMA's MoreNiche case is the UK consumer-law precedent: an affiliate
promotion needs a prominent statement of the arrangement, and ambiguity or a
late disclosure can be misleading.

Practical wording, near the table and on the linked rows:

> **Ad: we earn a commission when you buy through some links on this page. It
> does not change the ranking or the verdicts.**

Only use the second sentence if it stays true as programmes are added. If a
commission ever influences selection or order, say so instead.

Sources: [ASA affiliate marketing](https://www.asa.org.uk/advice-online/affiliate-marketing.html),
[ASA 2024 summary](https://www.asa.org.uk/news/get-yourself-affiliated-with-the-rules-on-affiliate-marketing.html),
[CMA MoreNiche](https://www.gov.uk/cma-cases/moreniche-non-disclosure-of-commercial-promotion-of-products),
[Business Companion: reviews and endorsements](https://www.businesscompanion.info/en/quick-guides/fair-trading/reviews-and-endorsements).

### Google

Mark every affiliate link `rel="sponsored"` (`rel="sponsored nofollow"` is also
fine). This is separate from the reader-facing disclosure. Our page already
uses `rel="nofollow noopener noreferrer"` on sources, so the change is small.
Google's spam policy on "thin affiliation" also applies: the comparisons,
verdicts and three-year sums are what make this page more than a link farm, so
they have to stay the main content.

Sources: [Qualify outbound links](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links),
[Spam policies](https://developers.google.com/search/docs/essentials/spam-policies).

### Amazon, specifically

- Required statement, clear and conspicuous on the site:
  **"As an Amazon Associate I earn from qualifying purchases."**
- Link-level disclosure near the link, for example "(paid link)" or "#ad".
- Links use a tag of the form `xxxxx-21`. Sub-tags are allowed for placement
  reporting, but never for identifying an individual visitor.
- **Prices:** show Amazon prices only when Amazon serves them (through the link
  or the Product Advertising API under its licence). Manually typed Amazon
  prices do not qualify. Where Amazon products are compared with other
  retailers, Amazon's lowest new price must be shown.
- Do not cloak the referrer or bounce visitors through an automatic redirect.

Sources: [Linking requirements](https://affiliate-program.amazon.co.uk/help/operating/linking),
[Programme policies](https://affiliate-program.amazon.co.uk/help/operating/policies),
[Disclosure help](https://affiliate-program.amazon.co.uk/help/node/topic/GHQNZAU6669EZS98).

**Consequence for this repo:** the Aqara G4, Blink 2K+ and EZVIZ EP3x Pro rows
use Amazon as `price_src`. If those become affiliate links, the honest fix is
to stop publishing an Amazon price in the table and put the source link behind
"Check price", or to drop the Amazon price source for another retailer. The
three-year sums would then need a fixed, dated price for the sundry, as the
microSD `CARD` and the stick `STICK` now are: both are cited to their own
Amazon UK page, which is the retailer conflict worth settling before an
affiliate tag goes near them (ADR 26).

### Cookies and the "no tracking" claim

A direct outbound link does not set anything on our page. The network or
retailer may set a cookie on its own site after the click; under PECR the
consent question belongs to what happens on the device, and to any tracking we
add ourselves. If we add click logging, pixels or link decoration, that needs a
consent assessment.

The site used to say "No affiliate links, no tracking, no cookies." Once an
affiliate tag is in a URL, that sentence is misleading even though we set no
cookie ourselves. It now says, in the intro and the footer:

> Some links are paid links. No cookies. As an Amazon Associate I earn from
> qualifying purchases.

The retailer or its network may set a cookie on its own site after the click.
We set none here and run no analytics.

Sources: [ICO storage and access technologies](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-the-use-of-storage-and-access-technologies/what-are-storage-and-access-technologies/),
[ICO cookies guidance](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/cookies-and-similar-technologies/),
[MDN Referrer-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy).

## Technical shape for a static GitHub Pages site

GitHub Pages serves static files and has no per-link server redirect. Options,
simplest first:

1. **Direct tagged deep links.** Put the tagged product URL straight in the
   source table. No redirects, no JavaScript, nothing to break, and it matches
   Amazon's rules. Downside: the tag is visible in the status bar, which is
   fine as long as the disclosure is clear.
2. **A `/go/` page per product** with a `<meta refresh>` or a JS redirect.
   Adds a click of latency, needs a separate file per product, and for Amazon
   an automatic intermediate redirect is against its policy. Not recommended.
3. **A redirect host** (Cloudflare Worker or similar) if we ever want click
   counts or a single place to swap tags. Only worth it if we need reporting
   that the networks do not already give us.

Link data belongs in `build/rows.py` with the rest of the sources: add an
optional `aff` URL per source or per row, and one helper that emits
`rel="sponsored nofollow noopener noreferrer"` plus the disclosure marker.
Everything else on the page stays generated, so the CSV and Markdown exports
keep matching the HTML.

## Suggested order of work

1. Awin is joined (publisher 3141383). Read each merchant's advertiser id out of
   the account and put the ones we can price in GBP into `AWIN_MERCHANTS`, so
   their offers carry a paid link instead of a plain one.
2. Ask Reolink which network serves UK. Tapo is closed off for now: Webgains
   declined, so its links stay plain until a network that reads this site
   accepts us. Email EZVIZ about UK availability.
3. Decide the Amazon question before applying to Associates: either drop
   Amazon as a price source for those three rows, or show "Check price" and no
   figure.
4. Add the disclosure block, the link helper and the `rel` attributes in one
   change, and update the intro, README and `data/doorbells.md` claim in the
   same commit.
5. Re-check every price note that says "Amazon UK" so the wording matches what
   the page actually does.

## Open questions

- Does any programme accept a single-page site with no newsletter or audience
  figures? Awin publishers are reviewed per advertiser, so the answer may
  differ by brand; Webgains does not, unless the traffic is measurable.
- Which traffic proof would satisfy Webgains on a reapplication, and is it
  worth a script on a page that currently sets no cookie? Search Console
  access or a privacy-friendly counter both change that claim.
- Which Amazon category a video doorbell falls into (5%, 3% or 2.5%) is not
  confirmed.
- Whether Reolink's UK traffic converts through Awin or Impact.
- Whether a "no tracking" claim can survive any affiliate tag at all, or
  whether the intro should simply say "no analytics, no cookies on this site".
  It now says the second thing: the footer's "no tracking" is gone.
- Which rings can stop showing an Amazon price. The offers rule leaves Amazon
  as the winner where it is cheapest and pays best, which is still five of the
  seven ring rows: Oura Ring 4, RingConn Gen 2 Air and Gen 3, Ultrahuman Ring
  AIR and the Galaxy Ring had no GBP-priced alternative we could verify. Only a
  second priced shop, or Amazon's Product Advertising API, changes that - not
  the routing rule.
