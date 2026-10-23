# 17. The record track reads in two words from 1200

- Status: Accepted
- Date: 23 October 2026
- Source: the owner's review of 23 October 2026: whether the record labels at
  1101 to 1279px can get their words back without squeezing the catch.

## Context

ADR 16 gave the record track 118px from 1280. Below that the track is
`minmax(90px,7.4%)`, 90 to 95px, and its lines lose 1rem to the hanging
indent: 44px of room at 1200, so "Only with extra kit" takes four lines for
four words.

The catch is the only flexible track in the band. The model column is 27%, the
score column 8.2% and the two cost columns 10%, so the 28px the record needs
comes out of the catch, and the only question is what that costs it.

## Measurements

Settled pages, every row scrolled through first, Chromium at 900px viewport
height. The probe is the query below, 118px with the 10% cost columns.

| Width | Record track | Table height | Page height | Rows taller |
|---|---|---|---|---|
| 1199px | 90 → 118px | 1,488 → 1,471px | 3,307 → 3,290px | 0 |
| 1150px | 90 → 118px | 1,542 → 1,542px | 3,361 → 3,361px | 1 |
| 1101px | 90 → 118px | 1,604 → 1,680px | 3,552 → 3,628px | 4 |

At 1199 Nest's row loses 17px and nothing grows. At 1150 one row grows while
the page keeps its height, and at 1101 four rows grow and the page is 76px
taller. The cost is zero at 1199, so 1200 is the width the band starts at
because it is the breakpoint the stylesheet already has, not a new edge.

## Decision

```
@media (min-width:1200px) and (max-width:1279px){
 .main-t thead tr,.main-t tr.main{grid-template-columns:40px 27% 118px minmax(84px,6.7%) minmax(96px,8.2%) 10% 10% 1fr}
}
```

That keeps the 10% cost columns of the 1101 to 1279 band and widens only the
record. Blink and Arlo read in two lines and Nest in three, the same counts
the 1280 band reads, at this font and at a 16px stand-in for a fallback 15%
wider. From 821 to 1199 the track stays at 90px and the three labels keep the
four lines ADR 16 left there.

## Rejected

- **118px for the whole band.** It adds 76px to the page at 1101 and makes
  four rows taller, which is the catch paying for the labels with exactly what
  the request said not to spend.
- **A proportional track, such as `minmax(90px,9.4%)`.** It reaches 118 at the
  top of the band and 104 at 1101, so it moves the catch's cost with the
  viewport and reads in three lines at the narrow end.
- **106px.** It buys a line rather than the two words, for 18px of the 28px
  the full width needs.
- **Taking the width from the model column.** The model column holds the name
  and the photo; the catch is the one column that can pay in lines it already
  has room for.
- **A breakpoint at 1150.** One row still grows there, so the labels would
  read in two lines with a taller row. 1200 is where the cost is zero, and the
  stylesheet already splits at 1200 for the sources lists.

## Consequences

- `desktop rows` measures 1200, 1199 and 1101 as well as the older widths. The
  record track must be at least 118px from 1200 and under 118 below, so a
  moved or mistyped breakpoint fails the audit.
- `docs/performance-budget.md` carries the current heights.
