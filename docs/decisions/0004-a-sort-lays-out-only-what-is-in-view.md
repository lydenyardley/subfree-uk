# 4. A sort lays out only what is in view

- Status: Accepted
- Date: 20 October 2026
- Source: the overdrive audit of 19 October 2026, item 1 (Direction C), and
  the measurements in `docs/performance-budget.md`.

## Context

The page claims to be instant, and sorting is where it was not. A sort
re-appends fourteen `tbody` elements and Chromium lays the table out again.
At 390px that is 5,000px of cards, so the layout was the whole task: 45 to
221ms at 4x CPU throttle, one long task per sort. The script itself was never
the cost.

The same sort also set fourteen score bars to zero and ran fourteen
`setTimeout`s to draw them back. The bars are `aria-hidden` decoration, so the
ripple carried no information, and it ran on the interaction the reader
repeats most.

## Decision

### The score bars are painted once, at their score

The build writes `transform:scaleX(score/8)` into the markup. `drawBars`, its
timer array and the `transition` on the fill are gone, and a sort no longer
touches a bar. Nothing on the page moves when the reader sorts, which is what
the design rules asked for.

### The phone cards are contained

`.main-t tbody.item` carries `content-visibility:auto` and
`contain-intrinsic-size:auto 330px`, inside the phone media query only. A card
below the fold is not laid out, so a sort lays out the three or four cards in
view and nothing else.

`auto` in the intrinsic size is what makes this shippable. The first paint uses
a 330px content estimate, 363px of card with its padding and rule, and
remembers the real height once a card has been laid out, so the estimate is
only paid for cards the reader has not reached. Real cards measure 331 to
409px, so the first paint lands within about 2% of the settled height, in
whichever direction the reader's fonts push it: 6,620 against 6,613px in the
audit browser, 6,688 against 6,832px in the desktop preview. All of that
movement is below the fold, and Chrome's scroll anchoring held it: thirty-four
150px scroll steps moved the reader by 0px.

### The desktop table is not contained, and that is named

`content-visibility` does not apply to table rows, and the desktop cost is the
table's own column balancing rather than the cards. At 1280px the sort's task
is 70 to 150ms at 4x in either state: this change does nothing there, and the
check prints that figure without gating it. The budget's sort line is the
phone, where the reader is and where the numbers above apply.

## Consequences

- A 390px sort and its layout measures 6.6 to 14ms (median 9.3, eighteen sorts
  in three runs) against 44.8 to 221.3ms without the containment.
- `perf_check` gates the figure at 50ms, and it fails at 75.7ms when the
  containment is removed. The measurement forces the sort's layout with an
  `offsetHeight` read inside the same task, because a long-task observer only
  reports what the browser chooses to schedule and it missed the work entirely
  at 1280px in one run.
- `bars_check` asserts all fourteen bars sit at their score and that a sort
  leaves every `transform` untouched, so re-adding a redraw fails the build.
- Print is unaffected: a 390px-wide PDF of the page has the same 28 pages and
  the same text with the containment on or off, and all fourteen "Best for"
  lines survive.
- The accessibility tree is unaffected: `content-visibility:auto` keeps the
  skipped subtree exposed, and the last card at 5,210px is still in the tree.
- A jump to a card lands in the same place (centred, 227px from the top) with
  the containment on or off, because the estimate is close to the real card.
- The sort no longer has any motion. A future idea to animate it has to argue
  against this record, not just add a transition.
