# 21. A phone's two 3-year figures share a row

- Status: Accepted
- Date: 23 October 2026
- Source: the owner's review of 23 October 2026: the two 3-year figures should
  align without the reserved caption line that leaves an empty gap.

## Context

The two 3-year costs sit side by side in the third row of a phone card, each
under its own label. The labels are "3 years, no plan" and "3 years, with
plan", and they do not wrap at the same width: below about 405px the shorter
one fits a line while the longer takes two, and below about 340px both take
two. Since the figure follows its label, the two numbers started on different
lines in between.

ADR 15 answered that by reserving two label lines for both cells with
`min-height:2.6em`. It worked, and it left a 15.6px gap between the shorter
label and its figure, on every card, at every width where that label fit one
line.

## Decision

The two cells are two-row subgrids of the card. The label sits at the bottom
of the first row and the figure at the top of the second, so the two figures
always start on the same line, and a label that wraps takes its extra line
from the space above itself instead of pushing its figure down.

```
.main-t td.c-nosub,.main-t td.c-sub{display:grid;grid-template-rows:subgrid;padding:0}
.main-t td.c-nosub .figv,.main-t td.c-sub .figv{display:block;grid-row:2}
.main-t td.c-nosub::before,.main-t td.c-sub::before{grid-row:1;align-self:end;margin-top:0.5rem}
```

A text node cannot take a grid row, so the figure is wrapped in
`<span class="figv">`, which is `display:contents` on a desktop and therefore
invisible there. The label keeps its 8px of space above it as a margin,
because the cell no longer has the padding to sit in. The score and the catch
each move down one row.

## Measurements

Chromium at 390, 414 and 320, all 14 cards:

| Width | Label heights | Figures start | Cards |
|---|---|---|---|
| 390px | 15.6 and 31.2px | 772 and 772px | aligned |
| 414px | 15.6 and 15.6px | 756 and 756px | aligned |
| 320px | 31.2 and 31.2px | aligned | aligned |

At 390 the card is 363px tall before and after, because the row was already as
tall as the wrapping label; what moved is the 15.6px of empty space, from
between the short label and its figure to above the label. On a desktop the
wrapper contributes no box: with the same comparison open, the page is 4,181px
at 1280 before and after.

## Rejected

- **Keeping the reserved line.** It is the gap the review asks to remove.
- **Forcing both labels onto two lines.** A width cap on the label or a break
  in its text fills the gap with a second line, but it keeps every card as tall
  as before at every phone width, and a wider fallback font can still split
  the longer label again.
- **Bottom-packing each cell.** With `justify-content:flex-end` the figure's
  position depends on the note under it, so a row with a note on one side only
  would misalign the pair.
- **Positioning the label absolutely.** It removes the label from the cell's
  height, so the two cells would no longer share the row that aligns them.

## Consequences

- `labels` asserts the two figures start on the same line at 390, and
  `desktop rows` still asserts the two cells share a row and that a phone card
  has three tracks.
- The phone spec cells are no longer all block rows: the two 3-year cells are
  grid containers, and `labels` now accepts either.
