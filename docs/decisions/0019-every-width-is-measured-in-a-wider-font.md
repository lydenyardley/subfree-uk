# 19. Every desktop width is measured in a wider font

- Status: Accepted
- Date: 23 October 2026
- Source: the owner's review of 23 October 2026: a layout break like the 901px
  catch must not reach CI unnoticed.

## Context

The tracks are fixed pixels, so a fallback font about 15% wider than Arial
moves words while every box reports fit. ADR 13's defect was exactly that: at
821 the catch's words ran 51px past the chevron's left edge while the cell
reported no overflow. The sources check already widens `--sans` to Verdana for
one measurement, but the rows were only ever measured at the machine's font,
and CI's DejaVu is not the local Segoe UI.

Measured today at Verdana, the catch holds at every desktop width. Its ink ends
10 to 13px left of the chevron at 901, and the band's catch reads in one line
at 821 and 900.

## Decision

`desktop rows` judges each of its ten widths twice: once at the page's own
`--sans`, then with `--sans` set to `Verdana, DejaVu Sans, sans-serif`. The
second pass runs every existing assertion and names itself in the message, as
in "at 900px under the wider fallback the catch in m-tapo-td21 still reads in
10 lines".

The widths now include 1200, 1199 and 1101, the edges the record track and the
cost columns are set at. The compare box's new 40px track, the footnote
marker's place and the catch's clearance are all measured in both fonts.

## Verification

A probe that cuts the catch's text box to 60px fails the check at 900 and 821,
with two of its four findings from the wider pass:

```
Result: FAIL, 4 issue(s)
  - at 900px the catch in m-tapo-td21 still reads in 10 lines
  - at 821px the catch in m-tapo-td21 still reads in 10 lines
  - at 900px under the wider fallback the catch in m-tapo-td21 still reads in 12 lines
  - at 821px under the wider fallback the catch in m-tapo-td21 still reads in 12 lines
```

## Limits

The catch's line count above the band is measured but not capped. At 901 it
reads in 8 to 11 lines at this font and 10 to 12 at Verdana, which is the width
ADR 13 deliberately left it: the band stops at 900 because that is where the
catch stops painting under its chevron. A cap there would be a number about the
copy rather than the layout. What the pass does assert at those widths is
clipping, table overflow, the footnote's place and the record track, and it
asserts them in both fonts.

## Consequences

- A layout that only breaks under a wider fallback now fails the audit on any
  machine, not only the one whose font is wider.
- `desktop rows` measures every width twice, so it runs about twice as long.
- The pass is the second use of the same widen-the-variable probe; the sources
  check remains the first, because it has its own column and its own words.
