# Affiliate links: what is available and what it would cost us

Research done 18 October 2026. This page records what we found before adding any
affiliate link to the site, because three of the current claims depend on it:
"No affiliate links" (the intro), "No affiliate links, no tracking, no cookies"
in `data/doorbells.md`, and the use of Amazon product pages as price sources.

**Status: research only. No affiliate links are live.**

Nothing here is legal advice. Commission rates, network terms and Amazon's
operating agreement change; re-check each one before signing up.

## Short version

- We can realistically join first-party programmes for **eufy, Reolink, Arlo,
  Aqara and Tapo**, all through affiliate networks (Awin, Webgains, Impact).
- **Ring, Google Nest, Blink and Hikvision** have no publisher-facing UK
  programme we could find. For those, retailer programmes are the route:
  **Amazon Associates UK**, **Currys via Awin**, or **eBay Partner Network**.
- Every programme can reject small publishers. Applying is not the same as
  being accepted.
- **Amazon is the awkward one.** Three rows currently take their price from an
  Amazon listing (Aqara G4, Blink 2K+, EZVIZ EP3x Pro). Amazon's linking terms
  only allow prices that Amazon serves through a link or the Product
  Advertising API, so hard-coded Amazon prices in a static page are a terms
  problem, not just a freshness problem.
- Adding links means changing the site's "no affiliate links, no tracking"
  claim. That claim is currently true and worth keeping until the links ship.

## Brand programmes

| Brand | Programme | Network | Approval | Published rate | Apply |
|---|---|---|---|---|---|
| eufy | Yes, UK programme | Awin | "Select affiliates"; apply, acceptance not assured | 7% standard, 30-day cookie; eufy's own UK page says 7-15% for approved sales | [Awin listing](https://ui.awin.com/merchant-profile/36326), [eufy UK](https://www.eufy.com/uk/affiliate) |
| Reolink | Yes | Awin or Impact (own page does not say which serves the UK) | Apply and be approved; invites sites, blogs, YouTube | 6-20% in tiers by volume | [reolink.com/affiliate](https://reolink.com/us/affiliate/), affiliate@reolink.com |
| Arlo | Yes, UK | Awin | Apply; no published minimum audience | 10%, 30-day cookie, validated 30 days after sale | [Awin listing](https://ui.awin.com/merchant-profile/122884) |
| Aqara | Yes, UK | Awin | Apply; higher rates mentioned for content sites | 5%, 30-day cookie | [Awin listing](https://ui.awin.com/merchant-profile/99139) |
| TP-Link Tapo | UK listing exists | Webgains | Unverified | Reported 5%, up to 14 days; not confirmed from the listing page itself | [Webgains listing](https://www.webgains.com/front/publisher/program/view/programID/296930) (page did not load when checked) |
| EZVIZ | Yes | Impact | Apply; UK availability not confirmed | Not published on the page we read | [EZVIZ affiliates](https://www.ezviz.com/ca/page/affiliate-program) (Canada locale) |
| Ring | None found for publishers | - | - | - | Use Amazon UK or Currys instead |
| Google Nest | None found for hardware (Workspace only) | - | - | - | Use Amazon UK or Currys instead |
| Blink | None current (FlexOffers says not currently offered) | - | - | - | Use Amazon UK or Currys instead |
| Hikvision | None found; partner programme is for installers | - | - | - | Use Amazon UK or eBay instead |

Unconfirmed and worth a direct email before building anything: Reolink's UK
network, Tapo's UK rate and acceptance, EZVIZ UK availability, and whether any
programme will accept a one-page site.

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

The site currently says "No affiliate links, no tracking, no cookies." Once an
affiliate tag is in a URL, that sentence is misleading even though we set no
cookie ourselves. Honest replacement:

> We set no cookies and run no analytics. Some retailer links carry an affiliate
> tag, which lets the retailer or its network attribute a sale; the retailer's
> own cookie policy then applies.

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

1. Join Awin (one account covers eufy, Arlo, Aqara and Currys) and apply to
   those four programmes.
2. Ask Reolink which network serves UK, and ask Webgains/TP-Link for the UK
   Tapo terms. Email EZVIZ about UK availability.
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
  differ by brand.
- Which Amazon category a video doorbell falls into (5%, 3% or 2.5%) is not
  confirmed.
- Whether Reolink's UK traffic converts through Awin or Impact.
- Whether a "no tracking" claim can survive any affiliate tag at all, or
  whether the intro should simply say "no analytics, no cookies on this site".
