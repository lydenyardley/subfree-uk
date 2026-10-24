# 22. The critique's fifteen findings

- Status: Accepted, all fifteen findings settled
- Date: 24 October 2026
- Source: the 23 October critique (`docs/audits/2026-10-23-critique.md`) and the
  owner's dispositions of 24 October: implement R2, R3, R4, R7, R8, R9, R10,
  R11, R12, R14 and R15; show R5 and R13 as a mockup; reject R6. R1 was not
  taken. The owner then took R5's alignment without its verdicts, and R13 as
  drawn.

## Context

The critique measured the page at 1280px and 390px, light and dark, with the
comparison open, and found fifteen things worth changing. Eleven of them are
about the reader being able to check a claim, compare two numbers, or hit a
control; the rest are polish. This record says what changed, why, and which
check holds each one.

## Decision

| Item | Change | Held by |
|---|---|---|
| R2 | The cue names the first column with less than 60% of itself showing, and the columns snap one per model. At 390 the second model is 58% visible at rest and the third is off the edge; the cue named the third. | `comparison scroller`, `compare markers` |
| R3 | The doorbell table is captioned "Doorbell comparison: 14 models, 8 columns" and the skip link says "Skip to the doorbell table". | `table name` |
| R4 | The row's toggle is a bordered "Costs & sources" button, 44px tall, on its own line under the catch. The panels are hidden by the `js` class instead of the `hidden` attribute, so a reader without JavaScript gets all 14 open (8,651px tall at 1280, 13 spec pairs each) instead of none. | `details hit area`, `desktop rows`, `no JavaScript` |
| R5 | The reserved badge line only: every compare column leaves the same 19px for a verdict, written or not, so the three photos start at 120px at 1280 where the column without one started at 101. The verdict for every row was proposed and declined, because it makes the page recommend all fourteen models, and some have nothing to win. | `compare photos` |
| R6 | Rejected: see below. | — |
| R7 | The comparison uses the table's own words ("3-year cost, no plan") and "cheapest of these 3"; the row note reads "cheapest for this model: with plan". | `compare words`, `compare cost row` |
| R8 | Every delta names its baseline: "+£25.00 more than TP-Link Tapo TD21", with the brand words "Video Doorbell" dropped because every brand here has one. | `compare cost row`, `compare words` |
| R9 | The compare label is 44x44 at every width, not only on a phone, so the compare track is 47px: 44px of target plus the 3px verdict rule that sits in the same cell. | `compare target`, `desktop rows`, `row rule` |
| R10 | A range collapsed to one value reopens from the pointer: a click right of the handles moves the maximum, a click left moves the minimum. | `price slider` |
| R11 | The empty state's two recovery actions sit in a 12px-gapped row instead of one space apart. | `empty result` |
| R12 | A phone keeps a tagline ("No subscriptions") where the full remit is dropped, and the count line says "doorbells", not "rows". | `mast remit` |
| R13 | Twelve pairs in two columns of six, the score breakdown across the foot under a hairline, and the sources under the photo, filling the blank grid it left. | `details panel` |
| R14 | The two photo buttons on a row are named "View <model> photo" and "View <model> photo full size". Neither claims to open a thumbnail: both open the full-size image. | `photo names` |
| R15 | The masthead sits inside `<header class="mast-head">`, with the intro beside it rather than in a header of its own. | axe `region`, `axe WCAG` |

## The filter row, after the review

The critique did not raise it, but the owner's follow-up did: between 821 and
1200 the sort control sat at the far end of the band under the price slider,
reading as a caption for it, with the count stranded at the other end and about
90px of empty space between them.

The filters keep their own line there. The sort now opens the second line under
the option groups, its label inline with the select, and the count closes that
line at the right. Measured at 821px in the page's font and again at Verdana:
the control block is 206px tall against 232 before, the sort starts at the
filters' left edge, and neither the count nor the note overlaps the select.

## The two columns, and the third copy of the range

R13 changes the panel from seven pairs left and six right, ending 77px apart,
to six and six with the score breakdown, the longest pair, across the foot. The
sources move into the figure, under the photo, where 240px of image left
nothing for them: they now wrap in the 180px column instead of taking a line of
their own below both columns.

| Width | Columns end | Panel |
|---|---|---|
| 1440px | 1,138 / 1,061 → 1,077 / 1,077 | 422 → 341px |
| 1280px | 1,219 / 1,142 → 1,158 / 1,158 | 463 → 402px |
| 1101px | 963 / 866 → 861 / 861 | 585 → 463px |
| 900px | one column | 804 → 771px |
| 821px | one column | 825 → 791px |

The foot exists only where there are two columns. Below 1101px the panel is one
list, and the rule that moves a pair to row 7 put the score breakdown halfway
up it; it is scoped to the two-column layout, and `details panel` reads the
rows' order at 900px as well.

The price column printed its range a third time, under the label and above the
slider, where the two labels beneath the slider already say it. It is gone, and
`price slider` fails if the column repeats the figures anywhere but those two.
The controls row is 159px at 1440 and 1280 and 206px at 1101 and below, in both
versions, so no page height moved.

## Rejected

- **A verdict on every row (R5 as proposed).** Fourteen verdicts make the page
  argue for every model on it, and a verdict that names the case a row wins has
  nothing to say about a row that wins none. The alignment does not need the
  words, so the words were dropped and the line kept.
- **R6, a real select-all.** The header's ticked-box glyph is decorative and a
  click does nothing. Making it a select-all means a fourth selection, the
  three-model cap and its refusal message, and a control whose state has to
  track three boxes in two views. The word "Compare" is already the column's
  caption for a screen reader, and the boxes are 44px targets. The page does
  not need a bulk action for fourteen rows.
- **Naming the row's photo "thumbnail".** It opens the full-size image, so the
  name would be false. The pair says which photo the reader is on instead.
- **Saying "vs Reolink PoE" in the compare row's header.** The baseline changes
  with the selection, and the header is one cell for three columns.
- **A 60% cue without the snap.** The snap is what makes the named column the
  one a swipe lands on; without it the cue tells the reader about a column they
  may never reach.

## Consequences

- `desktop rows` gained the load-state assertion: no costs-and-sources panel is
  open until one is clicked. The first version of R4 hid the panels by class
  alone and `.main-t tr.detail{display:block}` beat it on specificity, so all
  fourteen printed open at 821px and wider and the page was 9,639px tall at
  1280 instead of 3,359.
- `photo names` now asserts the details photo says it is full size, rather than
  that one name says "thumbnail".
- `filters row` asserts the sort's line: flush with the filters' left edge,
  the count on the same line, no overlap, one row per option group from 900px,
  and the slider's floor.
- `compare photos` fails when the three photos' tops differ or a column's
  badge line is not the height of a written one; on the old markup it reports
  101px, 120px and 101px.
- `details panel` now holds six pairs a column, the foot pair spanning the
  grid, the sources inside the figure, and the rows' order at 900px, where the
  one-column list must end with the score breakdown.
- `docs/audits/2026-10-23-critique.md` is pruned to the findings and their
  measured evidence; the fix for each is here. The mockup it pointed at is
  deleted, because both proposals are now the page.
- axe's best-practice findings still print as notes, except `region`: every
  element must sit inside a landmark, so that one now fails the run rather
  than printing. The README says so.
