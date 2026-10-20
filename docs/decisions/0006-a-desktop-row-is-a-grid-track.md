# 6. A desktop row is a grid track

- Status: Accepted
- Date: 20 October 2026
- Source: ADR 4 left the desktop table at 70 to 150ms per sort and named it; the
  measurements in `docs/performance-budget.md` and the probes behind them.

## Context

A sort re-appends fourteen `tbody` elements. At 390px that used to lay out
5,000px of cards, which ADR 4 fixed with containment. At 1280px it laid out
the table again, because a table's column widths depend on every cell in it,
so moving one row can change any column.

ADR 4 named that cost as "the table's own column balancing". Measuring it
disproved that. With `table-layout: fixed` and a colgroup carrying the widths
the table itself had chosen, the sort still measured 64.7ms against a 70.9ms
baseline: 9%, not the budget. The cost is not the column decision, it is laying
out fourteen rows of text. Halving the rows halved it, 70.9ms to 49.5ms, which
is the figure that shows what has to change.

Table rows cannot opt out of layout. `content-visibility` on a row group is
ignored, `contain: content` on one measured 113ms against 111, and `contain:
size` would need a fixed height per row, which the data does not have.

## Decision

### Above 821px a row is a grid track inside a block

`table.main-t`, its `thead` and its `tbody` are blocks. Each row of the header
and each `tr.main` is a grid with eight tracks, and the row group carries
`content-visibility: auto` with `contain-intrinsic-size: auto 118px`, 140px
between 821 and 1100. A sort lays out the rows in view and nothing else.

The markup is unchanged: the same table, row and cell elements, only laid out
as tracks. Chromium still exposes the table, header cells, row headers and
cells to assistive technology, which was checked on the accessibility tree
rather than assumed.

### The tracks are the table's own widths

At 1280px the table chose 33, 337, 120, 84, 102, 109, 114 and 349px. The
tracks are `calc(2rem + 2px) 27% 120px 6.7% 8.2% 8.7% 9.1% 1fr`, which is
34, 337, 120, 84, 102, 109, 114 and 348px: the 2px on the first track is where
the collapsed table border used to sit, and without it every column after the
compare box moved 2px left. Between 821 and 1100 the tracks are
`calc(2rem + 2px) 28% 84px 84px 84px 84px 84px 1fr`, because the table clamped
its numeric columns at about 84px there and gave the rest to the catch column.

The cells keep their `width` rules for the compare table, so `.main-t tr.main >
*` resets width to `auto`: a percentage width on a grid item resolves against
its own track, and the model column measured 91px inside a 337px track until
that reset was added.

### The header sticks as a block

`position: sticky` on a cell only moves it inside its parent, and the parent is
now the header block, so sticking the cells left the header behind on scroll.
The header block is sticky instead, and the cells are `display: flex` so a
one-line label still centres in a two-line row with the cell stretched to keep
its paper background over the strip.

## Rejected

- **`table-layout: fixed` alone.** 101ms median, and the table doubled to
  3,386px without explicit widths. With the table's own widths: 64.7ms.
- **`contain: content` on the rows.** 113ms against 111. Ignored by table rows.
- **Virtualising the table.** Print, find-in-page, jump links and the
  accessibility tree all assume the rows exist; a windowed table fakes a height
  and breaks all four, to save work the containment already skips.
- **Sorting with `transform` or `order` only.** The rows would paint in one
  order and remain in another for the keyboard and a screen reader. A sort is
  a reorder.
- **A separate card layout at every width.** It is 13.4ms at 1280px, but
  4,518px of single-column cards instead of a comparison table.

## Consequences

- The 1280px sort is 9.6 to 21ms at 4x, down from 70 to 150ms, against 55 to
  97ms with the containment switched off in the same page.
- `perf_check` gates the fastest of six sorts at 50ms **and** at 60% of the
  same page's uncontained sort, at both 1280 and 390px. Removing the desktop
  containment fails it at 128.3ms and fails the layout assertion; removing the
  sticky header fails the scroll assertion.
- Heights at every breakpoint are in `docs/performance-budget.md`. 1280px is
  exact; 900 to 1100px differ by about 1%; 821px, one pixel above the card
  breakpoint, is 2.7% taller because its catch column is 3px narrower. No cell
  clips and no page scrolls sideways at any width.
- Print is unchanged and does not see this layout: an A4 page is 794px wide,
  below the breakpoint, so both produce the same bytes.
- `content-visibility: auto` keeps skipped rows in the accessibility tree, as
  it does for the phone cards; a jump to a row still lands centred with focus
  on its checkbox.
- The intrinsic size is an estimate until a row is laid out. At 1280px the
  rows average 120px, so the first paint is within 1% of the settled height at
  most widths; at 900px rows average 155px against the 140px estimate, so the
  table can start up to 200px shorter and grow as the reader scrolls. Chrome's
  scroll anchoring held the phone cards against the same movement in ADR 4.
- A future redesign of the desktop columns has to edit these tracks and the
  table's own widths together, or the two layouts will disagree.
