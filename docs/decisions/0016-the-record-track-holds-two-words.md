# 16. The record track holds two words at a time

- Status: Accepted
- Date: 23 October 2026
- Source: the owner's review of 23 October 2026: whether the 1440px record
  label's fourth line is worth reclaiming, and whether the footnote move
  crowded the record and price columns from 821 to 940px.

## Context

ADR 15 made the label and its footnote number one cluster, so the number now
spends about 12px on the label's last line. The record track is the narrowest
column, and its lines lose another 1rem to the hanging indent, so a line of
"Only with extra kit" has 44px of room in a 92px track at 1280 and 56px in a
104px track at 1440. Two rows read one word a line, four lines for four words.

The height did not grow. ADR 15 measured the page 20px shorter at 1440 and
17px shorter at 1280, and every row that changed got shorter. The cost is
typographic, not vertical.

## Decision

From 1280px the record track is 118px:

```
grid-template-columns:40px 27% 118px minmax(84px,6.7%) minmax(96px,8.2%) 152px 152px 1fr
```

Nothing changes from 821 to 1279px. There the catch needs every pixel it has
(138px of track at 901), and the four-line labels are what ADR 15 left behind:
the table is 2,495px at 901 and 2,366px at 821 both before and after that move,
and the price stays on one line in every row.

## Measurements

Settled pages, every row scrolled through first, Chromium at 900px viewport
height. At 1440 the page goes from 2,691 to 2,680, at 1300 from 2,835 to 2,818
and at 1280 from 2,937 to 2,920. The catch gives up 14px of text box at 1440
(299.9 to 285.8) and 26px at 1280 (218.4 to 192.7). At 1280 the catches of
Blink and Arlo gain a line, to 81px, and neither row grows, because the model
cell already sets both heights. Nest's row goes from 99px to 82px at 1280 and
Arlo's from 99px to 87px at 1440. No other row changes at either width.

The label's line counts at 118px are two for Blink and Arlo and three for Nest,
at 1440 and at 1280, at this font and at a 16px stand-in for a fallback 15%
wider. The same test at 110px gives four lines for Blink and Arlo under the
wider stand-in, which is why 110px is not the number.

## Rejected

- **110px.** It reads in two lines at this font and splits again at 16px, the
  same font-dependent bet that made the earlier 7.4% track stack words.
- **128px.** It fits Nest's "Only briefly (3 hrs)" in two lines at 14px, and
  not at 16px, for 10px more of the catch.
- **A smaller hanging indent.** An 8px indent gives each line 8px back, to
  64px at 1440, and "extra kit" plus the number needs 70px, so it splits again
  there and sooner on a wider font. It buys the line for the same
  font-dependent reason.
- **Widening at 901 to 940.** The record track there is 90px and the catch has
  138px at 901, the width ADR 13's band and ADR 15's assertion both depend on.
  The crowding in that band predates ADR 15 and changing it would trade a
  sentence column for a label column.
- **ADR 15's "widening the record column".** That rejection weighed 9px of
  footnote against a track. This one weighs a line count against the catch,
  measured at two font widths, and the footnote is part of why the line count
  moved.

## Consequences

- `desktop rows` asserts the record track is at least 118px at 1280 and 1440,
  so a later track change fails the audit instead of quietly stacking words.
- `docs/performance-budget.md` carries the new heights at 1440, 1300 and 1280.
- At 821 to 940px the record and price columns are unchanged from ADR 15: the
  label reads in four short lines, the number ends the last one, and nothing
  clips or crosses a cell.
