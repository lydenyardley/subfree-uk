# Performance budget

The page exists for two interactions: change the sort, or open the comparison,
and see the answer. These are the numbers that keep both instant on a mid-range
phone and on a desktop.

Measured on the built page with `Emulation.setCPUThrottlingRate` at 4, which is
the closest a desktop browser gets to a mid-range phone. A sort is measured at
390px, where the rows are cards, and again at 1280px, where they are grid
tracks; the comparison is measured at 1280px, where its 18 rows are the table
they always are.

| Budget | Where | Target | Measured 20 to 22 October 2026 | Status |
|---|---|---|---|---|
| Sort, script plus the layout it causes | 390px | under 50ms | 9 to 15ms, six sorts per run | Met |
| Sort, script plus the layout it causes | 1280px | under 50ms | 9.6 to 21ms, six sorts per run | Met |
| Compare open with the flight, transition included | 1280px | under 500ms, best of 3 | 115 to 237ms | Met |
| Compare open without the transition | 1280px | under 150ms, best of 3 | 16 to 75ms | Met |
| Longest task inside the compare open | 1280px | under 120ms, median of 3 | 0ms | Met |
| Table movement when the tray opens | 1280px | 0px | 0px | Met |

## The byte budget

| File | Budget, gzipped | Measured 28 October 2026 |
|---|---|---|
| `index.html` | 24,000 | 18,868 |
| `assets/page.css` | 18,000 | 15,298 |
| `assets/page.js` | 24,000 | 19,682 |
| The three together, a first visit | 60,000 | 53,848 |

These are the bytes a reader downloads before the page can answer them, so they
are the one performance number that can be held exactly: same input, same
output, no machine in between. `build/check.py`'s `transfer budget` check
rebuilds, gzips the three files at level 9 and fails above any ceiling. The
headroom is deliberate — a tenth of the total — so a row or a sentence does not
need a budget edit, while a second category's copy, a dependency or an inline
data block does.
The comparison's rows are in the script rather than in a JSON block on purpose:
the same bytes on the wire, one more parse, and one more copy to fall out of
step with `ROWS`. If the budget does bind, that is the first trade to revisit.

## How to measure

`python build/check.py` applies the 4x throttle for the length of the check. It
loads a clean page at 1280px, times six sorts with `offsetHeight` read inside
the same task, times the same six again with the containment switched off in
the page, then repeats both at 390px, and finally opens the comparison three
times with the flight and three times without it. Every figure above fails the
build.

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

## The cold load

Measured once, on 23 October 2026, at 390px with the same 4x throttle and an
empty cache: FCP and LCP 1,092ms, CLS 0.0738, 186,353 bytes over the wire. It
is a snapshot rather than a gate. The budgets above hold the two interactions,
and no check holds the first paint, so a change that doubled the photos would
not fail the build.

## Why the phone sort is now 7 to 14ms

The sort's own JavaScript was never the cost. It is 5 to 16ms: read the
`data-*` values, sort fourteen elements, re-append them. What followed was
Chromium laying out fourteen cards that together run to about 5,000px, and at
390px that was the whole task: 45 to 221ms at 4x, one long task per sort.

The phone cards now carry `content-visibility: auto` with
`contain-intrinsic-size: auto 410px`. A card below the fold is not laid out,
so a sort lays out the three or four cards in view instead of all fourteen.
The `auto` in the intrinsic size is what makes it affordable: the 410px
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

The cost is paid at first paint, before any card has been measured: the 410px
estimate is 443px of card, against real cards of 404 to 506px, so the page
lands within about 2% of its settled height and moves only below the reader's
fold. At 390 in the desktop preview that is 7,970 against 8,078px. Chrome's
scroll anchoring held it in thirty-four 150px steps with no jump. Nothing is hidden: the skipped cards stay in
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

The grid tracks started as the widths the table chose, so the desktop layout
did not move: the columns were 34, 337, 120, 84, 102, 109, 114 and 348px
against the table's 33, 337, 120, 84, 102, 109, 114 and 349px. The first track
carried 2px for the collapsed table border that sat there until ADR 6 made the
rows grid tracks; there is no border left to pay for, so ADR 18 made the track
40px, the compare box's own width. ADR 10 has since put a floor under
every header word and takes the two cost columns to 152px from 1280px, so the
columns are the table's own only where no word forces them wider.

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

1280px was exact because the tracks were read off the table there; with the
floors of ADR 10 the table is 1,420px tall against 1,419px before. Between 900
and 1100 the columns differ by 2 to 6% and a row can be one line of text taller
or shorter, which is the 1% of table height in the table above. The "cells
clipping" column counts a cell's own overflow, which misses a sentence painted
across its chevron: the 821px and 900px rows carried that defect until ADR 13,
where at 821 the catch track was 68px, its words ended 51px past the chevron's
left edge and the sentence ran to 20 lines. Below 901px the catch now takes the
row, no cell clips at any measured width, no page scrolls sideways, and every
row's cells start on the header's columns to the pixel. The audit measures 821,
900 and 901 as well.

The sources column has changed three times since that measurement: `c36b321`
put it beside the copy above 1100px, ADR 11 brought it down to 821px and split
the list above 1100px, and ADR 14 capped the copy at 80ch and split the list
again at 1200 and 1300px. Measured today, with every card settled, the page is
2,680px at 1440, 2,818 at 1300, 2,920 at 1280, 3,064 at 1200, 3,552 at 1101,
4,465 at 1100, 4,628 at 1000, 4,874 at 940, 5,100 at 900 and 5,454 at 821. ADR
11's second list took 971px off 1280 (4,232 to 3,261 against the same column in
one list) and 907px off 1101, and the single list beside the copy added 359px
from 821 to 1100 (5,100 to 5,459 at 900), where two lists would have left the
copy 319px wide at 821. ADR 13's catch band took 323px off 900 and 1,736px off
821 before that. ADR 14's 80ch cap and extra lists then take 446px off 1440 and
307px off 1280, and add 101px at 821, where the copy is 561px wide instead of
468 and the list 196 instead of 289. ADR 15's record footnote then takes 20px
off 1440, 17 off 1280 and 36 off 900. ADR 16's 118px record track takes a
further 11px off 1440, 17 off 1300 and 17 off 1280, and gives the wrapped
labels their words back at both widths. ADR 17's record band takes 17px off
1200, and ADR 18's first track takes 19 off 940, the one width where the
catch's extra 2px removes a line. ADR 20's filter row then takes 36px off
1440, 1280 and 901 and gives 4px back at 821, where the row has no width to
gain: the option groups that wrapped at every desktop width now share a line,
and the price slider is 285px at 1280 where it was 178. The table is 2,191px
at 900 against 2,513, and 2,330 at 821 against 4,066. The 820px and 390px
pages are below the phone breakpoint and are not affected.

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

## Why the compare open allows 500ms

Opening the comparison runs through `document.startViewTransition`: the
browser captures the old viewport, runs the update, captures the new one, and
only then paints the panel. The panel's first paint therefore waits for one
snapshot it did not wait for before.

The 18-row table is built before the transition starts, not in its update
callback. Built inside, the render and the snapshot's layout of it ran as one
task of 53 to 77ms at this throttle; built first, while the panel is still
hidden — and therefore hidden in the snapshot of the old frame either way —
the build is off the panel's critical path. The build is remembered by its
three column ids, so the `tray()` call inside the transition does not build it
a second time.

Only the named boxes are captured: the stylesheet turns the root's transition
name off, so the page behind the tray is not rendered into a picture and no
whole-page cross-fade runs. Seven are captured instead — the tray, the header,
and the three ticked rows' names and photos — and every one of them costs a
paint of its own at this throttle. Measured against the same open without the
transition, three captures cost 50 to 120ms and six cost 100 to 180ms, so a
capture is 25 to 30ms: the page cannot make one cheaper, only take fewer.

A ticked row is rendered from the moment it is ticked, not uncontained inside
the open. A contained row that is off screen has no box to capture, and the
first version set `content-visibility: visible` on the three rows just before
capturing them, which laid each row out for the first time inside the open.
Uncontaining at the tick instead costs 30 to 47ms, runs no task, and happens
while the reader is looking at the row they just ticked. At most three rows
are ever ticked, so at most three rows stop being contained.

Measured over three opens per run at this throttle: 115 to 237ms with the
flight, and 42 to 75ms with it switched off, which is the same panel built,
scrolled and painted on reduced motion. That second figure is the one the
budget keeps at 150ms, so the panel's own work stays where it was. The flight's
line is 500ms and deliberately loose: on a machine doing other work it has
measured 310 to 630ms, and the page cannot make a capture cheaper. What holds
the cost down is the count — seven boxes and no more — and that is a structural
claim, so `compare morph` asserts a captured group for every name and photo and
fails if anything else joins them, where this check would only see a number.

Closing runs the same seven captures the other way, so the same ceiling applies
there. `compare morph` asserts the reverse frames too: six pairs named on the
header before the close, six on the rows after it, and nothing left named once
the panel has gone.

That figure is about waiting, and it is not enough on its own: an open that
painted late after a long task still feels like a stall. The second line is
about the main thread — the median of the three opens' longest tasks, which
must stay under 120ms. The captures are that task, so the line sits above what
seven of them cost and below what a whole-page capture did.

## Why the back-to-top button listens to scroll

The button appears once the reader is past the sentinel above the table. An
`IntersectionObserver` looks like the cheaper way to know, and it was the first
version: it reports a *change* in intersection, so a jump from above the
sentinel to below it — End, a link that restores a scroll position, a tab
switch — never crosses it, and the button stayed hidden exactly when the reader
had scrolled furthest. The listener reads one rectangle through
`requestAnimationFrame`, so a burst of scroll events costs one layout read a
frame, and the boolean it writes is the same on every frame where nothing has
moved, so the assignment reflects no attribute change.

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
