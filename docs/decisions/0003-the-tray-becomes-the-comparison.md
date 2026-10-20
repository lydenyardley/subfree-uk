# 3. The tray becomes the comparison

- Status: Accepted
- Date: 20 October 2026
- Source: the overdrive audit of 19 October 2026, items 2, 3 and 4, and its
  tray-to-table prototype. Both are gone; the design they produced is below,
  and ADR 5 records what was declined.

## Context

The tray said "3 selected" and the comparison appeared somewhere above the
table. Nothing on screen said the panel was those three rows, and the page is
5,000px of cards on a phone with no sense of how much of it is left.

The audit asked for one authored moment: the tray lifts into the panel, and a
hairline reports where the reader is in the table. It also warned against
naming the eighteen table rows, which would turn one moment into a crowd.

## Decision

### The tray and the compare header are the same box

Both carry `view-transition-name: cmp-tray`, and they are never on screen
together. That last part is the change: while the comparison is open the tray
leaves, because a shared box that stays put cannot move. Clear moved into the
panel's actions so the tray's only unique job was not lost.

One name, one box, no clearing dance. Nothing else in the page is named. Open
and close run through `document.startViewTransition` at 240ms on one easing
curve; the page's own cross-fade is disabled so the table does not ghost
behind the pair.

The old bar leaves in 100ms and the new one arrives after. A still frame of the
first cross-fade showed both bars' text stacked and translucent in one box.

### The three chosen rows are not named

In the prototype the list is replaced by the panel, so a row can leave as a row
and arrive as a column. Here the table stays. A named row would be painted
twice for the length of the transition, once in place and once flying to its
column, or would have to vanish for 240ms from the table the reader is reading.
One pair carries the moment.

### Focus follows the control that left

The button that opens the comparison is hidden by opening it. On open, focus
moves to the panel's heading (`tabindex="-1"`), which announces "Side by side,
heading level 2"; on close, back to the tray's Compare. Focusing the section
itself was tried first and named every cell in the table. Without either,
opening from the keyboard dropped focus on the body and the next Tab restarted
at the top of the page.

### The rule reports the table, not the page

A 2px sticky hairline on the table's top edge, filled by a view timeline on the
table's box across its full cover range. `scroll(root)` would have measured the
whole page, and the table's progress and the page's differ by the mast, the
controls and the method block. The timeline only follows scroll; it never
changes it, and it is `aria-hidden` decoration.

Without `animation-timeline` support the `@supports` block never applies and
the hairline is the plain 2px track. Print hides it.

## Consequences

- The tray and the panel are no longer open at the same time. Anything that
  cleared the selection from the tray now clears it from the panel.
- The tray's cap hint ("maximum, untick one to swap") is not shown while
  comparing. The three ticked boxes and the disabled fourth stay in the table,
  and the count line still names the number.
- A future panel that wants a transition names at most one more element, and
  that element must leave the flow. A stationary duplicate is not a candidate.
- `morph_check`, `head_check` and `rule_check` in `build/check.py` fail the
  build if the two names diverge, if a second element is named, if the duration
  or the root suppression changes, if reduced motion or a missing API stops
  opening the panel, if the header's heading wraps or its links split, or if
  the rule stops growing with scroll.
- The panel's header is three rows at 390 (heading, the differences label, the
  three links) and one row from 820 up. Adding a fourth action is a header
  redesign, not a new link.
