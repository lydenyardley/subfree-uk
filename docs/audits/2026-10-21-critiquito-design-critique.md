# subfree-uk: design critique

**Date:** 2026-10-21
**Reviewer:** Critiquito
**Source:** live site https://lydenyardley.github.io/subfree-uk/, which matches repo commit `7298192` (main, 19 Oct 2026). Screenshots taken by Side Hustle CEO on 21 Oct 2026 at desktop 1280 px and phone 390 px (2x).
**Lens:** what a visitor trips over, ranked by what it costs them. Visible UI only.

## Routes and states covered

| # | Route / state | Desktop | Phone |
|---|---|---|---|
| 01 | `/` home, default | `01-home-desktop.png` | `01-home-phone.png` |
| 02 | `/` with Details open (Reolink PoE row) | `02-home-details-open-desktop.png` | `02-home-details-open-phone.png` |
| 03 | `/?cmp=reo-poe,tapo-d230,ring` compare, 3 ticked | `03-home-compare-desktop.png` | `03-home-compare-phone.png` |
| 04 | `/` filtered to 0 rows (empty state) | `04-home-filtered-empty-desktop.png` | `04-home-filtered-empty-phone.png` |
| 05 | `/` dark mode | `05-home-dark-desktop.png` | `05-home-dark-phone.png` |
| 07 | `/subfree-uk/does-not-exist` (404) | `07-404-desktop.png` | `07-404-phone.png` |
| 08 | `/` photo lightbox (Reolink PoE) | `08-home-photo-dialog-desktop.png` | `08-home-photo-dialog-phone.png` |

## Routes not captured, and why

- **06 `/doorbells.html`:** skipped because it is a byte-identical copy of `/`, so it would duplicate 01.
- **Not present on the site:** search, newsletter or sign-up, about, privacy or terms, category pages, per-product pages (details are inline rows, see 02), a custom 404 (GitHub's default is served, see 07), and any dev or admin pages.
- **Known capture artefact, not filed:** in the 03 full-page shots the sticky compare bar sits mid-page. That is how a full-page capture renders a sticky element, not a layout bug.

## Severity key

- **P1:** blocks the main task (choosing a doorbell) or undermines trust in the numbers.
- **P2:** worth fixing; costs the visitor time or confidence.
- **P3:** polish.

## Top 3

1. The default sort is by a figure no column shows, so the list looks mis-sorted (Ring at £79.99 sits below Arlo at £200.06, and Nest at £179.99 sits below Hikvision at £305).
2. On a phone, the side-by-side compare cuts off the third product (Ring here) with no sign that the table scrolls.
3. The intro promises "each one links to its source", but no row or price links anywhere: the only links are tiny footnote numbers inside Details.

## Tasks

### 1. Show the sort figure so the list order makes sense
- **Severity:** P1
- **Screens:** 01, 03, 05 (desktop and phone)
- **Problem:** The default "Sort by: 3-year cost to keep recordings" uses a figure that no column shows, so Ring (£79.99, "no recordings") sits below Arlo at £200.06, and Google Nest (£179.99, "3 hrs history") sits last, below Hikvision at £305, and the list reads as broken.
- **Task:** Add a visible "3-year cost to keep recordings" value to each row (or bold whichever of the two 3-year cells the sort uses), and add a one-line note under the sort control saying which figure the order follows.
- **Expected benefit:** Visitors can trust the ranking at a glance instead of thinking the cheapest doorbells were sorted wrongly.

### 2. Make the phone compare table show all three products
- **Severity:** P1
- **Screens:** 03 phone
- **Problem:** In "Side by side" on a 390 px screen, only Reolink PoE and Tapo D230S1 fit; the Ring column (the one to avoid) is cut off mid-word ("The microSD car", "hub's") with no scroll hint.
- **Task:** On phones, stack the compare as one card per attribute with three short values beneath it, or pin the label column and show a clear scroll cue (edge fade plus "Swipe to see Ring"); shorten the label column so it does not take a third of the width.
- **Expected benefit:** Phone visitors can actually compare the three doorbells they picked, including the one that costs most.

### 3. Give every product a visible link to its price source
- **Severity:** P1
- **Screens:** 01, 02 (desktop and phone)
- **Problem:** The intro says "each one links to its source", but product names and prices are plain text and the only links are "Sources 13, 14, 16" in small type at the foot of the open Details panel, which jump to a 52-item list.
- **Task:** Make each row's price (or a small "Check price at Reolink UK" link under it) open the retailer or manufacturer page the price came from, and label the Details source links by name ("Reolink UK store") instead of by number.
- **Expected benefit:** Visitors can check a price or go to buy in one tap, and the site's no-affiliate promise is visibly kept, which strengthens trust.

### 4. Explain the "3 years, cheapest" compare row
- **Severity:** P2
- **Screens:** 03 desktop and phone
- **Problem:** The first compare row shows "£79.99 · cheapest", "+£15.00" and "+£179.64", but nothing says that Ring's +£179.64 uses its with-plan cost because it cannot record without one.
- **Task:** Rename the row to "Cheapest way to record for 3 years" and show each absolute total with its basis in small text ("£259.63, with Ring plan"), keeping the difference as a secondary figure.
- **Expected benefit:** Visitors understand the true cost gap between their shortlisted doorbells without having to work it out from the rows below.

### 5. Tell the visitor which filter emptied the list
- **Severity:** P2
- **Screens:** 04 desktop and phone
- **Problem:** With the price slider at £40 to £40 the two thumbs overlap into one and the track turns grey, and "Nothing matches those filters" does not say that price is the cause.
- **Task:** Name the blocking filter in the message ("No doorbell costs £40 or less. The cheapest match is Reolink PoE at £69.99"), make the suggestion button say what it changes ("Raise maximum to £70"), and show the slider's current range as text above it.
- **Expected benefit:** Visitors recover from a dead end in one tap instead of guessing which control to undo.

### 6. Label and enlarge the compare checkbox in each row
- **Severity:** P2
- **Screens:** 01, 03 (desktop and phone)
- **Problem:** The row checkbox is an unlabelled box about 15 px square on both desktop and phone, and the only explanation is "Tick up to 3 rows to compare" above the table.
- **Task:** Add a visible "Compare" label next to each checkbox and give the box and the "Details" button a tap area of at least 44 by 44 px on phones.
- **Expected benefit:** Fewer mis-taps on phones, and visitors find the compare feature without reading the toolbar line.

### 7. Shorten each product card on phones
- **Severity:** P2
- **Screens:** 01, 02, 05 phone
- **Problem:** Each phone card stacks "3 yrs, no plan" and "3 yrs, with plan" on separate rows beneath a three-column block, so one doorbell takes most of a screen and the 14 cards run to about eight screens of scrolling.
- **Task:** Put both 3-year figures side by side in the same grid as Records free, Price and Free features, and tighten the vertical spacing between label groups.
- **Expected benefit:** Visitors see two or three doorbells per screen and can scan the list much faster on a phone.

### 8. Keep the "why" in the phone short answer
- **Severity:** P2
- **Screens:** 01, 03, 04, 05 phone
- **Problem:** On phones "The short answer" shrinks to "Reolink PoE or Tapo D230S1. Ring needs a plan to record", dropping the reasons and the warning that Blink and Arlo need extra hardware.
- **Task:** Show the same three coloured lines as desktop (best overall, easiest battery, avoid if you won't pay monthly), each kept to one or two lines, above the Filters panel.
- **Expected benefit:** Phone visitors get the full recommendation, including what to avoid, before they have to scroll the list.

### 9. Replace the GitHub default 404 with a branded one
- **Severity:** P2
- **Screens:** 07 desktop and phone
- **Problem:** A mistyped or old link shows GitHub's "File not found" page with "If this is your site..." advice, no link back to the doorbell list, and a page that is not sized for phones.
- **Task:** Add a simple 404 in the site's own style with the heading "Page not found", one line of explanation, and a clear "See the doorbell comparison" button.
- **Expected benefit:** Visitors who land on a broken link reach the comparison instead of leaving, and the site looks maintained.

### 10. Say who runs the site at the foot of the page
- **Severity:** P2
- **Screens:** 01 desktop and phone (end of page)
- **Problem:** The page ends abruptly after "Sources" item 52 with no footer, no named owner and no contact other than "Open an issue" (a GitHub link most shoppers will not use), on a page that tells people which products to buy and avoid.
- **Task:** Add a short footer with who made the comparison and why, a plain contact route (an email address or form), the "Last checked" date repeated, and a "Back to top" link.
- **Expected benefit:** Visitors can see that a real, reachable person stands behind the verdicts, which makes the recommendations more credible.

### 11. Make the column headers readable and explain the footnotes in place
- **Severity:** P3
- **Screens:** 01, 03, 05 desktop
- **Problem:** Headers such as "3 YRS, NO PLAN ᵃ" and "3 YRS, WITH PLAN ᵇ" are about 10 px uppercase grey, and the meaning of the a and b markers sits in "How we worked it out" far below the table.
- **Task:** Raise the header size to at least 12 px, write the headers out ("3-year cost, no plan"), and add a short explanation on hover or tap of each header.
- **Expected benefit:** Visitors understand what the two key cost columns mean without scrolling to the method section.

### 12. Replace the bare dash in "3 yrs, with plan"
- **Severity:** P3
- **Screens:** 01, 02, 03, 05 (desktop and phone)
- **Problem:** Reolink PoE, Aqara G4 and Hikvision show only a dash under "3 yrs, with plan", which could mean missing data rather than "no plan exists" (the Details panel says "No subscription offered or needed").
- **Task:** Show short text such as "No plan offered" in the cell instead of the dash.
- **Expected benefit:** Visitors read the absence of a plan as a plus, not as a gap in the research.

### 13. Explain what the coloured row borders and badges mean
- **Severity:** P3
- **Screens:** 01, 05 (desktop and phone)
- **Problem:** Rows carry green, blue or red left borders and badges ("Best overall", "Easiest battery setup", "Avoid without a plan") but nothing says why some picks are green and others blue, and the meaning relies on colour.
- **Task:** Add a one-line key above the table (green: best without fees, blue: best battery pick, red: avoid without a plan) and keep the badge text as the main signal.
- **Expected benefit:** Visitors, including those with colour-vision differences, understand the verdicts at a glance.

### 14. Highlight differences in the compare table
- **Severity:** P3
- **Screens:** 03 desktop and phone
- **Problem:** "Side by side" lists every attribute in the same plain text, so Ring's "No" for "Records free?" and "None" for "History, no plan" look no different from the other products' "Yes".
- **Task:** Reuse the list's records-free markers and red text for paywalled or missing features in the compare cells, and add an option to hide rows where all three values match.
- **Expected benefit:** Visitors spot the deciding differences between their three picks faster.

### 15. Make the disabled checkboxes look intentional at the limit of three
- **Severity:** P3
- **Screens:** 03 desktop and phone
- **Problem:** Once three rows are ticked, every other checkbox fades to a very light grey that looks broken, and the explanation sits only in the bottom tray.
- **Task:** Keep unticked boxes at normal contrast and, on tap, show a short inline message ("You can compare 3. Untick one to swap").
- **Expected benefit:** Visitors know why a box will not tick and how to swap a product.

### 16. Tone down white photo tiles in dark mode
- **Severity:** P3
- **Screens:** 05 desktop and phone
- **Problem:** Product photos sit on bright white tiles that glare against the near-black page, and the grey track of the free-features bar almost disappears.
- **Task:** Give photo tiles a soft light-grey or slightly dimmed background in dark mode and raise the contrast of the free-features bar track.
- **Expected benefit:** Dark mode is comfortable to scan and the feature scores stay readable.

### 17. Show the photo zoom on desktop and make the lightbox easier to close
- **Severity:** P3
- **Screens:** 01 desktop, 08 desktop and phone
- **Problem:** Phone thumbnails show a magnifier badge but desktop thumbnails show nothing, and the lightbox's only visible exit is a small "Close" text link at the bottom right.
- **Task:** Show the magnifier on desktop thumbnails (at least on hover), add a clear close button at the top right of the lightbox, and close it on a tap outside the photo.
- **Expected benefit:** Visitors discover the larger photos on desktop and leave the lightbox without hunting for the link.

### 18. Tidy the wording in the Details panel
- **Severity:** P3
- **Screens:** 02 desktop and phone
- **Problem:** Lines such as "Power: PoE; Wi-Fi: Wired Ethernet" and "Storage: microSD and/or NVR; RTSP/ONVIF" read as raw data, and the desktop panel's two columns of label and value pairs have uneven gaps.
- **Task:** Rewrite values in plain sentences ("Powered by an Ethernet cable, no Wi-Fi needed"), move technical terms such as RTSP/ONVIF into brackets, and align the two columns on a shared grid.
- **Expected benefit:** Non-technical visitors understand each doorbell's setup without decoding jargon.

## Severity count

| Severity | Count |
|---|---|
| P1 | 3 |
| P2 | 7 |
| P3 | 8 |
| **Total** | **18** |
