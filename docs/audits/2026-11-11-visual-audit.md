# SubFree UK: visual and UX audit

**Date:** 11 November 2026
**Reviewer:** Critiquito
**Source:** live site https://lydenyardley.github.io/subfree-uk/ (repo main at `dcb631b`, 11 Nov 2026). Fresh screenshots taken on 11 Nov 2026 with Playwright Chromium on the box: desktop 1440 x 900 at 1x and mobile 390 x 844 at 2x (touch, iPhone user agent). Full-page shots are marked "full"; the rest are the first screen.
**Lens:** what a shopper trips over, ranked by what it costs them. Visible UI and behaviour only. Contrast was measured on every visible text run of the doorbell, cameras and 404 pages in both themes (WCAG AA: 4.5:1 body, 3:1 large text). Tap targets were measured on mobile against the WCAG 2.2 minimum of 24 x 24 px.

## Screens and viewports

Files are in `docs/audits/screenshots-2026-11-11/`.

| # | Screen / state | Desktop 1440 | Mobile 390 |
|---|---|---|---|
| 01 | Doorbells `/`, default (full) | `01-home-desktop.png` | `01-home-mobile.png` |
| 02 | Doorbells `/`, first screen | `02-home-viewport-desktop.png` | `02-home-viewport-mobile.png` |
| 03 | First row's "Costs & sources" open | `03-home-details-open-desktop.png` | `03-home-details-open-mobile.png` |
| 04 | Compare, Reolink PoE + Tapo D235 + Ring 2K ticked (full) | `04-home-compare-3-desktop.png` | `04-home-compare-3-mobile.png` |
| 04b | Compare, first screen | | `04b-home-compare-3-viewport-mobile.png` |
| 05 | Filtered to nothing (max £40, Local / Home Assistant) (full) | `05-home-filtered-empty-desktop.png` | `05-home-filtered-empty-mobile.png` |
| 06 | Dark mode (full) | `06-home-dark-desktop.png` | `06-home-dark-mobile.png` |
| 07 | Photo lightbox | `07-home-photo-lightbox-desktop.png` | `07-home-photo-lightbox-mobile.png` |
| 08 | Price source card (tap on a price) | `08-home-source-card-desktop.png` | `08-home-source-card-mobile.png` |
| 09 | Categories menu open | `09-home-category-menu-desktop.png` | `09-home-category-menu-mobile.png` |
| 10 | Keyboard focus after six Tabs | `10-home-keyboard-focus-desktop.png` | |
| 11 | `/cameras/` (full) | `11-cameras-desktop.png` | `11-cameras-mobile.png` |
| 12 | `/rings/` (full) | `12-rings-desktop.png` | `12-rings-mobile.png` |
| 13 | `/printers/` (full) | `13-printers-desktop.png` | `13-printers-mobile.png` |
| 14 | `/pet-trackers/` (full) | `14-pet-trackers-desktop.png` | `14-pet-trackers-mobile.png` |
| 15 | `/baby-monitors/` (full) | `15-baby-monitors-desktop.png` | `15-baby-monitors-mobile.png` |
| 16 | `/doorbells.html` (redirects to `/`) | `16-doorbells-moved-desktop.png` | `16-doorbells-moved-mobile.png` |
| 17 | 404 (`/does-not-exist`) | `17-404-desktop.png` | `17-404-mobile.png` |
| 18 | `/cameras/` dark, first screen | `18-cameras-dark-desktop.png` | `18-cameras-dark-mobile.png` |

## Screens not captured, and why

- **Fourth tick at the compare limit (the disabled checkbox state):** not captured, so earlier task 15 is not rechecked.
- **"Copy shortlist" success:** headless Chromium blocks the clipboard.
- **Retailer and Amazon pages behind the links:** outside the site.
- **No dev or admin routes exist.**
- **Capture artefacts, not filed:** on the compare full-page shots the sticky compare bar and the back-to-top button are drawn where the capture stopped, not where a visitor sees them. Full-page shots were taken with `content-visibility` forced on so that every row paints; on a real scroll the rows render as they come into view.

## Severity key

- **P1:** blocks the main task (choosing a product that records without a subscription) or undermines trust in the figures.
- **P2:** worth fixing; costs the shopper time or confidence.
- **P3:** polish.

## Top 3

1. Five of the six comparisons are hidden behind a small "Categories" disclosure in the corner, and the home page reads as a doorbell-only site, so most visitors never find cameras, rings, printers, pet trackers or baby monitors.
2. On a phone the "Side by side" compare shows one product at a time behind a "Swipe to see" hint, so it is not side by side at all.
3. On a phone each product card is about 480 px tall and the doorbell list runs to about 13,900 px, with no sticky way back to Filters or Sort.

## Tasks

### 1. Show all six categories at the top of every page
- **Severity:** P2
- **Screens:** 01, 02, 09, 11 to 15 (desktop and mobile)
- **Problem:** The site now covers six product types, but the only route between them is a "CATEGORIES" disclosure in small caps at the top right (top left on mobile, under the theme button). The home page H1 is "Video doorbells that work without a subscription", the intro only talks about doorbells, and nothing on the first screen says the site has cameras, rings, printers, pet trackers or baby monitors. The strapline also changes from "Gadgets that work without a subscription" on desktop to "No subscriptions" on mobile.
- **Fix:** Put the six categories as a visible row of tabs or pills under the site name on every page (scrolling horizontally on mobile), with the current one marked, and keep one strapline on both viewports.
- **Expected benefit:** Visitors who land on doorbells discover the other five comparisons, and visitors from search can switch category in one tap.

### 2. Let phone visitors compare at least two products at once
- **Severity:** P2
- **Screens:** 04, 04b mobile
- **Problem:** The compare panel pins a label column that takes about a third of the 390 px screen and shows one product column, with the next one cut off at the edge and a "Swipe to see TP-Link Tapo D235" hint. The hint is an improvement on 21 Oct, but a shopper still has to remember one product's figures while swiping to the next.
- **Fix:** On narrow screens drop the label column into a row heading above each attribute and show two products per screen side by side (or three at 33% with short values), keeping the swipe only for the third.
- **Expected benefit:** Phone shoppers can actually see the difference between their picks, which is the whole point of the compare.

### 3. Cut the phone list down to a scannable length
- **Severity:** P2
- **Screens:** 01, 03, 11 to 15 mobile
- **Problem:** Each phone card stacks Compare, photo, name, Best for, Records free, Price, two 3-year costs, Free features, Main catch and a "Costs & sources" button, about 480 px per product. The doorbell page is about 13,900 px tall and cameras about 10,900 px. Once past the first card there is no way back to Filters or Sort except the back-to-top button.
- **Fix:** Show only name, the bold 3-year figure, Records free and the badge on the card, and move Free features and Main catch into "Costs & sources". Add a slim sticky bar with "Filters" and "Sort" once the list starts.
- **Expected benefit:** About three products per screen instead of under two, and shoppers can refine the list without scrolling back up.

### 4. Give the "Check price" rows a figure or take them out of the ranking
- **Severity:** P2
- **Screens:** 01, 06 desktop; 01 mobile (Blink Battery Doorbell 2K+, Blink Video Doorbell 2nd Gen)
- **Problem:** Two rows show "Check price" in the Price column and in both 3-year columns, so the bold figure the list is sorted by is missing and they drop to the bottom of a cost-ranked list. A shopper can read that as "dearest" when it really means "no figure".
- **Fix:** Show the last known price with its date ("£59.99 on 2 Nov"), or group these rows under a small "Price not confirmed" heading below the ranked list, and say so in the row.
- **Expected benefit:** The ranking stays honest and the shopper is not misled about where Blink sits.

### 5. Raise the small type
- **Severity:** P2
- **Screens:** 01, 02, 11 to 15 (desktop and mobile)
- **Problem:** On desktop most table text is 13 px, secondary lines ("Best for", "Last generation", "cheapest for this model: with plan") are 12 px and the control labels "SHOW ONLY", "POWER", "PRICE", "SORT BY" and the footnote markers are 11 px uppercase. Mobile body text is mostly 12 to 13 px. Contrast passes everywhere I measured (no AA failures in light or dark), so size is the problem, not colour.
- **Fix:** Set table body text to at least 15 px on desktop and 16 px on mobile, secondary lines to 14 px, and control labels to 13 px in sentence case.
- **Expected benefit:** Easier reading for the older shoppers who buy doorbells and printers, and fewer zoom gestures on phones.

### 6. Explain what the coloured row borders and badges mean
- **Severity:** P3 (still open from 21 Oct task 13)
- **Screens:** 01, 11, 13
- **Problem:** Rows still carry green, blue or red left borders and badges ("Best overall", "Best wire-free pick", "Avoid without a plan") with no key, and the meaning leans on colour.
- **Fix:** Add a one-line key above the table and keep the badge text as the main signal.
- **Expected benefit:** Shoppers, including those with colour-vision differences, read the verdicts at a glance.

### 7. Make the 404 page match the rest of the site
- **Severity:** P3
- **Screens:** 17 desktop and mobile
- **Problem:** The new branded 404 is a big step up, but its six green buttons are each as wide as their own label so the stack has a ragged right edge, there is no Categories menu or theme button, and the paragraph lists all six pages in prose right above six buttons that say the same thing.
- **Fix:** Give the buttons one shared width, cut the paragraph to one sentence, and reuse the normal header.
- **Expected benefit:** A lost visitor sees a tidy page that clearly belongs to the site.

### 8. Fix the empty-state sentence
- **Severity:** P3
- **Screens:** 05 desktop and mobile
- **Problem:** With the price range at £40 to £40 the message reads "No doorbell costs between £40 and £40, and none works locally with Home Assistant."
- **Fix:** When both ends match, say "No doorbell at £40 or less works locally with Home Assistant."
- **Expected benefit:** The recovery message reads as written by a person.

### 9. Use one name for the short-answer box
- **Severity:** P3
- **Screens:** 01 vs 11 and 13
- **Problem:** The doorbell page heads the box "Short answer: which to buy" while cameras and printers use "The short answer".
- **Fix:** Pick one heading for all six pages.
- **Expected benefit:** The site feels like one product, not six pages written at different times.

### 10. Separate Sources from the spec list in phone Details
- **Severity:** P3
- **Screens:** 03 mobile
- **Problem:** In the open panel the "Sources:" line runs straight into the "Power" label with no gap, and it sits above the specs, so the first thing a shopper reads is a list of links.
- **Fix:** Move Sources to the end of the panel and give it the same spacing as the other groups.
- **Expected benefit:** The panel reads as specs first, evidence second.

### 11. Keep the back-to-top button off the content on phones
- **Severity:** P3
- **Screens:** 03 mobile
- **Problem:** The back-to-top button sits over the right edge of the Details text.
- **Fix:** Give the list bottom padding equal to the button, or show the button only after a pause in scrolling.
- **Expected benefit:** No text hidden under a floating control.

### 12. Replace the "No photo" tiles
- **Severity:** P3
- **Screens:** 01 (Hikvision DS-KB6003-WIP), 11 (Blink Outdoor 4)
- **Problem:** A grey box with "NO PHOTO" in small caps looks like a broken image next to real product shots.
- **Fix:** Use a simple outline drawing of the product type with the caption "No official photo".
- **Expected benefit:** The table looks finished and the gap reads as deliberate.

### 13. Tone down white photo tiles in dark mode
- **Severity:** P3 (still open from 21 Oct task 16)
- **Screens:** 06, 18
- **Problem:** Several thumbnails (Tapo TD21, EZVIZ DB2) still sit on bright white tiles against the near-black page.
- **Fix:** Dim the photo tiles slightly in dark mode or give them a mid-grey ground.
- **Expected benefit:** Dark mode is comfortable to scan.

### 14. Write compare and Details values in plain words
- **Severity:** P3 (partly open from 21 Oct task 18)
- **Screens:** 03, 04
- **Problem:** Values such as "microSD and/or NVR; RTSP/ONVIF" and "Wired Ethernet" still read as raw data.
- **Fix:** Lead with a plain sentence ("Records to a memory card or a home recorder") and put the protocol names in brackets.
- **Expected benefit:** Non-technical shoppers understand each product's setup.

### 15. Say which column the bold figure comes from when it switches
- **Severity:** P3
- **Screens:** 01, 13
- **Problem:** The sort now follows "the bold figure", which is a clear fix, but the bold value jumps between the no-plan and with-plan columns, and the only explanation in the row is an 11 px "cheapest for this model: with plan".
- **Fix:** Raise that caption to the table's body size, or add a small "with plan" tag next to the bold figure itself.
- **Expected benefit:** Shoppers can follow the ranking down the page without zig-zagging between columns.

## Earlier pass (21 Oct 2026)

| 21 Oct task | Status on 11 Nov | Where now |
|---|---|---|
| 1. Show the sort figure | Fixed: bold figure plus "Order: 3-year cost to keep recordings (the bold figure)" | Follow-up polish in task 15 |
| 2. Phone compare shows all three | Partly fixed: swipe hint and edge cue added, still one product per screen | Task 2 |
| 3. Visible link to each price source | Fixed: every price opens a named source card | |
| 4. Explain the "3 years, cheapest" row | Fixed: "Cheapest way to record for 3 years" with the basis under each total | |
| 5. Say which filter emptied the list | Fixed: names the filters and offers "Raise the maximum to £70" | Copy nit in task 8 |
| 6. Label and enlarge the compare checkbox | Fixed: visible "Compare" label, 60 x 44 px tap area | |
| 7. Shorten phone cards | Partly fixed: the two 3-year figures now sit side by side, cards still about 480 px | Task 3 |
| 8. Keep the "why" in the phone short answer | Fixed: four short lines including what to avoid | |
| 9. Branded 404 | Fixed | Polish in task 7 |
| 10. Say who runs the site | Fixed: footer names the maker and gives an email address | |
| 11. Readable headers, footnotes in place | Partly fixed: headers written out; labels still 11 px | Task 5 |
| 12. Replace the bare dash | Fixed: "No plan" | |
| 13. Explain row colours and badges | Still open | Task 6 |
| 14. Highlight differences in compare | Fixed: "Differences only" toggle and red text for missing features | |
| 15. Disabled checkboxes at the limit | Not rechecked (state not captured) | |
| 16. White photo tiles in dark mode | Still open | Task 13 |
| 17. Photo zoom on desktop, easier lightbox close | Fixed: magnifier on desktop, close button at top right | |
| 18. Plain wording in Details | Partly fixed | Task 14 |

Of the 18 earlier tasks: 11 fixed, 4 partly fixed, 2 still open, 1 not rechecked.

## Severity count

| Severity | Count |
|---|---|
| P1 | 0 |
| P2 | 5 |
| P3 | 10 |
| **Total** | **15** |
