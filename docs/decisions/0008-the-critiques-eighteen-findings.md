# 8. The design critique's eighteen findings

- Status: Accepted
- Date: 22 October 2026
- Source: `docs/audits/2026-10-21-critiquito-design-critique.md`, items 1 to
  18. The measurements are in `docs/performance-budget.md` and in the check
  names below.

## Context

A read-only critique of the live page, with screenshots at 1280px and 390px,
found three things that cost a visitor the main task: the default sort was by
a figure no column showed, so the list read as mis-sorted; the phone's
side-by-side comparison cut the third product off with no sign that it
scrolled; and the intro promised that each price links to its source while
every price was plain text. Fifteen more findings were smaller. This record
covers all eighteen in one pass, and names the check that holds each one. The
audit document stays, because its screenshots are the before.

## The list reads as sorted

**The order follows a figure the row bolds (1).** The derived `keep_basis`
says which of the two 3-year figures `keep3` came from, and `keep_note` says
it in words (`records free, no plan`, `with the Ring Solo plan`). The cell that
figure comes from starts bold in the no-JavaScript page, `markSort()` bolds it
after every sort, and `#sortnote` names the figure under the control. Ring now
sits where its £259.63 plan cost puts it, with the plan named beside the
figure. `sort figure` picks each sort that has a figure, asserts exactly one
bold cost cell per row and that it is the right one, and asserts no bold cell
is left when sorting by a column of its own.

**Every price opens the page it came from (3).** Each price is an `<a
class="buy">` to its row's `price_src`, with the shop in its name and `nofollow
noopener` on the link, and the details' source list prints the sources by name
(`Reolink UK: Battery Doorbell PoE`) instead of by footnote number. `price
links` reads every row's price cell, the link's name and its rel, and the
Reolink details' source names.

**The two cost headers are written out (11).** They read `3-year cost, no
plan` and `3-year cost, with plan` at 12px, up from 10px of `3 YRS, NO PLAN ᵃ`,
and each letter beside them is a link to the working under the table (`#m-a`,
`#m-b`) rather than a superscript to hunt for. `cost header name` asserts the
words, the size, the letter, the target and that the target exists.

## The comparison

**The cue to swipe is above the table, and names a column you cannot see (2).**
`#cmp-cue` sits under the comparison's header, where the reader looks first; at
the foot of a 1,700px table it was a screen and a half below the column it
named. `cmpCueUpdate()` names the first column that starts past the right edge
— the one that is out of sight altogether, not the one that is half in view —
and `.cmp-wrap::after` fades the edge. The label column narrowed from 84 to
76px. `comparison scroller` asserts the cue is above the table, visible, and
that its words are `Swipe to see ` plus the first column whose left edge is
past the scroll box's right edge.

**The compare box is named (6).** The desktop layout names the column in its
header, at the same 12px as the rest. A phone card has no header, so the box
carries the card's own muted caption (`COMPARE`) under it. The caption sits in
a 60px rail with an 8px gutter, which gives the two figure columns back the
width a 64px rail would have taken, so the caption costs a card 2px rather
than 26px. `compare label` asserts the header at 1280, the caption at 390, the
12px floor on both, and that the whole label is at least 44px by 44px.

**The cost row says what it is made of (4).** It is now `Cheapest way to record
for 3 years`, each cell an absolute total first (`£259.63`) with the difference
as the secondary figure and the basis in small text under it (`with the Ring
Solo plan`). `compare cost row` reads every cell and the row's label.

**The comparison marks what is missing, and leaves good news alone (14).** A
cell that starts with `None` is marked in the avoid colour, and the record
column reuses the list's own record marker so a `No` reads the same in both
places. Two rows are left unmarked on purpose: `None` in the plan row and in
the paywall row is the cheapest and most open option on the page, and painting
it red would warn a reader off it. `compare markers` reads five rows of a
three-model comparison and asserts one marker, one marked storage cell, one
marked history cell, and nothing marked in the plan or paywall rows.

**A fourth box is refused, not greyed out (15).** Nothing is disabled at three
selections. The fourth tick is undone and `#cmp-cap` says `You can compare 3.
Untick one to swap.` beside the count, with the same words announced. The rule
applies to a reader's tap only: a `?cmp=` link or a test that sets the
selection is not second-guessed. `compare cap` clicks a fourth box and asserts
three remain ticked and the message is visible and announced.

## Trust

**The page ends with a person (10).** The footer repeats the date, links the
repository, gives a plain email address and a way back, and the back-to-top
button appears once the reader is past the sentinel above the table.
`closing line` asserts the owner, the email, the link, and the button: hidden
at the top, visible after the table, and landing focus on the `h1`.

**A mistyped address lands on the site (9).** `build.py` now writes `404.html`
in the page's own styles, with `Page not found`, one line of explanation, the
site's stylesheet at the same content version, and a `See the doorbell
comparison` button back to the site root, root-relative so it works at any
depth. `not found` asserts the file exists, its heading, its link, that it is
`noindex`, that it wears the stylesheet, and that it does not point at GitHub.
It is in `GENERATED`, so a stale copy fails `rebuild` too.

**The row colours are explained (13).** `#vkey` above the table says what
green, blue and red mean in words. At 390px the key is hidden and the short
answer's three coloured lines carry it instead, which is finding 8's fix.
`page key` asserts the key is visible with three entries at 1280, that it does
not describe the styling rather than the verdict, and that at 390 the key is
gone and the three lines are there.

*Reverted on 22 October 2026, at the owner's request: the key did not earn its
space, because every badge already names its verdict in words and the
comparison's header rule is now the page's ink rather than a second colour
code. `#vkey`, its styles and the `page key` check are gone.*

**Dark mode dims the photo tiles (16).** `--imgbg` is `#2b2a28` in both dark
rules with `--imgf:brightness(.78)`, and the free-features bar's track uses
`--rule` rather than `--rule2`. `theme toggle` switches to dark, reads the tile
behind a photo and asserts it is dim.

**The lightbox has three ways out (17).** A close button in the corner, a tap
anywhere off the photo, and Escape. The magnifier badge sits at 55% rather than
invisible until hover, so a desktop reader can see the photos enlarge.
`photo lightbox` opens a photo, closes it with the corner button, and closes it
again with a click off the photo.

## The phone

**A card is a third shorter (7).** The two 3-year figures share a row in the
card's grid (`3 years, no plan` beside `3 years, with plan`) instead of each
taking a line, and the label block is tighter. `labels` reads the top of the
figure in every card, not of its cell: the two cells always start level, so a
cell box says nothing about the two numbers inside them. Both labels reserve
two lines, so a label that wraps does not push its number a line below the one
it is being compared with, and because the row was already as tall as the
wrapped one, no card grew. `phone containment` still holds the cards to one
contained block each.

**The phone keeps the short answer's reasons (8).** All three lines are there
at 390px, each in its own colour with its border, rather than the one condensed
sentence that dropped the reasons and the warning about Blink and Arlo.

**The filter that emptied the list is named (5).** `#empty-txt` says which
filters the range excludes (`no doorbell costs between £40 and £40`), the
recovery button says which control it moves (`Raise the maximum to £45`), and
`#f-range` prints the range as words above the slider, so two thumbs on top of
each other still read. `empty result` asserts the message names the price and
the doorbells, and that the button says `maximum`, `minimum` or `Show`;
`price slider` asserts the range text matches the handles and follows them.

## The details panel

**Every value is a sentence (18).** `PLAIN` holds the power and storage
sentences for all fourteen rows, keyed by id, and the build refuses a row with
no entry or an entry with no row. The panel's pairs are one grid in two
columns, so the left and right halves line up. `details panel` opens the
Reolink row, asserts the pairs sit at exactly two left offsets, and that the
power and storage lines are sentences rather than term lists.

## Deliberately unchanged

**The comparison still scrolls sideways.** The critique offered stacking it as
one card per attribute. The table keeps its pinned label column and a cue
instead: a card per attribute would put the three values out of line with each
other at the moment the reader is comparing three things, which is the job the
panel exists for.

**The desktop rail keeps a single box.** A `Compare` label beside every one of
fourteen checkboxes would be forty-two words of noise down a column that the
header already names. The desktop gets the column header, the phone gets the
caption.

**The cost headers keep a link, not a tooltip.** The critique suggested
explaining the columns on hover or tap. A marker link to the working works on
a phone and for a keyboard, and a tooltip does neither.

**The card estimate stays 330px.** The cards now run to 441px, so the estimate
is further below the tallest card than it was. Raising it to cover the tallest
would reserve 470px for every card and lengthen the page by about a thousand
pixels to hide a gap the reader never sees: an off-screen contained card is
not painted, so its clipped overflow is invisible until it is laid out at its
real height. `contain-intrinsic-size:auto 330px` stays, and the comment in
`page.css` says what the number is for.## What the review of this change found

Three of the eighteen fixes were wrong in a state nobody had looked at, and
each was found by using the page rather than by reading the diff.

**Every printed column sat one place to the left.** Printing hides the compare
box; a hidden grid cell leaves its track behind, so the seven cells that were
left started one track to the left of the seven headings above them. On A4
landscape that put each price under the heading before it. The heading and the
track now go with the box, and `print` asserts, at 1123px with print media on,
that no compare cell is displayed and that every cell starts at its heading's
left edge. The defect predates this change, but naming the column made it
print a word that did not belong to anything.

**The two 3-year figures did not line up.** `3 years, with plan` wraps to two
lines in a 145px column and `3 years, no plan` does not, so the plan figure sat
15px below the no-plan figure in every card. Both labels now reserve two lines,
and `labels` measures the figure's own top edge in all fourteen cards instead
of the top edge of the two cells, which always matched.

**axe called a skipped card's Details button obscured.** A card below the fold
is contained and not painted, so its contents overflow a box that is only the
330px estimate, and axe reads that box as a clip: `target-size`, 2 nodes in
dark and 1 in light, only in Firefox. In both engines a card in view is never
clipped, so this was the audit reading a tree no reader can see rather than a
defect. `axe_violations()` now lays every card out with a style tag for the
measurement and removes it afterwards, the same way the performance budget
measures the uncontained page. No rule is turned off, and the strict state is
the one a reader scrolls through.

## Consequences

- `build/check.py` is now one command with 72 named checks. Five are new
  (`sort figure`, `price links`, `compare label`, `details panel`, `not
  found`), `print` is new from the review above, and seven were extended
  (`comparison scroller`, `price slider`, `cost header name`, `theme toggle`,
  `photo lightbox`, `closing line`, `labels`), each proved to fail on the change
  it guards.
- `404.html` joins the generated files. A build that changes the stylesheet's
  version changes the 404 with it, and the audit fails if the file is stale.
- The back-to-top button listens to scroll through `requestAnimationFrame`
  instead of an `IntersectionObserver`, because a jump past the sentinel never
  crosses the observer and the button stayed hidden in exactly the case it was
  for. `docs/performance-budget.md` records the cost.
- The compare open keeps its 150ms budget. Turning off the root's transition
  name removes a snapshot that was never visible; the measurement could not
  separate it from machine noise, so the budget stands unchanged.
