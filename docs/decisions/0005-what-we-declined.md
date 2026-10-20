# 5. What we declined

- Status: Accepted
- Date: 20 October 2026
- Source: the four read-only audits of 19 October 2026. All four are now
  completed, implemented or decided, and their documents are removed. This is
  the last thing they had left to say.

## Context

Each audit ended in numbered suggestions. Most shipped: the labels that
matched the data, the shorter proof, the tray that becomes the comparison, the
static score bars and the contained phone cards. The rest are declined here,
with the reason and the evidence, so the next pass argues against a recorded
decision instead of rediscovering the idea.

## Distill

### 1. A counted line where identical rows collapse: declined

The count is already in the control. The label reads "Differences only (4
identical)", and the toggle is one tap away from the rows it hid. A line inside
the table would repeat the number in the one place the reader is scanning for
differences, and it would sit among the decision rows that never collapse,
describing rows somewhere else in the panel.

### 3. Shorten the "Best for" lines to six words: declined

Those lines are sourced data, not copy. Each one is the claim the row's
footnotes support, and the qualifier is usually what makes it true: "records to
a card, cloud optional" becomes a different, unsourced claim at six words. The
page keeps its claims in `ROWS` next to their sources, so a rewrite of fourteen
of them is a sourcing pass, not an edit. Nothing measured says the length costs
the reader anything; what was expensive on a phone was the label column, and
that shipped.

### 4. Move Local / Home Assistant behind a disclosure: declined

The audit called it not transformative, and it is the arrival question for one
specific reader. Below 821px every filter is behind the Filters disclosure
already, so the desktop honour is the only change, and it would hide the single
non-price axis from a reader who came to ask exactly that question. Eight
visible controls is not a measured problem; the page is a decision surface and
the controls are the search.

## Delight

### 1. A closing line naming the trade: declined

The page's rule is that every sentence is backed by a source or by arithmetic
it shows. "The cheapest three-year cost versus the model tagged easiest setup"
is a verdict about a trade this particular reader may not be making, and the
cost row already computes that trade for the three models they chose. Written
once for everyone, it either picks for the reader or repeats the row.

### 3. "Widen the budget to £295 to include Hikvision": declined

Measured at 390px: the current label, "Show Hikvision DS-KB6003-WIP at £295",
is one 24px line and the empty state is 110px tall. The proposed wording wraps
to two lines and makes the panel 153px. It also opens on the mechanism rather
than the outcome, and the sentence above it has just said why nothing matched.
The recovery is a named model and a way out; the explanation is one sentence
too many at the moment the reader is stuck.

### 4. "Back to the short answer" after the last row: declined

The problem is orientation inside the table, and the sticky table header
already solves it: a reader at row 14 can see that they are at row 14. The page
ends in the method and a closing line that already carries a way back to the
table. A second jump link turns the ending into a menu and spends 44px of
target height at the bottom of a 6,600px page, which is the one place a reader
is leaving rather than arriving.

## Overdrive

### 2. A sticky current-model verdict line: declined

A line that follows the scroll changes with every row, and it has only two
forms. As a live region it announces on scroll, which breaks the
one-announcement-per-action contract. As decoration it repeats what the card
already says as it passes. It would also be a second sticky band on a phone,
directly under the sticky table header. The verdict tag is printed in the row.

### 3. The plan-price assumption slider (Direction A): declined

It adds a claim surface. The page has exactly one plan assumption, Ring's £10,
and it is labelled in the sentence that uses it as uncited. A slider would put
a control on that single guess and produce a number that reads as a quote. It
would also reorder the comparison while the reader drags, and the page reserves
reordering for the reader's own filters.

Reopening condition: plan prices sourced from each vendor's UK page. At that
point the plan cost is data, and the control is a filter rather than an
assumption.

## Rules that survive

- One extraordinary moment per release.
- No sound, no haptics, no scroll-jacking, no pinned sections, no parallax on
  a comparison table.
- No animation on filter or sort. The reader is working.
- Delight copy introduces no new facts.
- A declined idea comes back with evidence, not with a redesign of the page
  around it.

## Consequences

The audit documents and the tray-to-table prototype are removed. ADR 3 holds
the design they produced, including where the build deviates from the prototype
and why; ADR 4 holds the sort work they finished. A future audit starts from
these records rather than from the originals, and a suggestion listed here
needs a measurement or a source to reopen it.
