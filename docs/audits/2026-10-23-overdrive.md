```
──────────── ⚡ OVERDRIVE ─────────────
》》》 Entering overdrive mode...
```

# The 23 October 2026 overdrive audit

- Status: A's arrangement is built, B is declined, C and O5 are deferred.
- Date: 23 October 2026
- Target: `index.html`, `build/page.css`, `build/page.js`
- Mockup: `docs/mockups/2026-10-25-overdrive-a.html`
- Companion: ADR 22, which closed the critique this audit builds on.

## What "extraordinary" means here

This is a functional comparison page, not a landing page. A shader background or a particle system would be wrong. The reader is deciding how to spend £45 to £295 on a doorbell and £55 to £468 over three years. The "wow" is the page doing the arithmetic in the reader's hands, at 60fps, with the source one gesture away.

The page already goes beyond the baseline. The ticked rows fly their name and photo into the comparison column on a 240ms curve, with a 500ms budget and a reduced-motion fallback. The compare panel opens without a view transition when the reader asks for less motion. The table header sticks, the compare tray stays in reach, and the whole page is 186KB with no third-party script.

The gap is not visual ambition. It is that the comparison is still a table you read, not an object you manipulate. The reader can tick three models and see a side-by-side table. They cannot take one column and move it against another to see the £90 difference land.

## What already exists, so this does not rebuild it

- The row-to-column flight is `compare morph`, recorded in ADR 0009. It names six parts, runs on the tray's curve, and cleans up on `finished` with a 700ms backstop.
- The compare open is measured twice. The panel's own work stays under 150ms. The flight gets 500ms.
- `prefers-reduced-motion` skips the flight and keeps the panel.
- The compare cost row already prints the total, the delta, and the basis.
- The source data for every claim is in `ROWS` and `S`. No new fetch is needed for a source card.

## Three directions

| Direction | What the reader feels | Technique | Cost | Fallback | Verdict |
|---|---|---|---|---|---|
| A. The comparison instrument | They arrange three models and watch the differences follow | Pointer Events, CSS transforms, FLIP for row collapse, the existing view transition for open and close | Medium: 3 to 5 days, 4 to 6KB, a new check family | The current table | Build |
| B. The budget-first answer | They drag a budget and the page answers with a ranked strip | The existing price filter promoted to the first control, FLIP reflow, `@property` for the count | High: it changes the information architecture and hides the table | The current filter | Decline |
| C. Sources in situ | They tap a figure and the claim opens with its page, date, and quote | Popover API, the existing `S` data, the existing view transition | Low: 1 to 2 days, 2 to 3KB | The details panel | Build with A |

### Direction A, the comparison instrument

The reader picks three models, and the compare panel opens as it does now. Each column carries a small handle clipped onto the 3px rule under its photo. The reader drags the handle left or right, and the column takes its neighbour's slot, or goes to the far end. The whole column travels, the cost row included, and so does its verdict rule, so a green header is always the column that earned it. The figures do not travel: every delta names the cheapest of the three, wherever its column sits, so a move changes the order the columns are read in and never the arithmetic. On a keyboard, each handle is a button: Left and Right move the column one place, and Home and End send it to either end.

The numbers are already in the DOM. The deltas are already computed in `buildCmp()`. The interaction adds a pointer layer, a column order and a rebuild when the column lands, not a new data path.

The wow is not the drag. It is that the reader decides which model they read first, and the £45 difference is still the same fact two columns later. A column that can be moved is a comparison the reader is arranging, not one the page has fixed for them.

The first shape of this direction was one divider between two columns, swapped as the divider passed. The owner replaced it with a handle per column on 25 October, so the gesture arranges the comparison instead of pushing one column through a gap.

`docs/mockups/2026-10-25-overdrive-a.html` is that shape in one file: three real
models, a handle clipped onto each column's rule, the drag under pointer
capture, the whole column moving with the pointer, and the shared rows collapsed
into one line with a count. Verified in Chromium at 1280 and 900: the column
lands in its slot, the cost cell moves with it, the share line reads 2 of 13,
focus returns to the handle, Escape restores the order, pointercancel drops the
gesture, and reduced motion lands without a slide.

The owner accepted it on 25 October with four changes, and the page carries all
four. The verdict rule stays with its column through the move. The handle is a
six-dot grip, not three bars. The handle is never cut by the column it passes,
so a column in flight paints above its neighbours. And the reference stays put.
The sketch measured its deltas against the column on the left, which was the
question it was drawn to ask; the page measures them against the cheapest of the
three, so a move reorders the reading and never the figures.

The phone does not get the drag. At 390px there is room for one model column and a sliver of the next, so the phone keeps the snap and the truthful cue from R2, and the instrument is an 821px-and-wider interaction.

### Direction B, the budget-first answer

The price slider becomes the first control. The reader drags a budget and the page answers "3 models keep recordings under £360 for three years" with a ranked strip. The table becomes the evidence below.

This is a product change dressed as a UI change. It makes the page answer a different question first, and it hides the comparison that is the page's best asset. The existing filter already does the job for a reader who wants it. Decline it for now. Revisit only if the owner wants the page to lead with budget rather than with the comparison.

### Direction C, sources in situ

Every figure in the instrument gets a source card. The reader taps a price, a 3-year total, or a verdict, and a card morphs from the figure. The card shows the source name, the URL, the date checked, and the sentence that supports the claim. On a desktop, a hover peek shows the same card without a click. On a phone, a tap opens it as a popover.

The data is already there. `ROWS` has `price_src`, `rec_src`, `history_src`, and `ha_src`. `S` has the name and URL. `CHECKED_ISO` has the date. The card adds no network request and no new claim. It makes the page's strongest promise, that every price is checkable, visible at the moment the reader doubts a number.

## Recommendation

Build A as the signature, with C as its supporting layer. Do not build B.

One moment, not three. The comparison instrument is the thing a reader will show someone else. The source card is the thing that makes them trust it. The budget-first rewrite would compete with both and weaken the table.

## Numbered recommendations

### O1. Choose one signature, and say no to the rest (P1)

The page's next extraordinary moment is the comparison instrument. Every other proposal waits. A page with three wow moments has none.

**Acceptance.** The change adds one interaction that a reader can describe in a sentence: "I can drag one doorbell against another and see the difference."

### O2. Keep the existing flight, and do not rebuild it (P1)

The name and photo flight is already recorded and measured. The drag state should reuse the panel and the columns, not replace the open transition. Add a `data-dragging` state that turns off the view transition names while the pointer is down, so a drag never starts a second capture.

**Acceptance.** `compare morph` still passes unchanged. A drag does not call `startViewTransition`.

### O3. Make the handle a real control, with keyboard parity (P1)

Use Pointer Events with `setPointerCapture`. Each column's handle is a `<button>` whose accessible name carries the model and its place, for example "Move EZVIZ DB2 Pro Kit left or right. Column 2 of 3." A drag moves the column to the slot nearest the pointer when it lands, and the column glides there. Left and Right move it one place, Home and End send it to an end. The visible clip is 26px by 18px with its centre on the 3px rule. The target is 44px and sits in the header's empty strip, so the price row underneath stays clickable.

**Acceptance.** A pointer drag moves a column and rebuilds the table in the new order. The deltas do not change, because they name the cheapest column wherever it sits. Arrow keys do the same. The accessible name carries the position. The target is at least 44px and covers no part of the cost row.

### O4. Recompose on drop, not on every frame (P1)

A drag moves the column with the pointer and slides its neighbour aside. It does not rebuild the table mid-gesture. Cache the column offsets on pick-up, write one transform per cell per frame, and rebuild once, when the column lands. Use `requestAnimationFrame`, and stop when the pointer stops.

**Acceptance.** A drag at 4x CPU holds 60fps, or the page falls back to the snap-only version. No layout is read inside the frame loop after the first measurement.

### O5. Collapse identical rows with a spring, and keep the count (P2)

Rows where all three models agree collapse to one line. The line says how many rows that is (for example, "2 of 13 rows identical in all three") and the four decision rows stay. Use a CSS grid row transition or a FLIP on the row heights, not a JavaScript height animation.

**Acceptance.** The collapse runs at 60fps, the count matches the rows hidden, and the "Differences only" toggle and the collapse do not fight each other.

### O6. Put the source card on every figure in the instrument (P1)

The card opens from a price, a 3-year total, or a verdict. It shows the source name, the URL, the date, and the sentence. Use the Popover API with `popovertarget`, and fall back to the existing details panel when the API is missing. The card is a `<div role="dialog">` with a close button and Escape.

**Acceptance.** A price opens a card with the right source name and URL. Escape closes it and returns focus to the figure. The card works with JavaScript on and degrades to the details panel without it.

### O7. Gate the work on the existing budgets (P1)

The drag must hold 60fps at 4x CPU, or it does not ship. The source card must not add a network request. The page stays under the current 186KB transfer on a cold load, or the owner accepts the delta in `docs/performance-budget.md`. `prefers-reduced-motion` keeps the snap and removes the spring and the card morph. No WebGL, no third-party script, no new font.

**Acceptance.** `performance budget` passes with the new interaction. The reduced-motion run has no transition and no spring. The no-JS run still shows every price and both 3-year figures.

### O8. Add named checks, and prove each one fails on the old build (P1)

The two checks the arrangement needs are in place:

- `compare column move`, in `build/checks/compare.py`: drag a column's handle by one slot, assert the order and the cost row follow, the figures do not, the verdict rule stays with its column, focus returns to the handle, and the move is announced. It also measures the handle: its centre on the rule, its 44px target clear of the price row, and its grip inside the table.
- `compare column keys`, in `build/checks/accessibility.py`: focus a handle, press Right, Left, End and Home, and assert the order, the focus, the name's column number and the live text.

The collapse's check (`compare spring`, in `performance.py`) and the source
card's (`source card`, in `behaviour.py`) arrive with O5 and C.

Each check must fail when the feature is reverted. A check that passes on the old build proves nothing.

**Acceptance.** Two new named checks, each red on the old build and green on the new one. On the old build both report `no column handle on …`. `python build/check.py` stays one command.

## The tests

- **Wow.** Show the drag to someone who has not seen the page. Do they pick up a column without being told? If they need a caption, the affordance is not there.
- **Removal.** Take the drag away. Does the page feel worse, or does nobody notice? If nobody notices, the drag is decoration.
- **Device.** Run it on a 390px phone, a 1280px laptop, and a 4x CPU profile. The phone gets the snap, not the drag. The laptop holds 60fps. The slow profile falls back.
- **Context.** Does it make sense for a page whose promise is "no tracking, no affiliate links, check every price"? The source card does. A particle system would not.

## What this does not change

The prices, the sources, the 14 models, the default sort, the table as the evidence, the no-tracking promise, the print sheet, or the no-JS list. The instrument is a new way to read the same data.

## Where this stands

A's arrangement is on the page: `compare column move` and `compare column keys`
hold it, and `performance budget`, `axe WCAG` and the Firefox structural pass
still pass. The verdict rule travels with its column, the cost row's tint sits on
the row so a column in flight cannot tear a gap through it, and the address
carries the arrangement alongside the selection.

What is not built: O5's collapsed line (the panel still has the
"Differences only" toggle) and C's source card. C waits for O5's answer, because
both reshape what a reader can open from a cell.

The critique's P1 items landed in ADR 22. The arrangement's own record is ADR 23.
