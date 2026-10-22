# 11. The sources keep the working in sight

- Status: Accepted
- Date: 22 October 2026
- Source: the owner's review of 22 October 2026, which asked for the second
  column from 821px and for the list inside it to split into two above 1100px.

## Context

The numbered sources are the list every footnote marker points at, so they sit
with the working they belong to. They were a second column beside the copy
only above 1100px. Below that they stacked under it, which put the last of the
54 entries up to a thousand pixels below the copy, and the owner wanted the two
side by side from the phone breakpoint up.

The list had been one column of host groups in that second column. At 1280 it
ran to 2,026px beside 585px of copy, and the owner asked for two lists above
1100px so it reads in half the height.

## Decision

`section.method` is a two-column grid from 821px, with the sources at the
copy's top on the same `1.618fr` to `1fr` split as before, so the widths the
owner approved are unchanged: 741px of copy and 458px of sources at 1280, and
631px and 390px at 1101. The list is one column of groups until 1101px and two
from there.

A host name is one unbreakable word, and the longest here,
`eaglesecuritysolutions.co.uk`, is about 207px at 12px in Segoe UI. A 217px
list holds it on Windows and clips it under DejaVu Sans on the CI machine,
where the first version of this change failed. Widening the column only moves
the font that breaks, so the heading takes `overflow-wrap: anywhere`: it wraps
onto a second line only when its own list is too narrow, which happens at 1101
for two host names and at neither 1280 nor 900.

## Consequences

- The page is 971px shorter at 1280 (4,232 to 3,261) and 907px at 1101, where
  more headings wrap, because the two lists halve the sources' height: 2,026
to 1,054px at 1280.
- From 821 to 1100 the page is 359px taller (5,100 to 5,459 at 900). The list
  is one column in a 283px column there, so it runs to 2,026px beside 642px of
  copy. Two lists wide enough for the longest heading need 438px, which leaves
  the copy 319px at 821, too narrow for the working; the owner asked for one
  column in this band.
- `source list` asserts the list is beside the copy at 900, 1101 and 1280 and
  below it at 390, that it runs in two lists at 1101 and 1280 and one at 900,
  that no host name is clipped or the list wider than its column, at 1280 with
  the page's own type and again under `Verdana, DejaVu Sans`, so the CI font
  cannot hide a missing break.
- `docs/performance-budget.md` carries the new page heights and the reason
  they moved.
