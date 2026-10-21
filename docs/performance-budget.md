# Performance budget

The page exists for two interactions: change the sort, or open the comparison,
and see the answer. These are the numbers that keep both instant on a mid-range
phone and on a desktop.

Measured on the built page with `Emulation.setCPUThrottlingRate` at 4, which is
the closest a desktop browser gets to a mid-range phone. A sort is measured at
390px, where the rows are cards, and again at 1280px, where they are grid
tracks; the comparison is measured at 1280px, where its 18 rows are the table
they always are.

| Budget | Where | Target | Measured 20 October 2026 | Status |
|---|---|---|---|---|
| Sort, script plus the layout it causes | 390px | under 50ms | 9 to 15ms, six sorts per run | Met |
| Sort, script plus the layout it causes | 1280px | under 50ms | 9.6 to 21ms, six sorts per run | Met |
| Compare open, transition included | 1280px | under 150ms, best of 3 | 84 to 150ms | Met |
| Table movement when the tray opens | 1280px | 0px | 0px | Met |

## How to measure

`python build/check.py` applies the 4x throttle for the length of the check. It
loads a clean page at 1280px, times six sorts with `offsetHeight` read inside
the same task, times the same six again with the containment switched off in
the page, then repeats both at 390px, and finally opens the comparison three
times. All four figures fail the build.

`offsetHeight` is doing the work here on purpose. A long-task observer only
reports what the browser chooses to schedule: at 1280px in one run it reported
0ms for a sort whose layout measured 110ms.

Each sort is gated twice: the fastest of the six must be under 50ms **and** at
most 60% of the same page's uncontained sort. The first is the budget. The
second is what makes it fair: this harness runs on a desktop that also does
other work, and a machine at full load took one run's 1280px sort from 15ms to
130ms without the page changing at all. A loaded machine inflates both numbers
and fails only the first test, which is why one test alone is not enough. A
page that lays every row out again fails both.

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

The check itself measures 9 to 15ms with the containment and 55 to 97ms without
it.

The cost is paid at first paint, before any card has been measured: the 330px
estimate is 363px of card, against real cards of 331 to 409px, so the page
lands within about 2% of its settled height and moves only below the reader's
fold. In the audit browser that is 6,620 against 6,613px; in the desktop
preview, 6,688 against 6,832px. Chrome's scroll anchoring held it in thirty-
four 150px steps with no jump. Nothing is hidden: the skipped cards stay in
the accessibility tree, a jump to a card lands in the same place, and a printed
page has the same 28 pages and the same text with the containment on or off.

## Why the desktop sort is now 10 to 20ms

The desktop table's sort used to be 70 to 150ms at 4x: the table laid out all
fourteen rows again, because a table's column widths depend on every cell in it
and moving a row can change any of them. Table rows cannot opt out of layout,
so the rows stopped being table rows. Above 821px each row is a CSS grid track
inside a block, and the row group carries `content-visibility: auto` with
`contain-intrinsic-size: auto 118px`, so a sort lays out only the rows in view.

Four levers were measured against the table first, at 1280px against a 111ms
median baseline, and none of them reaches the budget:

| Lever | Sort plus layout | Table height |
|---|---|---|
| None | 111ms median | 1,675px |
| `content-visibility` on the rows | 138ms median | 1,675px |
| `contain: content` on the rows | 113ms median | 1,675px |
| `table-layout: fixed` | 101ms median | 3,386px |
| Grid rows, contained | 9.6 to 21ms | 1,675px |

The first two are ignored or counterproductive on table rows. Fixed layout
carries the cost of the automatic column widths it removes, and with the
table's own widths it still measured 64.7ms against 70.9ms: the cost is per
row of text, not per column decision, which is why only laying out fewer rows
moves it.

The grid tracks reproduce the widths the table chose, so the desktop layout
does not move. At 1280px the table is 1,675px tall either way, all fourteen
rows are the same height, and the columns are 34, 337, 120, 84, 102, 109, 114
and 348px against the table's 33, 337, 120, 84, 102, 109, 114 and 349px. The
2px on the first track is where the collapsed table border used to be; without
it every column after the compare box sat 2px left.

Measured on fresh pages at every breakpoint the stylesheet defines, with every
card scrolled through first so contained rows settle:

| Width | Table height, table → grid | Page height | Cells clipping | Horizontal overflow |
|---|---|---|---|---|
| 1440px | 1,624 → 1,620px | 3,408 → 3,405px | 0 | 0 |
| 1280px | 1,675 → 1,675px | 3,448 → 3,448px | 0 | 0 |
| 1100px | 1,759 → 1,740px | 3,620 → 3,601px | 0 | 0 |
| 1000px | 1,907 → 1,927px | 3,800 → 3,820px | 0 | 0 |
| 900px | 2,182 → 2,167px | 4,096 → 4,081px | 0 | 0 |
| 821px | 2,688 → 2,818px | 4,662 → 4,792px | 0 | 0 |
| 820px | 4,581 → 4,581px | 6,140 → 6,140px | 0 | 0 |
| 390px | 4,960 → 4,960px | 6,573 → 6,573px | 0 | 0 |

1280px is exact because the tracks were read off the table at 1280px. Between
900 and 1100 the columns differ by 2 to 6% and a row can be one line of text
taller or shorter, which is the 1% of table height in the table above; at 821px,
one pixel above the breakpoint where the layout becomes cards, the catch column
is 113px against the table's 116 and three rows gain a line, for 2.7% of table
height. No cell clips at any width, no page scrolls sideways, and every row's
cells start on the header's columns to the pixel.

A row's box begins 1px lower than a table row's, because the header block is a
pixel taller than the header row was; the text sits on the same baseline in
every column. With that one pixel, a pixel diff of the 1280px table against the
old one is 2.3%, almost all of it in the row rules and the 2px header rule.

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
fastest of three and prints all three rather than trusting one number. 150ms is
the line at which the capture has become a stall rather than a frame; a change
that doubles the page's share lands well past it. With the desktop rows
uncontained the same open measured 187ms, since the transition captures a page
that has just laid every row out.

## Why the stylesheet and script are separate files

The page used to carry 25KB of CSS and 27KB of JavaScript inside its HTML, so
a repeat visit downloaded both again and no cache header could help. The two
sources are now `build/page.css` and `build/page.js`, and the build emits them
as `assets/page.css` and `assets/page.js`, linked with a content version in the
query. A price change produces a new URL, so the cache is busted, but the path
stays stable: GitHub Pages caches HTML for ten minutes, and deleting an old
hashed filename would break a page that cached copy still points at.

Measured with `gzip -9` on the built page, which is the conservative bound for
what GitHub Pages serves:

| | First visit | Repeat visit |
|---|---|---|
| Inlined (before) | 29,020 bytes | 29,020 bytes |
| Separate files (after) | 29,840 bytes | 13,516 bytes |

The split files are 6,945 bytes of CSS and 9,379 bytes of JavaScript; the HTML
alone is 13,516 bytes compressed. A first visit costs 820 bytes more than the
inlined page, because the files compress slightly worse apart than inside the
document. A repeat visit drops from 29,020 to 13,516 bytes, because the
versioned assets come from cache instead of being downloaded again. That is the
trade: 2.8% more on a cold cache for 53% less on every visit after it. It also
costs two more requests, both same-origin.

`check.py` asserts that the page loads the versions the build wrote, that no
`<style>` block remains, and that both files match the build's text, so a stale
inline copy cannot come back.
