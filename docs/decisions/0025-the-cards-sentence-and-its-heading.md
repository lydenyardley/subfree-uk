# 25. The card's sentence, and its heading

- Status: Accepted
- Date: 26 October 2026
- Source: the owner's report of 26 October 2026, the day after the source card
  landed in ADR 24. Two things: the Nest row's "Records free?" figure reads
  "Only briefly (3 hrs)" and the card it opens read "None"; and the card's
  heading sat below the line of its close button.

## Context

The card prints "the row's own sentence for that claim", and the claims were
built from the fields that look nearest to their figures. The recording verdict
printed `storage`, and on thirteen rows that reads fine, because a microSD card
or a hub is both where footage goes and why the doorbell records for nothing.
Nest is the row where the two answers part company: it has no local storage at
all and keeps three free hours in Google's cloud, so a figure reading "Only
briefly (3 hrs)" carried a card reading "None", which is the answer to a
different question. The same sentence served the no-plan total, so the row's
"£179.99 = £179.99 (3 hours of history only)" also had "None" under it.

The heading was pushed below the button by the card's 3rem of top padding,
which was there to keep the text clear of an absolutely positioned close
button. The title therefore started at 49px down a card that is often 160px
tall, reading as a card that opened halfway down itself.

## Decision

**A card's sentence answers the question in its own title.** "Records free
without a plan" is the recording question, so it prints the row's `history`
line, which is the dataset's own "Recorded history without subscription". Where
the sentence and the figure rest on different pages the card lists both, because
a sentence has to be checkable where the card says it came from: Arlo's card
names its blog post and its 2nd-gen FAQ, and EZVIZ's names the Amazon listing
and the UK no-subscription guide.

"The 3-year cost with no plan" prints what the sum buys. Where the sum adds
kit, that is the storage line, which names the SmartHub that £115 of Arlo's sum
is for and the Sync Module 2 in Blink's; where it adds nothing, it is the
history line, which is what Nest's £179.99 gets. The assumption note in the
card and this sentence now travel together, since both exist only when the sum
buys something beyond the doorbell.

**The heading and the close button share the card's first row.** The card is a
two-column grid, the title in a `minmax(0,1fr)` column and the button in an
`auto` one, so the column is the button's own width and the two cannot drift
apart; a long title wraps inside its column rather than under the button. Both
tops sit at the card's 12px padding, so they are flush, and the card's top
padding no longer has to clear an absolutely positioned button.

## The regression the review caught

The first version put `display:grid` on `#card` itself, and an author `display`
on a `<dialog>` overrides the browser's own rule for one that is not open. The
closed card stayed on the page, 340 by 163px, holding the last figure's
evidence, and the audit's axe pass merely noted an empty heading in it. The grid
is now gated on `#card[open]`, and `source card` reads the closed card's
`display` and its box, so a card left painted fails by name.

## Consequences

- `source card` reads both recording cards on every row, 28 cards, against the
  rule restated from `ROWS` rather than from the build, so a card that drifts
  fails instead of agreeing with a copy of the build's mistake. It also
  measures the heading's row, its clearance from the button and the closed
  card's rendering. On the build before this record it reports 26 findings:
  thirteen recording cards quoting the storage line, the two missing history
  pages, and three heading measurements (49px down, 40px off the button's line,
  28px under the button).
- Two pages joined two cards. Arlo's recording card lists its blog and its FAQ,
  and EZVIZ's recording and no-plan cards list the Amazon listing and the UK
  no-subscription guide, where the no-plan card used to name the listing twice.
- The card's stylesheet is eleven rules, from nine: the `[open]` gate and the
  close button's placement in the grid. The script is unchanged at 64 lines.
- Across the three files the card now costs 6,507 compressed bytes over the
  build before it, 3,007 in the HTML, 749 in the stylesheet and 2,751 in the
  script, against the 6,358 recorded in ADR 24. Nothing in this repo budgets
  page weight, so this is a measurement rather than a gate.
