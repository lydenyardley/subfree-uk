# Page outline: GPS pet trackers that work without a subscription (draft)

Status: research draft for a future `/pet-trackers/` page. Not built, not published, not committed.
Checked: 9 Nov 2026 (evening, UK time). Every price below was read on the linked page on that date. "not shown" means the page did not publish it; nothing is estimated.
Free work only. Things that would cost money are flagged with **(costs money)**.

## 0. The honest headline

Almost every *true* GPS pet tracker has a SIM inside and someone pays for its mobile data. "No subscription" therefore means one of three things, and the page should say which on every row:

1. **Bundled data, paid once** - the maker includes the SIM and data in the price (PitPat: "for as long as you use it"; PAWVA: "10-year connectivity included").
2. **Subscription required** - the tracker does nothing useful until you buy a plan (Tractive, Weenect, Pawfit).
3. **No SIM at all** - Bluetooth/Find My tags (AirTag) or radio-frequency finders. Free forever, but they are *not* GPS trackers: they only update when a nearby phone passes, or within radio range.

## 1. Products (7 rows)

Compare ids follow the site style (short kebab-case).

| Compare id | Product | Type | Subscription? | Maker UK price (link) | Best UK retailer price found | Plan cost (maker's UK page) | 3-year cost (maths) |
|---|---|---|---|---|---|---|---|
| `pitpat-gps` | PitPat Dog GPS Tracker | GPS + cellular, SIM built in | **No** - data paid by PitPat. Optional PitPat LIFE £3.99/month (extras, not tracking) | [£99.00 (Black Friday, was £149.00)](https://www.pitpat.com/gps-tracker/) | PitPat direct £99.00 is cheapest. [Amazon UK £149.00, sold by PitPat](https://www.amazon.co.uk/dp/B0H7XTW5HY) | None needed ([PitPat FAQ on the product page](https://www.pitpat.com/gps-tracker/)); LIFE optional [£3.99/month](https://www.pitpat.com/pitpatlife/) | £99.00 + £0 = **£99.00** (at the current offer) |
| `pawva-x01-plus` | PAWVA X01+ | GPS + cellular (LTE-M, 2G fallback), SIM built in | **No** - "10-year connectivity included" | [£77.99](https://www.pawva.co.uk/product-page/pawva-x01-gps-dog-tracker-with-light-sound) | Maker only (no UK retailer listing found) | None needed for 10 years (same page) | £77.99 + £0 = **£77.99** |
| `tractive-dog-6` | Tractive DOG 6 | GPS + cellular, SIM built in | **Yes** - required | [£59](https://tractive.com/en/pd/gps-tracker-dog?edition=black&shopCountry=GB) | [Amazon UK £51.18, sold by Tractive](https://www.amazon.co.uk/dp/B0D6Z4L6BW) | [Basic: £13.50/month rolling; £84/year (1-year plan); £108 per 2 years. Premium: £96/year; £120 per 2 years; £240 per 5 years](https://tractive.com/en/c/plans) | £51.18 + 3 × £84 = **£303.18** (Basic, yearly) |
| `tractive-cat-6-mini` | Tractive CAT 6 Mini | GPS + cellular, built into a breakaway collar | **Yes** - required | [£59](https://tractive.com/en/pd/gps-tracker-cat?shopCountry=GB) | [Amazon UK £59.00, sold by Tractive](https://www.amazon.co.uk/dp/B0GKGHFQW3) | Same plans as DOG 6 ([plans page](https://tractive.com/en/c/plans)) | £59 + 3 × £84 = **£311.00** (Basic, yearly) |
| `weenect-xt` | Weenect XT (dogs) | GPS + cellular (2G/NB-IoT/LTE-M/4G), SIM built in | **Yes** - "Subscription required" | [£44.99 tracker only; £120.99 with a 1-year plan](https://www.weenect.com/uk/en/gps-dog-tracker/) | [Amazon UK £44.99, sold by Weenect](https://www.amazon.co.uk/dp/B0G7KPLBLB) | [£13/month rolling; 1-year £6.67/month; 2-year £4.59/month; 5-year £3.67/month (billed up front)](https://www.weenect.com/uk/en/gps-dog-tracker/); optional Premium £2.99/month ([subscriptions page](https://www.weenect.com/uk/en/subscriptions/)) | £44.99 + 36 × £13 = **£512.99** (monthly). Yearly total for the 1-year plan: not shown as a single figure |
| `pawfit-3` | Pawfit 3 | GPS + cellular (4G), SIM built in | **Yes** - "+ Subscription Plan" | [£54.99](https://www.pawfit.com/en-gb/product/pawfit-3.html) | [Amazon UK £54.99, sold by Pawfit](https://www.amazon.co.uk/dp/B082F7J7LW) | [Basic: £9.99/month (1 month); £71.88/year; £95.76 per 2 years. Premium: £83.88/year; £119.76 per 2 years; £143.64 per 3 years](https://www.pawfit.com/en-gb/product/pawfit-3.html) | £54.99 + 3 × £71.88 = **£270.63** (Basic, yearly) |
| `apple-airtag-2` | Apple AirTag (2nd generation) | Bluetooth + UWB, Find My network. **Not GPS** | **No** | [£29.00 (1 pack), £99.00 (4 pack)](https://www.apple.com/uk/shop/buy-airtag/airtag) | [Amazon UK £29.00 (1 pack)](https://www.amazon.co.uk/dp/B0GJTCB2QM); [4 pack £79.00](https://www.amazon.co.uk/dp/B0GJTMMWRS) | None | £29.00 + a collar holder (price not shown; not sold by Apple) |

Notes per row:
- **PitPat**: "There's no subscription needed to find your dog... no monthly fees required." SIM "installed at the factory, and we pay for all the data it uses... for as long as you use it." Live updates "every 10 seconds". Dogs only; the [cat tracker page](https://www.pitpat.com/cat-gps-tracker/) is a sign-up for launch news. Battery: "several days" (no hours figure published). App only (no web access). Optional PitPat LIFE adds free straps, Video Vet, loss replacement, "exclusive app features"; PitPat says tracking never needs it. Third-party reviews say walk history needs the paid upgrade ([Smart Bark review](https://www.smartbark.co.uk/post/pitpat-dog-tracker-review-gps-with-no-subscription)); **not confirmed on PitPat's own page**, so flag it as unverified. Price is a Black Friday offer; the Amazon listing is £50 dearer.
- **PAWVA**: UK company (Mildenhall, Companies House no. 16745513 on its homepage). "No subscription. No monthly fees. 10-year connectivity included". The X02 is [£110.00](https://www.pawva.co.uk/product-page/pawva-x02-gps-dog-tracker) with the same promise. The X01+ page says it falls back to "2G/3G" in weak areas - but [Ofcom says](https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/3g-switch-off) UK 3G is now switched off and 2G goes "by 2033 at the latest". 14-day returns. A new, small brand: treat the 10-year promise as the company's policy.
- **Tractive**: plans page shows GBP when opened from the UK, with "*Pricing may vary depending on location*". Prices shown as offers against higher struck-through prices (e.g. Basic 1-year "£7 / month" vs "£9 / month"). Basic gives 24-hour location history; Premium adds 365-day history, family sharing, worldwide coverage and GPS export. Monthly billing is Basic only.
- **Weenect**: says plainly "a subscription is necessary to operate our trackers". All plans include live tracking and 30 days of history.
- **Pawfit**: Basic walks up to 2 hrs, Premium up to 6 hrs; Ordnance Survey maps Premium only. Pawfit Lite for cats [£42.00 + plan](https://www.pawfit.com/en-gb/product/pawfit-lite-gps-tracker-for-cats.html).
- **AirTag**: Apple's page: AirTag "sends out a secure Bluetooth signal that can be detected by nearby devices in the Find My network". Apple's own words: "AirTag was designed to help people locate their personal belongings, not to track people or another person's property" ([Apple Newsroom, Feb 2022](https://www.apple.com/newsroom/2022/02/an-update-on-airtag-and-unwanted-tracking/)). Needs an iPhone. Samsung's Galaxy SmartTag2 is the Android equivalent ([Samsung UK, £34 in the page data, shown out of stock on 9 Nov](https://www.samsung.com/uk/mobile-accessories/galaxy-smarttag2-black-ei-t5600bbegeu/)); its page says it "must be connected to the user's mobile device" via SmartThings Find.

Considered, not included:
- **Tabcat** (radio-frequency finder, no SIM): tabcat.co.uk returned server errors (500/504) all evening, so no price or spec could be read. Re-check before adding.
- **Samsung Galaxy SmartTag2**: see AirTag note (stock unclear).
- **PAWVA X02**: same no-subscription model at £110.00; add if the page wants a second PAWVA row.

### Affiliate programmes (known so far)
| Shop / brand | Programme | Source |
|---|---|---|
| Amazon UK | Amazon Associates, tag `subfreeuk-21` (live on the site) | `docs/affiliate-links.md` in the site repo |
| PitPat | **Awin**, advertiser 43513: "Earn up to 10% commission per sale", 30-day cookie, "UK only" | [Awin profile](https://ui.awin.com/merchant-profile/43513), [PitPat affiliate terms](https://www.pitpat.com/affiliate-publisher-terms/) |
| Tractive | **Impact** (not Awin): "$20 per tracker sale", 30-day cookie | [Impact sign-up page](https://app.impact.com/advertiser-advertiser-info/Tractive1759963280585.brand) |
| PAWVA, Weenect, Pawfit, Apple | not shown / none found this pass | - |

Applying is free, but approval is not assured (Awin already rejected Currys and Very for this site). PitPat is the obvious first Awin application because the cheapest price is on PitPat's own site. **Joining Impact means a new account - ask Lyden first.**

Pricing rule check (site rule: best UK price; Amazon only when same or less):
- PitPat: link PitPat direct (£99 vs Amazon £149). If PitPat's Awin is approved, that link pays too.
- Tractive DOG 6: Amazon £51.18 is cheaper than tractive.com £59, so Amazon (tagged) wins.
- CAT 6 Mini, Weenect XT, Pawfit 3, AirTag 1-pack: Amazon ties the maker price, so Amazon (tagged) wins on commission.

## 2. Search terms and real questions

Search terms (phrases seen in UK thread titles and UK listings this evening, not search-volume data):
- "gps dog tracker no subscription" / "dog gps tracker no monthly fees" (Amazon UK listing titles above)
- "cat tracker" / "cat gps trackers"
- "tractive vs pitpat"
- "airtag collar vs tractive"
- "affordable dog gps"
- "pet tracker for my cat"
- "GPS dog tracker, worth it?"

Real questions (threads opened 9 Nov 2026):
| Community | Thread (title as posted) | Date | Note |
|---|---|---|---|
| r/CatsUK | [Cat tracker](https://www.reddit.com/r/CatsUK/comments/1xbnsvm/) | 21 Oct 2026 | 21 replies in the feed |
| r/CatsUK | [Getting close to the letting them out stage. Any tracker recommendations?](https://www.reddit.com/r/CatsUK/comments/1wle7ci/) | 20 Sep 2026 | 40 replies |
| r/CatsUK | [AirTag collar vs Tractive or similar for indoor/outdoor city cat?](https://www.reddit.com/r/CatsUK/comments/1wj6rwf/) | 17 Sep 2026 | The exact Bluetooth-vs-GPS question the page answers |
| r/CatsUK | [Cat GPS trackers](https://www.reddit.com/r/CatsUK/comments/1sswvco/) | 22 Apr 2026 | 26 replies |
| r/UK_Pets | [Tractive vs pitpat](https://www.reddit.com/r/UK_Pets/comments/1vg2fo6/) | 5 Aug 2026 | Subscription vs no-subscription head to head |
| r/UK_Pets | [Dog tracker](https://www.reddit.com/r/UK_Pets/comments/1qgkuxj/) | 18 Jan 2026 | |
| r/UK_Pets | [Affordable dog GPS](https://www.reddit.com/r/UK_Pets/comments/1mgcjnz/) | 3 Aug 2025 | Older, but 20 replies on cost |
| MoneySavingExpert | [Pet tracker for my cat](https://forums.moneysavingexpert.com/discussion/6668989/pet-tracker-for-my-cat) | 19 May 2026 | Replies name Tabcat, Tractive and quote "£84 for a year or £120 if you pay for 2 years" (a user's figures; the 2-year Basic price on Tractive's page now is £108). MSE bans posting about your own site |
| Gransnet | [A tracker on a cat](https://www.gransnet.com/forums/pets/1350413-A-tracker-on-a-cat) | 3 Aug 2025 | AirTag in a quick-release collar, "No subscription to pay"; Tractive refunded a 12-month plan |
| r/tractivegps | [Monthly subscription misnomer - seems like false advertising to me...](https://www.reddit.com/r/tractivegps/comments/1f6pgxx/) | 1 Sep 2024 | Not UK-specific; the title calls the "monthly" price misleading (post body not read) |
| HotUKDeals | [GPS Dog tracker, worth it? If so, which is best?](https://www.hotukdeals.com/discussions/gps-dog-tracker-worth-it-if-so-which-is-best-4523288) | not shown (page body did not load, title only) | |

Mumsnet Talk: no pet-tracker thread found in its reachable pages or by web search this evening (Mumsnet's search needs a browser).
Reddit pages were read via each thread's RSS feed (title, date, reply count); reply counts are feed entries minus the post itself.

## 3. Page outline

**Route:** `/pet-trackers/` (fits `cameras/`, `rings/`, `printers/`).
**Title tag:** GPS pet trackers that work without a subscription (UK)
**H1:** GPS pet trackers that work without a subscription
**Intro (2-3 lines):** Most GPS trackers for dogs and cats need a monthly plan, because a SIM inside has to send the location to your phone. We list the few that include their data in the price, the ones that charge for it, and what three years really costs. Some links are paid links. No cookies.

**H2 The short answer**
- Best no-subscription GPS for dogs: PitPat (data included "for as long as you use it").
- Cheapest no-subscription GPS: PAWVA X01+ (10 years of data included).
- Best for cats: no subscription-free GPS cat tracker found; Tractive CAT 6 Mini if you will pay, an AirTag if your cat stays near people's phones.
- Avoid paying monthly: every subscription tracker is cheaper on a 1- or 2-year plan than month by month.

**Filters** (same pattern as the other pages):
- Show only: Works without a subscription; GPS (not Bluetooth); Suits cats
- Data: Included for life / Included for a fixed term / Subscription / No SIM (Bluetooth)
- Price: slider/bands as on other pages
- Sort by: 3-year cost; Price, low to high; No subscription first; 3-year cost, no subscription; 3-year cost, with plan; Model, A to Z

**H2 Side by side** (comparison table columns):
| Compare | Model | Subscription? | Price | How it finds your pet (GPS+SIM / Bluetooth) | Live update rate | Battery | 3-year cost, no plan | 3-year cost, with plan | Main catch |
Extra columns for the CSV/markdown: Data included until; Location history free; Geofence/escape alert free; Works outside UK; Cat-suitable (weight/collar); Plan & UK price; Plan price region; Sources; Unverified / re-check; Last checked.

**H2 How we worked it out** - same method block as other pages; add "who pays for the data, and until when".

**H2 Bluetooth tag or GPS tracker?** (short explainer - see caveats below)

**FAQ**
1. Is there a GPS pet tracker with no subscription in the UK?
2. How can a tracker have no subscription if it has a SIM?
3. Will an AirTag work as a cat or dog tracker?
4. What happens to a "no subscription" tracker if the company closes?
5. Is the monthly plan or the yearly plan cheaper?
6. Do GPS trackers work in the countryside with poor signal?
7. Is a GPS tracker safe on a cat's collar?
8. Does a tracker work abroad?
9. Do I still need a microchip? Yes. [GOV.UK](https://www.gov.uk/get-your-dog-cat-microchipped): "All dogs in the UK must be microchipped and registered by the time they're 8 weeks old"; in England a cat must be microchipped and registered by 20 weeks. A tracker is extra, not a replacement.

## 4. Honesty caveats (must appear on the page)

- **GPS vs Bluetooth.** A GPS tracker works out its own position from satellites and sends it over the mobile network, so it needs a SIM and signal. An AirTag or SmartTag has no GPS and no SIM: it is only found when a passing phone on Apple's or Samsung's network hears it, so in a field or a quiet lane it may not update for hours. Apple says AirTag is for "personal belongings".
- **"No subscription" is a promise, not a contract term.** PitPat pays for data "for as long as you use it"; PAWVA includes "10-year connectivity". If either company stops trading or changes policy, the tracker could stop. Say so on both rows.
- **Signal.** Every GPS row needs mobile coverage at the pet's location (PitPat: "via mobile networks"; Pawfit: "Please ensure you have adequate network coverage"). UK 3G is switched off and 2G will go by 2033 ([Ofcom](https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/3g-switch-off)), so any "2G/3G fallback" claim is weaker than it reads.
- **Your phone pays too.** PitPat reminds users that the app uses the owner's phone data, which may cost when roaming.
- **Offer prices.** PitPat £99 is a Black Friday price (RRP £149); Tractive shows discounted plan prices against higher struck-through ones. Re-check before publishing and on a schedule.
- **Cats.** PitPat is dogs-only today. Cat trackers are heavier than they look on a small neck; Pawfit 3 says "dogs and cats weighing over 3.5kg". Only use breakaway/quick-release collars.
- **A tracker is not a fence.** It tells you where your pet is, it does not keep it safe (point made by owners in the Gransnet thread).

## 5. Unverified / to re-check
- PitPat walk history behind PitPat LIFE: only in a third-party review, not on PitPat's pages.
- PAWVA: no independent UK retailer, and its "2G/3G" claim conflicts with 3G being off.
- Tabcat: site down all evening.
- SmartTag2 stock and price: Samsung page shows "Out of Stock" and the price only in page data.
