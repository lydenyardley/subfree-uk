# Performance budget

The page exists for one phone interaction: change the sort, or open the
comparison, and see the answer. These are the numbers that keep that
interaction instant on a mid-range phone.

Measured on the built page at a 390px viewport with a 4x CPU throttle, which
is the closest a desktop browser gets to a mid-range Android phone.

| Budget | Target | Measured 20 October 2026 | Status |
|---|---|---|---|
| Sort response | under 100ms | 5 to 16ms of script | Met |
| Compare open, transition included | under 150ms, median of 3 | 83 to 122ms warm; 119 to 171ms on the first open | Met |
| Longest task during a sort | under 50ms | 65 to 125ms | **Open** |
| Longest task when the compare opens | under 50ms | none over 50ms in 3 runs | Met |
| Table movement when the tray opens | 0px | 0px | Met |

## How to measure

`python build/check.py` applies `Emulation.setCPUThrottlingRate` at 4 for the
length of the check, dispatches four sorts and three compare opens, and prints
the slowest sort, the three opens, the longest long task seen during the sorts
and the longest one seen while the comparison opens. The response, shift
and compare-task lines fail the build; the sort's long-task figure is printed
because it more than doubles between runs on the same machine, which is why the
budget records it instead of gating on it. An open Details row
makes it worse: with all fourteen open it measured 110ms.

## Why the compare open allows 150ms

Opening the comparison now runs through `document.startViewTransition`: the
browser captures the old viewport, runs the update, captures the new one, and
only then paints the panel. The panel's first paint therefore waits for one
snapshot it did not wait for before, which is one to two frames at this
throttle. The page's own share is the 18-row render, 4 to 20ms.

Measured over three opens per run: 83 to 122ms warm across nine runs, and 119
to 171ms on the first open of a session, which pays the snapshot pipeline's
warm-up. The spread tracks machine load, which is why the check takes the
median of three and prints all three rather than trusting one number. 150ms is
the line at which the capture has become a stall rather than a frame; a change
that doubles the page's share lands well past it.

## Why the long-task line is open

The sort's own JavaScript is 5 to 16ms. The rest of the task is Chromium
laying out 14 card blocks that together run to about 5,000px, and a
`:has`-free reorder of that much content cannot avoid a layout pass.

The forced reflow that used to sit in `drawBars`, a `void tbl.offsetWidth`
after fourteen transform writes, was 40 to 70ms of that pass and bought
nothing: the `setTimeout` boundary already commits the zeroed bars, so the
draw still restarts from zero and animates to the score.

`content-visibility: auto` with `contain-intrinsic-size` on the phone cards
was measured too. It cut the longest task to 58ms and added 84px of page
height from the size estimate, so it is not in yet: 58ms is still over the
ceiling, and the height is a cost the page would pay on every visit.

Next step: take the cards out of the sort's layout path entirely, either by
containing off-screen cards once the intrinsic-size estimate stops costing
height, or by sorting only the row headers and leaving the card bodies out of
flow. Either needs a fresh measurement against this table, not a guess.
