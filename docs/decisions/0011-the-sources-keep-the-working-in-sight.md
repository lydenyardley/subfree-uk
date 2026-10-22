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
copy's top. The list is one column of groups until 1101px and two from there.

The second column is fixed at 486px above 1100px. A host name is one
unbreakable word, and the longest here, `eaglesecuritysolutions.co.uk`, is
about 207px at 12px; two lists plus the 24px gap need 438px, and 486 leaves
the tightest list 231px. The copy keeps `1.618fr` of what is left, which is
still wider than its 80ch measure, so the width the sources take was
whitespace.

## Consequences

- The page is 988px shorter at 1280 (4,232 to 3,244) and at 1101, because the
  two lists halve the sources' height: 2,026 to 1,038px.
- From 821 to 1100 the page is 359px taller (5,100 to 5,459 at 900). The list
  is one column in a 313px column there, so it runs to 2,026px beside 642px of
  copy. Two lists need 438px, which leaves the copy 319px at 821 (the wide
  layout's 486px would leave 271px), too narrow for the working; the owner
  asked for one column in this band.
- `source list` asserts the list is beside the copy at 900, 1101 and 1280 and
  below it at 390, that it runs in two lists at 1101 and 1280 and one at 900,
  that no host name is clipped, and that it does not overflow its column.
- `docs/performance-budget.md` carries the new page heights and the reason
  they moved.
