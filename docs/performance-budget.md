# Performance budget

The page exists for one phone interaction: change the sort, or open the
comparison, and see the answer. These are the numbers that keep that
interaction instant on a mid-range phone.

Measured on the built page at a 390px viewport with a 4x CPU throttle, which
is the closest a desktop browser gets to a mid-range Android phone.

| Budget | Target | Measured 20 October 2026 | Status |
|---|---|---|---|
| Sort response | under 100ms | 5 to 16ms of script | Met |
| Compare response | under 100ms | 15 to 20ms | Met |
| Longest task during a sort | under 50ms | 65 to 125ms | **Open** |
| Table movement when the tray opens | 0px | 0px | Met |

## How to measure

`python build/check.py` applies `Emulation.setCPUThrottlingRate` at 4 for the
length of the check, dispatches four sorts and a compare, and prints the
slowest sort, the compare response and the longest long task seen during the
sorts. The response and shift lines fail the build; the long-task figure is
printed because it more than doubles between runs on the same machine, which
is why the budget records it instead of gating on it. An open Details row
makes it worse: with all fourteen open it measured 110ms.

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
