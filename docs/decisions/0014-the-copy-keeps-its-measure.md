# 14. The copy keeps its measure, the sources take the rest

- Status: Accepted
- Date: 23 October 2026
- Source: the owner's review of 23 October 2026: the copy is
  `minmax(0, 80ch) minmax(0, 1fr)` from 821px, and the source list gets a third
  list at 1200px and a fourth at 1300px, with a 2rem gap.

## Context

ADR 11 fixed the sources column at 486px above 1100px and left the copy at
1.618fr of what remained. That copy track is wider than its own paragraph
measure: 631px at 1101 and 741px at 1280, against a 561px measure, so every
paragraph stops short of its column. At 1280 the 180px beside each paragraph
was doing nothing while the sources, 458px with two lists, were the longest
thing in the row.

## Decision

`section.method` is `minmax(0, 80ch) minmax(0, 1fr)` from 821px. The copy is
never wider than its measure, and the sources take everything left over, so the
row ends at the list's edge rather than at whitespace.

The entries are one list to 1100px, two from 1101, three from 1200 and four
from 1300, all with a 2rem gap. That supersedes ADR 11's 1.5rem at 1101; the
gap is one distance at every width that has more than one list.

A source link wraps anywhere, like the host heading above it, because a link
whose text is a host name is one unbreakable word. At 1300 four lists of
144.75px hold `smarthomeassistant.co.uk guide` at 159px under Verdana, and
without the break it painted into the next column while the container still
reported fit at Segoe's narrower width.

## Measurements

Settled pages, every card scrolled through first, Chromium at 900px viewport
height:

| Width | Copy | Sources | Lists | Page |
|---|---|---|---|---|
| 1440px | 561px | 815px | 4 | 2,711px |
| 1300px | 561px | 675px | 4 | 2,852px |
| 1280px | 561px | 655px | 3 | 2,954px |
| 1200px | 561px | 575px | 3 | 3,082px |
| 1101px | 561px | 476px | 2 | 3,552px |
| 1100px | 561px | 475px | 1 | 4,465px |
| 900px | 561px | 275px | 1 | 5,136px |
| 821px | 561px | 196px | 1 | 5,456px |

The 80ch cap is 561px at this type size, and the copy is that wide at every
desktop width because the cap binds above 821. The 2rem gap holds at 1101,
1200 and 1300. No host heading takes more than two lines and no link leaves
its column, under Segoe or Verdana.

## Rejected

- **Four lists from 821.** The sources get 196px at 821, so four lists leave
  25px each for a 159px link; the extra lists need the column to widen first.
- **Keeping ADR 11's 1.5rem gap for two lists.** The difference is 4px a
  column at 1101, and two gaps in the same list are one rhythm to hold.
- **Moving the fourth list to 1400px.** The owner asked for 1300. At 1300 the
  list is 675px wide, 144.75px a column, which holds every heading and link
  with the anywhere break.
- **Smaller source type to fit four lists.** The 12px floor is the type floor
  and `type floor` asserts it.

## Consequences

- The page is 446px shorter at 1440 (3,157 to 2,711) and 307px shorter at 1280
  (3,261 to 2,954). At 821 it is 101px taller (5,355 to 5,456), because the
  copy widened from 468 to 561 while the list narrowed from 289 to 196, and the
  extra lines in the list outweigh the copy's saving. The 900px and 1100px
  pages are unchanged at 5,136 and 4,465.
- `source list` measures 821, 900, 1101, 1200, 1280 and 1300. It asserts the
  list count at each, the 2rem gap at 1101, 1200 and 1300, the copy at no more
  than 80ch measured in the page's own font, and the list ending at the
  working's right edge. It reads the wide font at 1300, the narrowest four-list
  width. That check caught the link overflow before this was committed.
- The link's anywhere break is the same trade the host heading made in ADR 11:
  a word too wide for its column breaks rather than painting into the next one.
- `docs/performance-budget.md` carries the current heights and the two deltas.
