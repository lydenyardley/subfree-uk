# Route critique, 7 November 2026

This document contains a visual and interaction critique of every non-development route in the project: the doorbells, cameras, smart rings, printers, 404 page and legacy redirect. The four comparison pages were inspected in Chromium at desktop and phone widths. The generated 404 and alias were read in the browser and in source. The user asked to run `/impeccable critique`, but the `impeccable-critique` skill is not available through the skill loader and the `impeccable` CLI is not installed. This is an independent manual critique, not a claim that the Impeccable detector or live overlay ran.

## Scope and method

- Routes reviewed: `/`, `/cameras/`, `/rings/`, `/printers/`, `/404.html`, and `doorbells.html`.
- Browser sizes: 390×844 on each route; 1440px desktop screenshots on doorbells and cameras, with the desktop comparison behavior tested on doorbells. Route-specific mobile first-row positions were measured after a fresh load. The three-model comparison was scrolled to 2,200px in the document.
- The full `python build/check.py` passed all 97 checks. It includes WCAG axe checks on the root route, but the route-specific browser test does not repeat axe on all category pages.
- The local browser could not resolve `gc.zgo.at`, so an external resource failure appears in preview logs. This is caused by the environment's DNS failure and is not evidence that the production counter is broken.
- This report numbers active findings only. Earlier audits are recorded in `docs/audits/2026-10-28-design-critique.md` and accepted design decisions. Repeated or explicitly declined ideas are called out below instead of counted as new findings.

## Route-by-route overview

| Route | Desktop impression | Phone first product top | Observed state |
|---|---|---:|---|
| Doorbells `/` | Dense comparison ledger with a clear decision rail | 615.0px | A useful part of the first card appears on the first phone viewport |
| Cameras `/cameras/` | Same visual language, distinct product-specific verdicts; long desktop heading and rail remain legible | 645.3px | A portion of the first camera card appears on the initial phone viewport |
| Smart rings `/rings/` | Same visual language; membership facts sit beside the scores and costs | 633.2px | First ring card begins in the lower half of the initial phone viewport |
| Printers `/printers/` | Same visual language, with a longer five-line decision rail | 754.5px | About 90px of the 477.8px first card is visible at 844px |
| 404 `/404.html` | Minimal text-and-links recovery page | N/A | Browser-default serif body font; no shared category/theme controls |
| Legacy alias `doorbells.html` | Immediate meta-refresh and one fallback link | N/A | 487 bytes; intended as a redirect, not a full page |

The camera, ring and printer pages share the comparison design. Their category-specific copy changes the density. The 404 and alias have deliberately smaller scopes, but the 404 is less visually integrated than the comparison pages.

## Numbered findings

### 1. [P1] Desktop comparison columns lose their names during long scrolls

**Evidence.** At 1440px, the three-doorbell comparison table was 961px tall. Its model headers are `position: relative` in `build/page.css:335,345`. After setting the page scroll position to 2,200px, the header top was −1,566.6px relative to the viewport. Only the spec column is sticky at phone width (`build/page.css:585-586`).

**Why it matters.** At the point where a reader compares a lower specification, the model names and badges have scrolled away. The reader has to remember which column is Ring, Reolink or Arlo. This is especially costly after column rearrangement.

**Design direction.** Keep model identity available while scrolling the comparison without adding a large second header band. The October 28 critique already named this concern. It remains present in the current CSS and this run reproduced the header position directly.

### 2. [P2] Printer advice uses more of the first phone screen than the other categories

**Evidence.** At 390×844, the printer route's `.vshort` block is 182px high and carries five product recommendations or warnings, versus 72.8px on cameras and 91px on smart rings. The first printer row starts at 754.5px. The first printer card is 477.8px tall, so only about 90px is visible in the viewport. On fresh 390×844 loads, the doorbell route starts its first row at 615.0px, cameras at 645.3px, and smart rings at 633.2px.

**Why it matters.** Printer advice is useful and specific, but its prominence pushes the actual products below most of the first screen. This is category-specific content density, not a shared CSS failure.

**Design direction.** Preserve the useful printer trade-offs while reducing the first-screen weight. Consider separating extra printer-specific notes from the short recommendation surface or progressively revealing detail, then check that a user can still reach the relevant model and cost quickly.

### 3. [P3] The phone first-paint gate does not require enough of a product to be visible

**Evidence.** `build/checks/structure.py:79-100` passes when the first row's top is less than or equal to the viewport height. It therefore permits a row beginning at y=843 in an 844px viewport, even though almost none of the product is visible. Fresh route loads in this review started the first row at y=615px for doorbells, y=645.3px for cameras, y=633.2px for rings and y=754.5px for printers.

**Why it matters.** The check can pass after later content changes push nearly the whole first product below the fold. Its current condition proves that the row begins on screen, not that a visitor can engage with a result.

**Design direction.** Measure a useful visible portion of the first product card at realistic mobile heights. Keep the check data-driven and load each route at phone width before measuring so responsive initialization runs.

### 4. [P2, unconfirmed] The desktop doorbell short-answer rail may be clipped at the right edge

**Evidence.** The 1440×1000 screenshot of `/` showed long short-answer lines continuing beyond the right edge of the captured image. The desktop aside measured x=888 to x=1407 in a 1440px browser, leaving 33px before the viewport edge. The camera and printer aside also use long recommendation copy.

**Why it matters.** The short answer is the page's top-level recommendation. If a line is clipped rather than wrapped, readers may miss the end of the reason or price.

**Confidence and limitation.** This is screenshot-based, not confirmed. The aside fits the measured document box and the document has no horizontal overflow. The browser panel may have cropped the capture. Do not change the layout until this is checked in a full-width browser.

**Design direction.** Verify the rail at a true 1440px viewport. If text is genuinely clipped, allow it to wrap or adjust the column width. If the browser panel caused the appearance, close this finding.

### 5. [P2] The 404 page's typography and shell differ from the comparison pages

**Evidence.** `/404.html` loads the site CSS, but Chromium computed its body font as Times New Roman at 390px. The page has the shared logo and recovery links, but no category menu or theme control. Its root-relative recovery links point to `/subfree-uk/...`, which is correct for the project's GitHub Pages base path.

**Why it matters.** A reader arriving at a dead URL gets a visibly different shell and cannot switch theme or use the normal category disclosure. The links do recover the reader to each comparison, so the issue is consistency and navigation affordance rather than a dead end.

**Design direction.** Treat the 404 as a route in visual review. Reuse only the parts of the shared shell that improve orientation, and ensure its typography is intentional. Keep its narrow recovery task rather than turning it into another full comparison page.

### 6. [P3] The legacy redirect should remain an intentional low-content exception

**Evidence.** `doorbells.html` is 487 bytes and sends an immediate meta refresh to `./`, with a fallback link and canonical URL. The `generated alias` check verifies that it remains a small redirect rather than a second product page.

**Why it matters.** The redirect does not share the main site's typography or controls, but adding them would duplicate UI for an address whose job is to forward old links.

**Design direction.** Keep the small redirect unless it stops forwarding on a supported host. This is a deliberate exception, not a request to redesign it.

### 7. [P3] Route-specific visual and accessibility review is thinner than root-route review

**Evidence.** The full audit runs its primary mobile, desktop, axe, comparison, keyboard and print checks on the doorbell route. `category.py:page_behaviour()` opens each non-root route at 1280px and checks row count, price sorting, compare open, a source card, assets and console. It does not run the same full 390px review or axe matrix for every category. The four pages rendered at both inspected widths, and their measured horizontal document widths were within their viewports.

**Why it matters.** The printer route's longer short answer is one category-specific content effect that a generic root-only gate does not express. This audit found no confirmed WCAG failure on the other routes, but those routes have less automated coverage.

**Design direction.** Add small, data-driven route checks where content length or category-specific behavior differs. Reuse property-based fixtures and the category registry rather than pinning model names or counts.

## Existing findings not repeated as new

The October 28 critique already called out selection colour, a score-source card, short-answer presentation, a back-to-top overlap, source-card typography, the coloured side-rule count, comparison labels, reorder affordance, filter disclosure, phone catch placement and differences-only wording. Several items are documented as declined or reverted in accepted decisions. This report does not relabel those as new findings. The comparison-header concern is repeated only because the live behavior remains present and was measured again.

## Impeccable status

The `/impeccable critique` skill was not available from the configured skill loader. `command -v impeccable` found no installed CLI, and the `.impeccable/` project configuration directory is absent. The Impeccable detector scan and its overlay were therefore not run. The findings above come from manual Chromium inspection, route/source reading, and the stated measurements. No detector finding count is implied.
