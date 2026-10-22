# 9. The ticked rows fly into their columns

- Status: Accepted
- Date: 22 October 2026
- Source: the owner's review of 22 October 2026, which asked for the names,
  and then the photos, to move into the comparison the way the tray does.

## Context

ADR 3 declined to name the ticked rows: a row named in both frames is either
painted in place and in the air at once, or vanishes from the table for the
length of the transition. The owner has since asked for the movement itself —
the row's name and photo travelling into the comparison's column.

Both objections are answerable now that the table is built before the
transition starts. A view-transition name can sit on one element at a time, so
each half carries it for one frame: the table's copy while the old frame is
captured, the header's copy in the frame after the update. The table's copy is
out of the picture for those 240ms, and the panel is over the table by then,
so the vanish ADR 3 warned about is not on screen.

## Decision

Each ticked row contributes two pairs, `cmp-n-<id>` for its name and
`cmp-p-<id>` for its photo. The rows are named just before
`startViewTransition` runs; the update callback moves the names to the
header's `.cmp-name` and `.cmp-photo img` and hides the table's copies; a
cleanup on `finished` — and a 700ms backstop, for a skipped or interrupted
transition — clears both sides. Nothing is named between opens.

A ticked row is rendered from the moment it is ticked, by
`tbody.item:has(input.cmp:checked){content-visibility: visible}`. A contained
row that is off screen has no box to capture, and the browser would skip that
pair; uncontaining at the tick rather than inside the open puts that layout
where nothing is waiting for it, and at most three rows are ever ticked.

The two boxes of a pair are meant to be the same shape, because the browser
scales the old picture into the new box: the header's name was a block as wide
as its column and stretched the row's 130px of text across 320px on the way,
so `.cmp-name` is now as wide as its text. The photos already matched at
45 by 60.

The pairs run on the tray's 240ms curve, so the open is one movement.

Closing runs the same six pairs in reverse. The header's copies carry the names
while the open frame is captured; the update callback hides the panel, gives
the names back to the rows' copies and takes the header's out of the picture.
The same 700ms backstop clears both sides. A pair whose row is hidden by a
filter is never named: its header copy stays visible and the panel closes
without a flight for that model, rather than flying to a box that is not there.

## Consequences

- `compare morph` asserts the two frames: six parts named on the rows before
  the open and none in the header; six in the header after it, none on the
  rows, with the table's copies hidden; then nothing named and nothing hidden.
  It also asserts a captured group for each of the six: a name that never
  became a snapshot still reads back from the element, and only the group
  proves the pair travelled.
- A change that skips a frame, names both halves at once, captures fewer
  parts or leaves a name behind fails the build, on the way in and on the way
  out. The close is asserted from the recorded frames: six pairs on the header
  before it, six on the rows after it, and none left once the panel has gone.
- A model with no photo pairs one name only.
- `prefers-reduced-motion` and browsers without the API skip the whole thing:
  the rows are never named, and the panel opens without movement.
- The flight costs paint. Seven boxes are captured where the open used to
  capture two, so `performance budget` measures the open twice — once with the
  transition and once with it switched off by reduced motion — and holds the
  panel's own work at 150ms while allowing the flight 500ms. The numbers and
  why the second line is loose are in `docs/performance-budget.md`.
