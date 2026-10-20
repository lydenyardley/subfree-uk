# Performance budget

The page exists for one phone interaction: change the sort, or open the
comparison, and see the answer. These are the numbers that keep that
interaction instant on a mid-range phone.

Measured on the built page with `Emulation.setCPUThrottlingRate` at 4. A sort
is measured at 390px, where the phone cards are; the comparison is measured at
1280px, where its 18 rows are the table they always are.

| Budget | Where | Target | Measured 20 October 2026 | Status |
|---|---|---|---|---|
| Sort, script plus the layout it causes | 390px | under 50ms | 6.6 to 14ms, median 9.3, over 18 sorts | Met |
| Sort, script only | 1280px | under 100ms | 5 to 16ms | Met |
| Compare open, transition included | 1280px | under 150ms, median of 3 | 52 to 122ms warm; 119 to 171ms on the first open | Met |
| Sort task, table layout | 1280px | not gated | 70 to 150ms at 4x, unchanged by this work | Named below |
| Table movement when the tray opens | 390px | 0px | 0px | Met |

## How to measure

`python build/check.py` applies the 4x throttle for the length of the check.
It dispatches four sorts and three compare opens at 1280px, then resizes to
390px and times six more sorts, reading `offsetHeight` inside the same task so
the sort's layout is in the figure. It prints the slowest sort, the three
opens, the 390px sort-plus-layout maximum, the longest task seen at 1280px and
the longest one seen while the comparison opens. All of those fail the build
except the 1280px task, which is printed for the reason below.

`offsetHeight` is doing the work here on purpose. A long-task observer only
reports what the browser chooses to schedule: at 1280px in one run it reported
0ms for a sort whose layout measured 110ms.

## Why the phone sort is now 7 to 14ms

The sort's own JavaScript was never the cost. It is 5 to 16ms: read the
`data-*` values, sort fourteen elements, re-append them. What followed was
Chromium laying out fourteen cards that together run to about 5,000px, and at
390px that was the whole task: 45 to 221ms at 4x, one long task per sort.

The phone cards now carry `content-visibility: auto` with
`contain-intrinsic-size: auto 330px`. A card below the fold is not laid out,
so a sort lays out the three or four cards in view instead of all fourteen.
The `auto` in the intrinsic size is what makes it affordable: the 330px
estimate is used until a card has been laid out once, then the real height is
remembered.

Two runs of six sorts each, alternating the two states so both see the same
machine load:

| Cards | Sort plus layout |
|---|---|
| Laid out | 44.8, 54.8, 57.5, 64.6, 108.7, 117.6, 132.1, 134, 139.8, 147.5, 147.5, 150.5, 153.3, 165.1, 176.1, 196.7, 198, 221.3ms |
| Contained | 6.6, 6.7, 7.3, 7.8, 8.2, 8.2, 8.4, 8.6, 8.9, 9.3, 9.7, 9.9, 10.1, 10.4, 10.5, 12.7, 12.8, 13.7, 14ms |

The check itself measures 15.8ms with the containment and 75.7ms without it.

The cost is paid at first paint, before any card has been measured: the 330px
estimate is 363px of card, against real cards of 331 to 409px, so the page
lands within about 2% of its settled height and moves only below the reader's
fold. In the audit browser that is 6,620 against 6,613px; in the desktop
preview, 6,688 against 6,832px. Chrome's scroll anchoring held it in thirty-
four 150px steps with no jump. Nothing is hidden: the skipped cards stay in
the accessibility tree, a jump to a card lands in the same place, and a printed
page has the same 28 pages and the same text with the containment on or off.

## What is still not fixed: the 1280px table

The desktop table's sort is 70 to 150ms at 4x, before and after this work. Its
cost is the table itself, and table rows cannot opt out of layout. Four levers
were measured at 1280px against a 111ms median baseline:

| Lever | Sort plus layout | Table height |
|---|---|---|
| None | 111ms median | 1,675px |
| `content-visibility` on the rows | 138ms median | 1,675px |
| `contain: content` on the rows | 113ms median | 1,675px |
| `table-layout: fixed` | 101ms median | 3,386px |

The first two are ignored or counterproductive on table rows. Fixed layout
carries the cost of the automatic column widths it removes, and without
explicit widths per column it doubles the table. A 1280px viewport on a CPU
four times slower than this one is not a device that exists; the phone is. The
figure is printed every run and stays in this table as the line to watch if
the desktop table grows.

## Why the bar draw is gone

Every sort used to set fourteen bars to zero, force a frame, then run fourteen
timers to draw them back, for a ripple nobody sees twice. The bars are painted
at their score in the markup now and nothing rewrites them. That leaves no
motion in sorting at all, which the design rules asked for anyway, and removes
fourteen timers per sort with it.

## Why the compare open allows 150ms

Opening the comparison runs through `document.startViewTransition`: the
browser captures the old viewport, runs the update, captures the new one, and
only then paints the panel. The panel's first paint therefore waits for one
snapshot it did not wait for before, which is one to two frames at this
throttle. The page's own share is the 18-row render, 4 to 20ms.

Measured over three opens per run: 52 to 122ms warm across twelve runs, and 119
to 171ms on the first open of a session, which pays the snapshot pipeline's
warm-up. The spread tracks machine load, which is why the check takes the
median of three and prints all three rather than trusting one number. 150ms is
the line at which the capture has become a stall rather than a frame; a change
that doubles the page's share lands well past it.
