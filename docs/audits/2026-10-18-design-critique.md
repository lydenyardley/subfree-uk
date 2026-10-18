# Design critique: SubFree UK

Target: [index.html](../../index.html) (identical to `doorbells.html`), reviewed
at 1280×900 and 390×844, light and dark. Date: 18 October 2026.

> ⚠️ DEGRADED: single-context (this harness exposes no design-review sub-agent;
> the only agent available is a web researcher). The design review and the
> detector/browser pass ran sequentially in one context.

Method: source review, rendered DOM and computed layout in Chromium, the
Impeccable detector (34 findings), and axe-core at 390px as a cross-check (0
violations). Screenshots were captured for the lightbox states; the review
below is based on rendered geometry, computed styles, copy and interaction
behaviour, not on a pixel-level viewing of those files.

---

## Design health score

| # | Heuristic | Score | Key issue |
|---|-----------|-------|-----------|
| 1 | Visibility of system status | 3 | Sort state, counts and the sticky tray all report clearly. |
| 2 | Match system / real world | 3 | PoE, NVR, microSD and Home Assistant are used without a gloss. |
| 3 | User control and freedom | 3 | Reset, Clear, Close and Esc all work; no undo needed. |
| 4 | Consistency and standards | 3 | Header sorting and the select stay in sync. |
| 5 | Error prevention | 3 | Three-compare cap disables the rest; no destructive actions. |
| 6 | Recognition rather than recall | 2 | 67 footnote links and a six-column cost comparison ask the reader to hold too much. |
| 7 | Flexibility and efficiency | 3 | Filter, sort, keyboard and the compare tray; state is not shareable. |
| 8 | Aesthetic and minimalist design | 3 | Dense by design, but 10px labels and footnote soup add noise. |
| 9 | Error recovery | 3 | Empty state explains and offers a reset. |
| 10 | Help and documentation | 2 | The method is thorough; there is no glossary and no way to make contact. |
| **Total** | | **28/40** | **Good** (70%) |

The page is close to the top of the "Good" band. The two P1 items below are the
difference between a careful data page and one that works as well on a phone
with a screen reader as it does on a desktop.

## Design specificity verdict

**Authored for this product, not category-interchangeable.** The structure is
the argument: free recording first, hardware price second, three-year cost
third, the catch fourth. A generic review page would lead with a star rating
and a buy button. The verdict rail, the footnote-per-price sourcing, the
"Not yet verified" line and the absence of fonts, scripts or tracking could not
be lifted onto another product unchanged.

The weakness is that the page is a very good data appendix, while the decision
itself lives in one small rail and three rows that all claim "Best overall".
The craft is in the evidence; the next gain is in the decision.

## What is working

1. **The short answer rail.** It answers the title before the table and gives
   the reader permission to stop scrolling. Three verdicts, each with a reason.
2. **Column order and number treatment.** "Records free?" precedes price;
   prices and costs right-align on tabular figures; the score gets a bar and a
   number rather than a colour alone.
3. **Restraint as a trust signal.** No external fonts, scripts or tracking, and
   every row carries its sources and its unverified claims. That is rare in
   this category, where every other page exists to sell an affiliate link.

## Priority issues

### P1. The table header disappears from the accessibility tree on phones

`.main-t thead { display: none }` below 820px removes the column headers from
the accessibility tree, not just from the screen. The visual replacement is a
`data-label` pseudo-element on each cell, which is not a header association and
is not reliably announced. Downstream: a screen reader user on a phone hears
fourteen unlabelled groups of numbers.

Fix: clip the header row instead of removing it, and hide its sort buttons at
that width so they do not become invisible focus stops. Verify with VoiceOver
or NVDA, not only axe. This is the one item that should be fixed before the next
deploy.

### P1. 10px type carries the most important labels

Twenty-one rendered elements sit at 10px: the verdict tags ("Best overall",
"Battery pick", "Avoid without a plan"), the stacked mobile field labels, the
footnote markers, and the column-header superscripts. The detector counts 25
instances. The smallest type on the page is doing the most load-bearing work.

Fix: an 11px floor, 12px for the verdict tags and mobile labels, sentence case
for the tags. The row height has room (106px on desktop; the tag adds no height
because it is already stacked under the model name).

### P2. On a phone, the first product starts below the first screen

Measured at 390×844: the first product row begins at y=984px, after 325px of
always-open filters. The short answer is visible above that, which softens it,
but the table — the reason for the page — needs a scroll and a filter wall
first. Seven controls and five decision points precede any product.

Fix: collapse the filter fieldsets into a "Filters" disclosure below 520px,
keeping Sort and the count visible. Target: first row inside the first viewport.
The desktop layout is fine as it is.

### P2. "Best overall" is on three rows

The tag is applied to all three Reolink variants (`reo-poe`, `reo-wifi`,
`reo-batt`), so the strongest badge in the table no longer distinguishes a
product. The short answer is honest — it names the family — but the row-level
badge is not.

Fix: one "Best overall" on the PoE model, then variant labels ("Best wired",
"Best battery") or a single "Best overall family" treatment on the group. This
is a domain-model change, not a copy tweak.

### P2. Footnote numbers are mixed into prices

Sixty-seven footnote links, several per numeric cell: `£54.99¹²`. In a column of
figures the superscripts compete with the number, and on a phone each card
carries two or three of them at 10px. The full sources already live in each
row's Details panel, so the table is duplicating an affordance.

Fix: one source affordance per row (or per column), and keep the per-cell
numbers out of the numeric columns. The `a`/`b` method markers at the column
heads already do the explanatory job.

## Numbered recommendations

Ordered by impact. Each maps to the Impeccable command that would carry it out.

1. **[P1] Restore header association at ≤820px.** Clip the `thead` instead of
   `display:none`; hide its buttons at that width. Test with a screen reader,
   not only axe. `$impeccable harden`
2. **[P1] Raise the type floor to 11px (12px for verdict tags and mobile
   labels).** Sentence-case the tags. Re-run the 24px target check afterward.
   `$impeccable typeset`
3. **[P2] Put the first row in the first phone screen.** Collapse the filters
   into a disclosure below 520px and keep Sort plus the count. `$impeccable adapt`
4. **[P2] Give one product one title.** Differentiate the three Reolink rows so
   "Best overall" is singular, and say which use case each variant wins.
   `$impeccable clarify`
5. **[P2] Take footnote numbers out of the price and cost cells.** Keep one
   source affordance per row; the Details panel already has the full list.
   `$impeccable distill`
6. **[P2] Add a contact route.** "Tell us and we'll fix it" has no link. Add a
   mailto or a GitHub issue link in the method section and the meta line.
   `$impeccable harden`
7. **[P3] Cap the dek measure.** The dek is 744px at 18px (about 86 characters
   per line) while body copy is 65ch. Give it the same cap. `$impeccable layout`
8. **[P3] Make zoom discoverable.** The dialog works (Esc, backdrop, focus
   return), but `cursor:zoom-in` is invisible on touch. Add a small expand glyph
   to the thumbnail on hover and focus. `$impeccable delight`
9. **[P3] Soften the dark-mode photo mats.** Thirteen pure-white rectangles are
   the brightest surfaces on a #151514 page. A light neutral mat or a hairline
   border keeps the cutouts legible without the glare. `$impeccable colorize`
10. **[P3] Gloss the jargon once.** PoE, NVR, microSD and Home Assistant appear
    in the verdict and the table without a definition. One line in "How we
    worked it out" would carry a first-time reader. `$impeccable clarify`
11. **[P3] Give the "No photo" placeholder breathing room.** The label sits
    flush against its 45×60 border; a 0.5rem inset (on the existing scale) fixes
    the two detector hits. `$impeccable polish`
12. **[P3] Run axe at 390px and 820px as well as 1280px.** The audit catches
    desktop issues only today, which is how item 1 shipped. Two more passes are
    cheap and close the blind spot. `$impeccable audit`

## Persona red flags

**Jordan, first-timer.** "Records to a card or NVR" and the "Local / Home
Assistant" filter both assume knowledge. Jordan will understand "no
subscription" and "£54.99", then stall on PoE and NVR. The three verdicts help,
but the vocabulary does not meet him halfway.

**Sam, screen reader / keyboard.** On desktop, every detail row, sort header and
compare control is keyboard-reachable with a visible focus ring. On a phone,
the header row leaves the accessibility tree (P1 above), and 15px checkboxes
depend on the spacing exception rather than a larger control.

**Casey, one-handed mobile.** The page is 7,525px tall at 390px; the first
product is below the fold; the filter block is 325px of always-open controls;
the photo zoom target is 45×60 with no visual cue. The compare tray sits in the
thumb zone once it appears, which is the right call.

## Detector results

Impeccable 4.5.0, `detect --json index.html`, exit 2, 34 findings:

| Count | Rule | Verdict |
|-------|------|---------|
| 25 | `undersized-ui-text` | Valid. Recommendation 2. |
| 4 | `side-tab` | **Intentional.** The 3px left rule encodes the verdict colour (best/battery/avoid) on the verdict rail and each tagged row. It is data, not decoration. Keep. |
| 2 | `cramped-padding` | Valid but minor. Recommendation 11. |
| 1 | `all-caps-body` | Valid, same fix as recommendation 2 (sentence-case the tags). |
| 1 | `monotonous-spacing` | **False positive.** The page uses a strict 1rem rhythm by design; 32 of 45 spacing values are 1rem. That is the system, not a failure to vary. Keep. |
| 1 | `aphoristic-cadence` | **False positive.** The hit is "No affiliate links, no tracking, no cookies" — a trust list, not a rhetorical tic. Keep. |

The detector also caught an `<img>` with no `src` in the new lightbox. That was
a real defect and is fixed: the image element is now created on first open.

## Minor observations

- Heading order is clean: one h1, then h2s for the short answer, the method and
  the sources.
- The 3px verdict stripe on the first cell is subtle, but it is the only
  colour cue that survives when the row is scanned quickly. Do not remove it
  while removing the side-tab detections above.
- The sticky table header and the sticky compare tray never collide because the
  tray only exists while rows are selected.
- The compare table keeps its header row on phones (it scrolls horizontally),
  so the P1 header problem is specific to the main table.
- The dark palette is duplicated in the media query and the `data-theme` block.
  That is a maintenance risk rather than a design one, and was called out in an
  earlier review.

## Run notes

- Target slug: `index.html` (resolved by path; `doorbells.html` byte-identical).
- Ignore list: none (`.impeccable/critique/ignore.md` does not exist).
- Assessment independence: **degraded**, as declared at the top. The design pass
  and the detector pass were sequential in one context.
- CLI detector: available, 34 findings, exit 2. Broken-image finding verified
  and fixed during the run; the count above is the post-fix run.
- Browser: Playwright Chromium, 1280×900 and 390×844, light and dark, against
  the running dev server on `localhost:8123`. No new server was started.
- Browser overlay: not injected. The CLI scan was the evidence path; no
  user-visible overlay was claimed.
- Axe cross-check at 390px: 0 violations. It does not detect the `thead`
  removal, which is why that item is a manual/AT finding.
- Cleanup: detector JSON and temp files removed; lightbox screenshots remain in
  the git-ignored `screenshots/` directory for a human pass.
- Questions skipped: the request scoped this run to the written critique and its
  numbered recommendations, not to choosing an implementation plan.
