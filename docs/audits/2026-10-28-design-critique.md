⚠️ DEGRADED: single-context (the only sub-agent exposed is a web researcher,
which cannot read local files, run the detector or drive the page)

# Design critique, 28 October 2026

The second pass over the page, run after the technical audit. It removes every
finding already listed there and numbers the design recommendations from 1.

## Method

Target: `index.html`, the built page, served at `http://127.0.0.1:8137` and
inspected in Chromium at 1440, 1280, 390 and 320px, in both themes, with the
details panel, the source card and the comparison open.

Deterministic scan: `impeccable detect --json index.html`, exit 2, 14 findings
across five rules. Browser evidence: direct DOM measurement and screenshots,
listed under each finding. Detector findings that were judged false positives
are named in the specificity section rather than turned into work.

This run did not inject the detector's live overlay. That needs the bundled
live server and a mutable script injection, and the review used the CLI scan
plus measurements in the page instead. The fallback signal is the scan itself.

## Design health score

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of System Status | 4 | Filter count, live announcements, the tray, the card's checked date. Nothing to fault |
| 2 | Match System / Real World | 3 | "3-year cost to keep recordings" is excellent; "Free features 5/8" is an invented unit with no legend at the point of use |
| 3 | User Control and Freedom | 3 | Reset, clear, close, Escape and a share link all exist; the card's focus return fails when its row is filtered away (audit R16) |
| 4 | Consistency and Standards | 3 | Figure links open cards, "Costs & sources" opens a panel, and two different close idioms sit in the comparison and the dialogs. "Differences only (2 identical)" means matching rows, not identical models |
| 5 | Error Prevention | 3 | The compare cap refuses a fourth box and says why; the nearest-match recovery is good; no destructive action anywhere |
| 6 | Recognition Rather Than Recall | 3 | Column headers carry their footnotes; the score's scale lives 14 rows below the first "5/8" |
| 7 | Flexibility and Efficiency | 3 | Sort, filters, URL share and keyboard column reorder; no shortcuts, which is right for the audience |
| 8 | Aesthetic and Minimalist Design | 3 | Ordered and dense in a good way; ten coloured side rules and four competing greens make the page louder than its argument |
| 9 | Error Recovery | 4 | The empty state names the filter that emptied it and offers the nearest match in one tap; the copy failure message is plain |
| 10 | Help and Documentation | 3 | Method, glossary and per-figure cards; no help at the one figure that has no card |
| **Total** | | **32/40** | **Good** |

## Design specificity verdict

**Authored, not interchangeable.** The identity is the argument, not the
decoration. A page that compares what survives without a subscription, and
prices that survival over three years, could not be an unrelated product with
the nouns swapped. The ledger table, the serif display and the three verdict
colours support that argument. They are a system, so a second category can
inherit them, which is what the audit's R18 to R21 are about.

**Deterministic scan.** 14 findings. Ten are `side-tab`, the coloured left rule
on verdict lines, the phone short answer and the card's sentence. One is
`flat-type-hierarchy`, measured by the detector as h3 12px, h2 13px and body
14px with a 1.08 step.
One is `all-caps-body`, 40 characters of uppercase, which is the comparison's
row labels. One is `aphoristic-cadence`, three short rebuttal sentences. One is
`icon-tile-stack`, a 36px tile above an empty heading.

**Judgement on the scan.** `side-tab` is a real overuse here, not slop in the
detector's sense, because the rule is a deliberate editorial device, but ten of
them is too many. `flat-type-hierarchy` and `all-caps-body` are true. The
`aphoristic-cadence` hit is a false positive. "No affiliate links, no tracking,
no cookies" is a factual trust signal on a page whose entire claim is
independence, not a manufactured contrast. `icon-tile-stack` is a false
positive, because the 36px box it matched is the dialog's close button, not an
icon above a feature heading.

## Overall impression

The strongest thing on the page is that every number can be opened. The source
card turns a comparison table into something a reader can audit, and that is
rare. The weakest thing is the comparison view, which loses the names of the
three models as soon as the reader scrolls to the rows that decide between
them. The second weakest is the score, the one figure with no card behind it.

## What is working

The table's information design. One row per product, the 3-year figure that
the sort follows set bold, the catch in words at the right edge, and the price
as a link. A reader can answer "what does this cost me over three years" with
one horizontal scan.

The phone card. The label-and-value grid keeps the table's words, the two
3-year figures share a row, and the compare box carries its own caption. It is
a genuine re-composition rather than a shrunken table.

The provenance card. It opens from the figure, prints the sentence, the
arithmetic, the page and the date, and hands focus back. It is the feature that
makes the rest of the page believable.

## Priority issues

### [P1] The comparison loses its column headers when it is scrolled

**Why it matters.** Eighteen spec rows is about two screens. At the row that
decides between three products, the reader has no model names on screen. The
main table already solves this with a sticky header; the comparison does not,
and the column order can now be rearranged, which makes memory worse.

**Evidence.** `position: relative` on `.cmp-t thead th` (`page.css:299`).
Measured at 1280px with the 14th row in view: the header's top edge is 292px
above the viewport.

**Fix.** Make the comparison header sticky at the viewport top, as the main
table does, with an opaque background and the same 2px rule. Keep the drag
handles in the header so reordering stays available while the header is stuck.

### [P1] The score is the only figure with no source card

**Why it matters.** 5/8 beside 7/8 is the page's own judgement, and it is the
one number a reader cannot open. Its definition sits under "How we worked it
out", 14 rows below the first score, and the card vocabulary has no entry for
it. A reader who wants to know why a product lost a point has to leave the
table and hold the breakdown in their head.

**Evidence.** `CLAIM_WHAT` in `build.py` has six claims, none for score.
`score` has no `data-claim` anchor in the row markup. The details panel prints
the breakdown, but only inside the row's panel, not from the figure.

**Fix.** Add a score claim, with the row's breakdown sentence and the method
page as its source, and let the score in the table open it. This is a new claim
key, so it follows the AGENTS.md rule: add the key, the source and the check
assertion together.

### [P1] The short answer reads as three paragraphs, not a recommendation

**Why it matters.** At 1440 the right rail is the first thing a deciding reader
reads, and it is three paragraphs of 5, 2 and 2 lines of body text with the
product name bolded mid-sentence. The names are links, but they look like text. On the phone the
same content collapses into three tight lines and works better than the
desktop version.

**Evidence.** Screenshot at 1440 light and dark. `.verdict p` is 14px body
text with an inline `<b>` label and a 3px rule.

**Fix.** Give each of the three lines the same shape. A small caps label, the
product as the first words at 16px, then one line of reason, and the avoid line
naming the three products without a sentence around them. Match the phone
version's density.

### [P2] Selection and verdict share one green

**Why it matters.** Ticking a row paints the compare box accent green. The
verdict markers, the score bars, the "records free" squares and the verdict
rules use the same family. A ticked Reolink row shows four greens, and none of
them means the same thing. Selection is state; a verdict is a judgement.

**Evidence.** `accent-color: var(--acc)` on checkboxes, `--v-best` and `--acc`
within a few degrees in both themes. Screenshot at 1280 light.

**Fix.** Make selection neutral, for example a tick in ink on a paper box with
the accent only as a border, and keep green for verdicts. The comparison's
column rule can then stay the only green on a selected column.

### [P2] The back-to-top button covers the end of the main catch

**Why it matters.** The button is fixed at the right edge and appears once the
reader is into the table, which is where the catch column's text ends. The
catch is the sentence that decides between two similar products, and its last
words run underneath the button.

**Evidence.** Measured at 1280×1000. The button is 44px at `right: 1rem`,
`bottom: 4.5rem`, so it occupies 1203 to 1247 by 884 to 928. At scroll 1800
the EZVIZ DB2's catch text box runs 1018 to 1231 by 925 to 965, an overlap of
about 40 by 43px. The Arlo row's catch box overlaps at scroll 2100. It never
covers a control, because the catch buttons sit on their own line at the left
of the column.

**Fix.** Reserve 3rem of right padding on `.catch-t` at widths where the button
is shown, so no line runs under it, or move the button clear of the table's
right edge. Hiding it while a row is open does not help here, because the row
is not the cause.

## Persona red flags

**Alex, the power user.** Ticking three boxes and opening the comparison takes
five interactions, and there is no keyboard path to the compare panel from the
table other than tabbing to the tray. The comparison then loses its headers on
scroll, so Alex has to re-read the first screen to remember the column order.

**Sam, the screen-reader and keyboard user.** The price range announces "40"
and "300" with no currency (audit R14). The tray that says "3 selected" is
outside every landmark, so a landmark jump skips it (audit R15). After a card
is closed with a filter active, focus lands on the body (audit R16). At 200%
zoom the viewport is below 820px, the table header collapses to cards and its
sorting buttons leave the tab order, though the sort select remains.

**Casey, one-handed on a phone.** The card's first screen shows the model, the
price and both 3-year figures, but the "Main catch" is below the fold in every
card. The comparison is a horizontal scroller with a cue that names the column
off the edge, which is the right call. The back-to-top button is in the thumb
zone and covers content.

## Minor observations

The page says "no affiliate links, no tracking, no cookies" once in the meta
line and again in the footer. Say it once, in the meta line, and let the footer
close with the contact route.

The count appears three times above the table, in the h1's dek, the sort row's
count line and the meta line, all saying 14 in different words. Two of them
are doing work. The dek can carry the scope without repeating the number.

An empty result centres its message in a 1440px column, which leaves the
recovery button far from the filters that caused it. Left-aligning the empty
state with the table would keep the fix beside the cause.

## Numbered recommendations

These are new. Items already covered by the technical audit are listed under
the table at the end rather than repeated.

1. **Stick the comparison header to the top of the viewport.** It loses the
   three model names at row 14, and the column order can be changed, so memory
   is not a reliable fallback. (P1)
2. **Give the score its own source card.** It is the one figure a reader cannot
   open, and it is the page's own judgement rather than a vendor fact. (P1)
3. **Rebuild the short answer as three scannable lines.** Label, product, one
   reason, with the product name at 16px and the avoid line reduced to names.
   (P1)
4. **Separate selection from verdict in colour.** A neutral tick for compare,
   green only for verdicts, so a ticked row does not read as four judgements.
   (P2)
5. **Keep the back-to-top button off the main catch.** Reserve right padding on
   the catch text at widths where the button is shown, so no line ends
   underneath it. (P2)
6. **Widen the source card and raise its date to 13px.** The proof surface
   should not be the smallest type on the page. (P2)
7. **Add one real section step.** Section headings are 13px uppercase and the
   body is 15px, so "How we worked it out" and "Sources" read as labels. Use a
   serif section size and keep the eyebrow style for labels inside a section.
   (P2)
8. **Reduce the coloured side rule to the three headline verdicts.** Ten
   instances of the same device, on the verdicts, the phone short answer and
   the card's sentence, dilute the one that matters. (P2)
9. **Move the comparison's row labels to 12px sentence case.** Eighteen
   uppercase labels is the hardest scan on the page. Keep uppercase for the
   table's short column headers. (P3)
10. **Make the column-handle affordance visible before hover.** A one-time
    "Drag to reorder" cue, or grips that appear on header hover and focus, so
    the only reorder path is discoverable. (P3)
11. **Close the filter disclosure by default at every width, with the active
    count in its summary.** It would lift the first row by about 80px and cut
    seven controls from the first screen. (P3)
12. **Put the main catch on the phone card's first screen.** One clamped line
    under the model, with the full sentence in the panel. The catch is the
    reason to choose between two otherwise similar products. (P3)
13. **Rename the differences-only control.** "Differences only (2 identical)"
    is read as two identical models. It counts rows that match across the
    three columns, so "Hide 2 matching rows" says what happens. Update the
    comparison's own assertion in the same change. (P3)

### Already covered by the technical audit, not repeated

| Finding | Audit item |
|---|---|
| Price range announces no currency and has no group name | R14 |
| Tray and back-to-top outside every landmark | R15 |
| Card closes to the body when its row is filtered away | R16 |
| No 320px reflow guard | R17 |
| The score's `/8` is hardcoded in every surface | R2, R18 |
| Check fixtures and copy pinned to this category | R20 |

## Open questions for the next pass

1. **Which comes first, the comparison or the score?** The comparison loses
   its headers on every long view. The score is one unexplained figure. The
   first is a bigger fix; the second is more embarrassing.
2. **Should the short answer stay in the right rail on desktop?** It competes
   with the table for the first screen. Moving it above the table as a single
   line, or into the table as the top three rows, are both defensible.
3. **Is the ledger density the brand?** If it is, the fix for the flat
   hierarchy is one strong section step and nothing else. If it is not, the
   page could take a bolder editorial treatment without losing the data.

## Run notes

- Target slug: `index.html`, resolved from the workspace.
- Ignore list: none. `.impeccable/critique/ignore.md` does not exist.
- Assessment independence: degraded. Only a web-research sub-agent is exposed,
  so both assessments ran in this context. The banner is at the top.
- CLI detector: 14 findings, exit 2, 5 rules.
- Browser visibility: Chromium through the app preview at
  `127.0.0.1:8137`, desktop and phone, light and dark.
- Overlay injection: not attempted. The CLI scan and direct measurement were
  used instead. No user-visible overlay exists.
- Live server cleanup: the static server used for the review was stopped after
  the final measurement.
- Persistence: the archive for this run is this file, as requested, instead of
  `.impeccable/critique/`.
- Questions: three are listed above, tied to the findings. They are options for
  the next pass, not a blocker for this one.
