# 24. The overdrive audit, and the source card it left open

- Status: Accepted. Direction A is built, B is declined, and C is the one item
  still open.
- Date: 26 October 2026
- Source: the 23 October 2026 overdrive audit, removed with this record. Every
  item it raised is settled below, with the check or the measurement that holds
  it. Its sketch for A, `docs/mockups/2026-10-25-overdrive-a.html`, is removed
  for the same reason the audit is: the page is the sketch now.

## Context

The audit asked what would make this page extraordinary, given that it is a
comparison rather than a landing page, and answered that the comparison was
still a table the reader read rather than an object they manipulated. It
proposed three directions. A is the comparison instrument the reader
arranges, shipped on 25 October and recorded in ADR 23. B is a budget-first
page that leads with a draggable budget and hides the table behind it. C is a
source card that opens from the figure the reader doubts. The audit recommended
A as the signature with C as its supporting layer, and declined B.

## The eight numbered items

| Item | Outcome |
|---|---|
| O1, one signature | Held. The instrument is the page's extraordinary moment, nothing was built alongside it, and B is declined below. |
| O2, keep the flight | Held. `compare morph` is unchanged, and `build/page.js` calls `startViewTransition` in two places only, the open and the close, so a drag never starts a capture. |
| O3, a real handle | Built. The 26 by 18px grip in a 44px target on the rule, Pointer Events under pointer capture, whole columns moved, and Left, Right, Home and End on each handle. `compare column move` and `compare column keys` hold it, and both fail on the build before it with `no column handle on …`. |
| O4, recompose on drop | Built. The drag writes one transform per cell per frame and rebuilds the table once, when the column lands. Measured on 26 October at 4x CPU throttle, three runs of one 341px drag: 45, 46 and 46 frames over 765, 782 and 782ms, every frame 17ms, no long task. It is held by that measurement and by nothing else, because no check times a drag. |
| O5, collapse identical rows | Already the page, in the shape ADR 5 chose. The panel's own control carries the count, reads "Differences only (N identical)" with N counted over the three ticked models, hides the rows where all three agree, and leaves the four decision rows standing. O5 would add an automatic collapse and a spring, not a number the reader cannot already see. ADR 5 declined the counted line and asks for evidence before it reopens, so the motion is a decision the owner has not taken rather than work waiting to be done. |
| O6, the source card | Open. This is C, the one thing this audit leaves undecided. It has its own section below. |
| O7, gate on the budgets | Held. `performance budget` passes with the drag on the page, the reduced-motion run has no slide, and the no-JavaScript run keeps every price and both 3-year figures. The cold load the audit quoted is the 186,353 bytes recorded in `docs/performance-budget.md`, and no WebGL, third-party script or font has been added since. |
| O8, named checks | Held for A, and both fail on the build before it. C's `source card` and O5's `compare spring` arrive with those two, if either is built. |

## What remains open: C, the source card

Every figure in the instrument would carry its own source. The reader taps or
clicks a price, a 3-year total or a verdict, and a card opens showing the source
name, the URL, the date the price was checked and the sentence that supports
the claim. On a desktop a hover peek shows the same card without a click; on a
phone a tap opens it as a popover.

The data is already on the page. `ROWS` carries `price_src`, `rec_src`,
`history_src` and `ha_src`, `S` carries each source's name and URL, and
`CHECKED_ISO` carries the date. The card adds no request and no claim, and it
puts the page's strongest promise, that every price is checkable, where the
reader first doubts a number.

The bar it has to clear, from the audit:

- A price opens a card with the right source name and URL.
- Escape closes it and returns focus to the figure that opened it.
- The Popover API with `popovertarget` where it exists, and the details panel
  where it does not.
- A `<div role="dialog">` with a close button, so the card is announced and
  dismissible rather than a hover-only shape.
- `source card`, in `build/checks/behaviour.py`, red on the build before it.

The audit had this waiting on O5's answer, because both reshape what a reader
can open from a cell. O5's answer is ADR 5's, and it keeps the rows as hidden
rows rather than turning them into a counted line, so there is no new kind of
cell for a card to open from. C is unblocked and waiting only on the owner.

## Declined: the budget-first page (B)

The price slider would have become the first control, the page would have
answered "3 models keep recordings under £360 for three years" with a ranked
strip, and the table would have become the evidence below it. That is a product
change rather than a UI change. It makes the page answer a different question
first, and it hides the comparison, which is the page's best asset. The
existing price filter already does the job for a reader who arrives with a
budget.

Reopening condition: the owner wants the page to lead with budget rather than
with the comparison.

## The bar for the next moment

A future candidate for the page's next extraordinary moment answers four
questions, which are the audit's own tests and worth keeping:

- Does a reader pick it up unaided? If it needs a caption, the affordance is
  not there.
- Does the page feel worse without it? If nobody notices, it was decoration.
- Does it hold on a 390px phone, a 1280px laptop and a 4x CPU profile?
- Can the page's promise, no tracking and no affiliate links and every price
  checkable, survive it?

## Consequences

- `docs/audits/` and `docs/mockups/` hold nothing now, so both are gone from
  the tree. An audit or a sketch recreates its folder when one runs, and the
  README lists neither.
- The two numbers the audit leaned on, the cold load's 186,353 bytes and the
  compare open's 500ms and 150ms lines, live in `docs/performance-budget.md`
  and in `performance budget`, which are the homes that fail when they move.
- The drag's frame rate is the one acceptance criterion in the audit with no
  check behind it. A gate would need a new measurement inside
  `performance.py`, which the owner has not asked for.
