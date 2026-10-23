# 15. The footnote stays on the copy's last line

- Status: Accepted
- Date: 23 October 2026
- Source: the owner's review of 23 October 2026: the `.fn` number stays inline
  with the end of the record label, still superscript, when the label wraps.

## Context

A record cell is a label and the number that cites the row's source:
`<span class="rec">Only briefly (3 hrs)</span><a class="fn">7</a>`. The label
is an inline-block so its bullet can hang outside a 1rem indent.

A marker outside that block has nothing after a wrapped label's last line. The
block ends at the column edge, so the number starts a new line at the hanging
indent: at 1280 it sat at the label's own left edge, 1px under its bottom, and
read as a note on the cell rather than on the words above it. Three rows wrap
there (Blink, Arlo, Nest) and seven widths from 821 to 1440 show the same
thing.

## Decision

The marker moves inside the label's block, and the label gets its own inline
span so it still reads as a label:

```
<span class="rec rec-brief"><span class="rec-t">Only briefly (3 hrs)</span><a class="fn">7</a></span>
```

There is no break opportunity between the label and the number, so the two are
one cluster. The number sits at the end of the last line, superscript and all,
and never starts a line of its own. `labels` reads `.rec-t`, so the number
cannot leak into the label's text.

The cost is the number's ~9px on that line. A label can take one more line than
it would without it: Blink's goes from three lines to four at 1440.

## Measurements

Settled pages, every row scrolled through first, Chromium at 900px viewport
height. The page is 20px shorter at 1440 (2,711 to 2,691), 17px shorter at
1280 (2,954 to 2,937) and 36px shorter at 900 (5,136 to 5,100). At 1101, 1100,
1000 and 940 the heights are unchanged.

At 1280 the number now starts 33px right of the label's left edge and 22px
above its bottom, on the last line, for all three wrapped rows.

## Rejected

- **A wrapper that owns the indent.** `.rec` is already the block with the
  hanging bullet. A second element around it, plus a scoped rule making `.rec`
  inline inside it, adds a level to move a 9px marker.
- **Moving the indent onto the cell.** `padding-left` on a `td` changes the
  track the table computes, so a text position would move a column.
- **Widening the record column.** It is the narrowest column on purpose; 9px
  of footnote is not worth a track.

## Consequences

- `desktop rows` reads the marker against its label at every width from 821 to
  1440. The number's left edge must be past the label's box and its top at
  least 4px above the box's bottom, so a number on a line of its own fails the
  audit. On the old markup it failed at all seven widths.
- The label and its citation are one block now, so nothing can separate them
  again without failing the check.
- `docs/performance-budget.md` carries the current heights.
