# 24. The overdrive audit, and the source card

- Status: Accepted. Directions A and C are built and B is declined, so the audit
  leaves nothing open. The card's weight and its stylesheet rule count are
  corrected in ADR 25.
- Date: 26 October 2026
- Source: the 23 October 2026 overdrive audit, removed with this record. Every
  item it raised is settled below, with the check or the measurement that holds
  it. Its sketches, `docs/mockups/2026-10-25-overdrive-a.html` for A and
  `docs/mockups/2026-10-26-source-card.html` for C, are removed for the same
  reason the audit is: the page is the sketch now.

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
| O6, the source card | Built by C, below, on 26 October. Every figure with a claim behind it opens a card holding the page, the row's own sentence, the day the prices were checked and, for a 3-year total, the sum it is made of. `source card` holds it. |
| O7, gate on the budgets | Held. `performance budget` passes with the drag on the page, the reduced-motion run has no slide, and the no-JavaScript run keeps every price and both 3-year figures. The cold load the audit quoted is the 186,353 bytes recorded in `docs/performance-budget.md`, and no WebGL, third-party script or font has been added since. |
| O8, named checks | Held for A and for C, and each fails on the build before it. O5's `compare spring` would arrive with O5, if the owner ever wants it. |

## Built: C, the source card

Every figure with a claim behind it opens its own card: the price, the record
verdict, both 3-year totals, the history line and the Home Assistant line, in
the table and again in the comparison. The card prints the source's name and
URL, the day the prices and plans were checked, the row's own sentence for that
claim, and, for a 3-year total, the sum the figure is made of with every page it
is built from, the uncited card price included as an assumption. `source card`,
in `build/checks/behaviour.py`, holds all of it. ADR 26 prices that card from
its own page in the same list, so the card's arithmetic no longer carries a
figure the reader has to take on trust.

The trigger is the figure itself, and it is an ordinary link to the page the
figure came from. Without a script, and on paper, the click goes where it always
said it would; with a script it opens the card instead. A middle click or a
command-click still leaves for the source, which is what the anchor is for.

The comparison carries one 3-year total per column rather than two, and that
total is whichever of the row's two figures is the cheaper route. Its card is
the one behind that route: `data-keep` names the route, the no-plan figure or the
plan's, and the card follows it, so the number a reader doubts opens the page the
number came from rather than the other route's.

The audit's case was that no new data is needed, and for four of the figures
that holds. `ROWS` carries `price_src`, `rec_src`, `history_src` and `ha_src`,
`S` carries each source's name and URL, and `CHECKED_ISO` carries the date. The
card adds no request and no claim, and it puts the page's strongest promise,
that every price is checkable, where the reader first doubts a number.

The bar it had to clear, from the audit, and how each line was answered:

| The audit's bar | Outcome |
|---|---|
| A price opens a card with the right source name and URL | Built. The address is the one the anchor already carried, and the name and URL are read out of the register by number, so the page still holds each URL once. |
| Escape closes it and returns focus to the figure that opened it | Built. The card is a `<dialog>`, so Escape, the backdrop and the return of focus are the browser's own; `source card` drives the close and reads the focus back. |
| The Popover API with `popovertarget` where it exists, and the details panel where it does not | Declined. `showModal()` is already proven on this page by the photo lightbox, and `<dialog>` is the one element that gives the top layer, Escape, a modal backdrop and the return of focus with no polyfill and no second shape to keep true. |
| A `<div role="dialog">` with a close button, so the card is announced and dismissible rather than a hover-only shape | Built as a `<dialog>` with a close button: the same thing, with the announcement and the dismissal in the element rather than in the attributes. |
| A hover peek on a desktop | Declined. A peek cannot be reached by keyboard or by touch, so the click path has to exist anyway, and two shapes showing one fact are two things to keep true. |
| `source card`, in `build/checks/behaviour.py`, red on the build before it | Built. It drives the table's figures, the comparison's figures and a phone's, and it fails on the build before it. |

The audit had this waiting on O5's answer, because both reshape what a reader
can open from a cell. O5's answer is ADR 5's, and it keeps the rows as hidden
rows rather than turning them into a counted line, so there is no new kind of
cell for a card to open from.

One kind of card the sketch drew was not built: the page's own call for a
verdict. A verdict is the page's judgement of the row's cited figures rather
than a fact with a page behind it, and no claim key in `ROWS` stands behind it,
so a card there would have had to invent the source it prints. Adding one means
adding a claim key and a page behind the verdict first.

### The one data change it needed

One thing the audit assumed was already in place was not. `ROWS` named a source
for the price, the recording claim, the history and the Home Assistant line, but
the plan's page lived only in the row's footnote list, so a card on the plan
column had no claim key to read. All fourteen rows now carry `plan_src`: the
page that publishes the plan's price, or, where the row has no plan, the page
that says none is needed, which is Hikvision's datasheet, Reolink's doorbell FAQ
and Aqara's specifications page. It obeys the rule the other four claim keys do,
that the key also appears in the row's `src` list, and `row_problems()` fails the
build by name when it does not.

### The provenance that moved, and the part that did not

The footnote numbers in the cells and the register at the foot of the page are
what the card replaces: with a script, every figure carries its own page and the
foot no longer has to. Both stay in the markup and are hidden by the script,
because two readers cannot open a card. The printed sheet gets them back: the
print block puts the markers and the register on the page and takes the
underline off the figures, which open nothing on paper. The reader without a
script is unchanged from before, and the figures are the better for it, because
the words that were plain text are now links to the pages behind them.

The row's own `Sources:` line stays for everyone, and its links go straight to
the pages rather than to the register. With the numbers gone it is the row's
citation list, and it is the only route to the sources that carry no claim key:
the independent reviews, the manuals and the terms pages.

### Measurements

The page grew 6,358 bytes compressed across its three files: 2,988 in the HTML,
which is 84 triggers with the source names in their labels and 66 row source
links that now carry the page's own addresses rather than a fragment, 605 in the
stylesheet and 2,765 in the script. No budget holds page weight anywhere in this
repo, so this is a recorded measurement rather than a gate.

The card itself is one `<dialog>`, 64 lines of script and nine stylesheet rules.
On a desk it opens 8px under the figure that was tapped, against the viewport
edge where that would push it off, and on a phone it docks to the bottom so the
figure it came from stays on the screen; `source card` measures both.

### Where the mockup went

`docs/mockups/2026-10-26-source-card.html`, drawn on 26 October and checked at
1280px and 390px, was never committed to the tree, and it is not kept: it went
the way of the sketch for A, because the page is the sketch now. It showed the
trigger, the hover peek, the three kinds of card, the card opening from a row,
and what it unblocks for the footnote numbers and the sources line; the two
shapes it drew that are not here, the peek and the verdict card, are declined
above.

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
  the tree and the README lists neither. An audit or a sketch recreates its
  folder when one runs. The source card's sketch was the last thing in
  `docs/mockups/`, and it went with the same reasoning as the sketch for A: the
  page is the sketch now, and a drawing of a design that has moved on is a
  second, older description of the same page.
- The two numbers the audit leaned on, the cold load's 186,353 bytes and the
  compare open's 500ms and 150ms lines, live in `docs/performance-budget.md`
  and in `performance budget`, which are the homes that fail when they move.
- The drag's frame rate is the one acceptance criterion in the audit with no
  check behind it. A gate would need a new measurement inside
  `performance.py`, which the owner has not asked for.
