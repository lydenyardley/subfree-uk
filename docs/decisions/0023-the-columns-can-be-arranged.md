# 23. The comparison's columns can be arranged

- Status: Accepted
- Date: 25 October 2026
- Source: direction A of the 23 October overdrive audit, which ADR 24 closes,
  accepted on 25 October with four changes: keep the verdict rule with its
  column, use a six-dot grip, never cut the handle, and hold the reference
  still.

## Context

The comparison has always been in the order the reader ticked the models in.
Two ways of moving a column were drawn. The first was one divider between two
columns, swapped as the divider passed: it pushes one column through a gap, and
the page is left comparing against whatever ended up on the left. The second is
a handle per column, which arranges the comparison rather than shifting it.

The three columns are the only place on the page where a reader has three things
in a row and a reason to put them in their own order.

## Decision

- **A handle, not a divider.** Each column carries a clip centred on its 3px
  rule: 26px by 18px, six dots, in a 44px target that sits in the header's empty
  strip. The target's bottom edge is 1.5px below the rule, so the cost row
  underneath is still the reader's to click.
- **The whole column moves.** Every cell carries its model's id, so the column,
  its verdict rule and its cost cell travel together, and the table is rebuilt in
  the new order when the column lands. Neighbours slide into the vacated slot;
  the last few pixels are a 160ms slide, and the rebuild happens when it ends.
- **The reference does not move.** A delta names the cheapest of the three,
  wherever that column sits. Arranging the columns reorders the reading and
  never the arithmetic, which is what a reader comparing prices expects.
- **The keyboard has the same power.** Each handle is a button; Left and Right
  move the column one place, Home and End send it to an end, focus follows the
  column, and the move is announced. The name carries the model and its place.
- **A column in flight is a surface.** It paints above its neighbours, so its
  handle is never cut in half, and it is opaque, so the two columns do not read
  through each other while they cross. The cost row's tint sits on the row
  rather than on its cells, so a sliding column cannot tear a pale gap through
  it.
- **The address carries the arrangement.** `?cmp=` is written in the arranged
  order and a shared link reopens the columns that way.
- **The phone does not get the drag.** Below 821px the comparison is a sideways
  scroller with one model on screen; the handles are hidden there rather than
  offering a gesture whose target is mostly off the edge.

## Consequences

- `compare column move` and `compare column keys` hold the behaviour, and both
  fail on the build before this one with `no column handle on …`.
- `buildCmp()` is keyed on the ordered ids, so a move and a tick change the
  table through the same rebuild.
- The cell positioning that lets a column fly is switched on with the drag and
  taken off when it lands. At rest the table paints the way it did before the
  columns could move, which is the page the compare open's budget was measured
  on; the open's longest task went back under its 120ms line.
- The sketch's Escape-to-restore did not ship: the page's own undo is the
  handle that made the move, and a second shortcut for one gesture was more
  surface than the arrangement earns.
- ADR 24 closes the audit this direction came from and holds what it left
  open, the source card. The collapsed identical-row line is not waiting: its
  count is the compare panel's own control, and ADR 5 declined the line itself.
