# 13. The catch takes the row it cannot fit

- Status: Accepted
- Date: 23 October 2026
- Source: the owner's review of 23 October 2026: "Stop the catch sentence
  clipping at 821px, the narrowest desktop width."

## Context

ADR 10 closed with the 821px catch cell still clipping a long sentence and
noted that the audit did not measure 821. The catch had been the row's last
track since ADR 6, and the tracks had been tuned twice by width without
looking at what the sentence needs.

Measured on the page before this change, at 821px the catch track is 68px of
the 772.8px table. Its text box is 0.2px wide, because the cell is a flex row
whose text may shrink and whose chevron cannot, so the sentence is laid out as
18 to 20 lines of one or two words. Those lines paint past the text box and
into the chevron: the words end 51.5px right of the chevron's left edge, and a
row grows to 394px. The same thing happens at 860px (23px into the chevron)
and at 900px the sentence still runs to 11 lines in a 224px row, though it
clears the chevron by 6.2px.

Eight tracks cannot hold a sentence at 821. The compare box, the five figure
columns and the 27% model column account for 704.65px of the table, so the
catch gets what is left. Shrinking the figures to buy the catch 120px takes
more width than the model column has to give, and any such split is a width
tuned for one font.

## Decision

Below 901px the catch leaves the tracks. The row is seven tracks, the compare
box and six columns, and the catch sits on a second grid row from the model
column to the table's right edge. It carries its own "Main catch" caption, the
same label a phone card gives it, and the model column takes the width the
catch gave up: `minmax(0,1fr)`, so the figures stay on their fixed columns and
no space is left at the table's edge.

The catch's `<th>` stays in the header and in the accessibility tree, clipped
to 1px rather than removed, so the table keeps eight named columns for
assistive technology while seven are drawn. The rows' cell borders are off in
this band and the item carries the rule instead, so an item still draws one
line and an open details panel does not draw two.

The band stops at 901px. At 901 the tracks leave the catch 138px, which clears
the chevron in every row by 6.9px, and at 940 the column is 4,893px of page
against the band's 5,108: the column is the shorter layout there, as it is at
1000 and 1100. 901 depends on no font, because the tracks above it are fixed
widths and one percentage.

## Rejected

- **Tuning the fixed tracks again.** Two earlier fixes of the same kind failed
  on the Ubuntu font, and the same sentence still would not fit: the catch
  would need 120px from a 208px model column.
- **A second header row for the catch label.** The header is one sticky block
  at the top of the table; its second row would sit above the first row's
  figures, not above any catch, and read as a caption for the wrong row.
- **The catch in a column at every width.** It works at 1280, where the catch
  is 458px wide, and the owner's approved rows are the desktop layout there.
- **Cards from 821px.** The phone layout is 6,140px at 820 against 5,355 at
  821; the table is the point of the page.
- **Letting the table scroll sideways in the band.** A sentence off the right
  edge is the same clip with a scrollbar.

## Consequences

- The page is 5,355px at 821 (7,091 before) and 5,136 at 900 (5,459 before);
  the table is 2,330px at 821 (4,066 before). The catch reads in one line at
  both widths, and no text paints under a chevron.
- `desktop rows` now measures 821, 900 and 901 and reads the words, not the cell
  box: a cell whose text may shrink reports no overflow while its words paint
  across the chevron. It asserts seven tracks, seven visible headers, the band
  from the model column to the table edge, the caption, and at most three
  lines of catch in the band; the column layout keeps its eight tracks and
  gains the same chevron assertion. Removing the band fails it at 821 and 900;
  adding the caption back to the column fails it at 1000.
- At 901 to 980 the catch is still a 5 to 11 line column. That is the state
  ADR 10 accepted, and the band's caption costs more height than it saves
  there.
- The catch's caption is generated content and repeats the header cell for a
  screen reader, as the phone card's does. It is the same trade ADR 4 made
  when the card layout hid the header row.
- `docs/performance-budget.md` carries the new page heights and the table
  height, with the band's boundary and the reason it stops at 901.
