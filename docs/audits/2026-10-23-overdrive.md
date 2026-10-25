```
──────────── ⚡ OVERDRIVE ─────────────
》》》 Entering overdrive mode...
```

# The 23 October 2026 overdrive audit

- Status: Proposal. Direction A is mocked up for the owner's judgement, B is
  declined, C is deferred.
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
| A. The comparison instrument | They move one model against another and watch the difference change | Pointer Events, CSS transforms, FLIP for row collapse, the existing view transition for open and close | Medium: 3 to 5 days, 4 to 6KB, a new check family | The current table | Build |
| B. The budget-first answer | They drag a budget and the page answers with a ranked strip | The existing price filter promoted to the first control, FLIP reflow, `@property` for the count | High: it changes the information architecture and hides the table | The current filter | Decline |
| C. Sources in situ | They tap a figure and the claim opens with its page, date, and quote | Popover API, the existing `S` data, the existing view transition | Low: 1 to 2 days, 2 to 3KB | The details panel | Build with A |

### Direction A, the comparison instrument

The reader picks two models. The compare panel opens as it does now. A vertical divider sits between the two model columns. The reader drags it left or right. The column under the divider moves, the delta chips recompute against the fixed column, and the rows that are identical collapse into one line with a count. When the reader lets go, the divider snaps to the nearest column edge. On a keyboard, the divider is a slider with Left and Right moving it by one column, and Home and End jumping to the ends.

The numbers are already in the DOM. The deltas are already computed in `buildCmp()`. The interaction adds a pointer layer and a re-render of three cells, not a new data path.

The wow is not the drag. It is that the drag makes the £90 difference physical. The reader sees the cheaper column and the dearer column move against each other, and the delta changes as they move. That is the thing a static table cannot do.

`docs/mockups/2026-10-25-overdrive-a.html` is that shape in one file: three real
models, a 44px divider with a 2px line, the swap under pointer capture, the
delta chips named against the baseline, and the shared rows collapsed into one
line with a count. Verified in Chromium at 1280 and 900: the pair moves, the
count goes 6 to 2, the keyboard swaps and resets, and reduced motion lands
without a slide. Two things the mockup cannot answer, because they are the
owner's calls. Whether a collapsed line may hide the third column's differences
on those rows, and whether the instrument replaces "Differences only" or sits
beside it.

The phone does not get the drag. At 390px there is room for one model column and a sliver of the next. The phone gets the snap and the truthful cue from R2, plus a two-model toggle that swaps the visible column. The instrument is a 821px-and-wider interaction.

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

### O3. Make the divider a real control, with keyboard parity (P1)

Use Pointer Events with `setPointerCapture`. The divider is a `<button role="slider">` with `aria-valuemin`, `aria-valuemax`, `aria-valuenow`, and `aria-valuetext` naming the two models. Left and Right move it by one column. Home and End jump to the ends. Escape returns it to the midpoint. The visual divider is 2px, and the hit area is 44px.

**Acceptance.** A pointer drag moves the divider and recomputes the delta. Arrow keys do the same. The accessible name and value change with the position. The hit area is at least 44px.

### O4. Recompute only the three cells that change (P1)

A drag updates the fixed column's delta chips and the divider position. It does not rebuild the table. Cache the column widths and the row values on open, and write `textContent` to the delta chips on each frame. Use `requestAnimationFrame`, and stop when the pointer stops.

**Acceptance.** A drag at 4x CPU holds 60fps, or the page falls back to the snap-only version. No layout is read inside the frame loop after the first measurement.

### O5. Collapse identical rows with a spring, and keep the count (P2)

When the reader drags one column over another, rows whose values match collapse to one line. The line says how many rows are identical (for example, "12 of 17 rows are identical") and the four decision rows stay. Use a CSS grid row transition or a FLIP on the row heights, not a JavaScript height animation.

**Acceptance.** The collapse runs at 60fps, the count matches the rows hidden, and the "Differences only" toggle and the collapse do not fight each other.

### O6. Put the source card on every figure in the instrument (P1)

The card opens from a price, a 3-year total, or a verdict. It shows the source name, the URL, the date, and the sentence. Use the Popover API with `popovertarget`, and fall back to the existing details panel when the API is missing. The card is a `<div role="dialog">` with a close button and Escape.

**Acceptance.** A price opens a card with the right source name and URL. Escape closes it and returns focus to the figure. The card works with JavaScript on and degrades to the details panel without it.

### O7. Gate the work on the existing budgets (P1)

The drag must hold 60fps at 4x CPU, or it does not ship. The source card must not add a network request. The page stays under the current 186KB transfer on a cold load, or the owner accepts the delta in `docs/performance-budget.md`. `prefers-reduced-motion` keeps the snap and removes the spring and the card morph. No WebGL, no third-party script, no new font.

**Acceptance.** `performance budget` passes with the new interaction. The reduced-motion run has no transition and no spring. The no-JS run still shows every price and both 3-year figures.

### O8. Add named checks, and prove each one fails on the old build (P1)

Add four checks to the existing families:

- `compare drag`, in `build/checks/compare.py`: drag the divider, assert the delta changes and the fixed column does not move.
- `compare keyboard`, in `build/checks/accessibility.py`: focus the divider, press Left and Right, assert the value and the accessible text.
- `source card`, in `build/checks/behaviour.py`: open a card from a price, assert the source name, URL, and date, close with Escape, assert focus returns.
- `compare spring`, in `build/checks/performance.py`: run the collapse at 4x CPU and assert the frame budget, with the reduced-motion fallback.

Each check must fail when the feature is reverted. A check that passes on the old build proves nothing.

**Acceptance.** Four new named checks, each red on the old build and green on the new one. `python build/check.py` stays one command.

## The tests

- **Wow.** Show the drag to someone who has not seen the page. Do they move the divider without being told? If they need a caption, the affordance is not there.
- **Removal.** Take the drag away. Does the page feel worse, or does nobody notice? If nobody notices, the drag is decoration.
- **Device.** Run it on a 390px phone, a 1280px laptop, and a 4x CPU profile. The phone gets the snap, not the drag. The laptop holds 60fps. The slow profile falls back.
- **Context.** Does it make sense for a page whose promise is "no tracking, no affiliate links, check every price"? The source card does. A particle system would not.

## What this does not change

The prices, the sources, the 14 models, the default sort, the table as the evidence, the no-tracking promise, the print sheet, or the no-JS list. The instrument is a new way to read the same data.

## Where this stands

A is mocked up, not accepted. Look at it, and say whether the gesture earns its
place on the page, whether the collapsed line is allowed to hide the third
column's differences, and whether "Differences only" survives it. C is deferred
until that answer, because a source card on a comparison that is still being
reshaped would be built twice.

The critique's P1 items landed in ADR 22, so O3 can start on the page whenever the
owner wants it.
