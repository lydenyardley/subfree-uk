⚠️ DEGRADED: single-context (no design sub-agent is exposed; the only
sub-agent available is web research, with no workspace or browser access)

```
──────────── ⚡ OVERDRIVE ─────────────
》》》 Entering overdrive mode...
```

# Impeccable overdrive: SubFree UK

- Target: `index.html`, the 14-row UK video doorbell comparison
- Run: 19 October 2026, read-only
- Mode: Read plus Operate
- Gate: no direction was built on the page. Directions B and C are mocked up
  in `docs/mockups/overdrive-tray-table.html`, which is the prototype the
  "pick before building" step asks for. The performance budget it names now
  lives in `docs/performance-budget.md`.

## What extraordinary means here

This is a functional comparison page used on a phone, often in a shop or on a
sofa, minutes before a purchase. Confetti, shaders and scroll-jacking would be
embarrassing. The right wow is the feeling that the page is faster and more
certain than a web page has any right to be: the verdict becomes the
comparison without a page load, and every number still shows its working.

The page already has the fundamentals: a single inline document, no external
scripts, instant filtering, a compute-on-demand cost row. Overdrive should
spend its ambition on one moment, not five.

## Direction A: The reader's own ledger

**What it looks like.** The compare tray grows a single control: a plan-price
assumption slider, defaulting to the page's own figure. Drag it and every
selected model's three-year cost and difference update in place, with a small
line that says what changed. The ranking order follows.

**Technique.** No new dependency. Plain input event, a 60fps-safe number
update, and a FLIP reorder of at most three selected rows.

**Trade-offs.** Highest intellectual payoff and the strongest fit with the
page's "we showed our working" voice. It also risks implying a precision the
data does not have: a reader could read the slider as a quote. It needs a
caption that the plan price is an assumption, and the page already has the
sentence to reuse. Interaction cost is real on a phone.

**Risk:** medium. New state, new copy, new guardrails.

## Direction B: Verdict to comparison, one continuous object

**What it looks like.** The reader ticks the top pick and taps Compare in the
sticky tray. The tray does not disappear while a new panel appears. Instead it
lifts, expands into the compare table, and the three chosen rows slide into
their columns. Tapping Close returns the table to the tray. The motion is short
(220 to 260ms), interruptible, and only runs when it can run well.

**Technique.** Same-document View Transitions, which the reference lists as
supported in all browsers, with a feature detect and an instant fallback. Give
the tray `view-transition-name: cmp-tray` and each compare row a stable name.
Skip the transition when `prefers-reduced-motion: reduce`, when the selection
count changes, and on the first paint. No library.

**Trade-offs.** Strongest visible "a website did that" moment, and it explains
the relationship between the tray and the table, which is currently spatial
only. Cost is one transition per open, no layout animation on sort. Risk of
feeling showy is low because the object is the reader's own selection.

**Risk:** low to medium. Native API, graceful fallback, one authored moment.

## Direction C: The instrument panel

**What it looks like.** The table never janks, at any sort, on a mid-range
phone. The score bars paint with `scaleX`, sorting reorders the 14 row blocks
without animating layout, and a hairline progress rule along the table edge
shows where the reader is in those rows. A tiny sticky line echoes the current
model's verdict as it passes. No entry animations, no reveals.

**Technique.** Fix the 14 `transition: width` warnings, delete the forced
reflow and 14 timers that redraw the bars on every sort, and add a
scroll-driven `animation-timeline: scroll()` rule for the progress rule inside
`@supports`, with a static rule as fallback. Firefox without the flag sees the
static rule. Add containment to the phone row blocks only if a measurement
shows it helps; table rows do not always take `content-visibility` cleanly.

**Trade-offs.** This is the invisible wow, and it suits a page whose pitch is
"instant". It is also the least memorable in a demo. The scroll-linked rule
must not become a scroll-jack; it only reports position.

**Risk:** low. Mostly subtraction and one CSS feature with a fallback.

## Recommendation

Build B, borrow C's performance work as its foundation, and leave A for a
later release.

B is the only direction that turns an existing relationship (tray to table)
into a felt one, and it uses the reader's own action as the trigger. C is
required either way: a cinematic transition on a janky sort would expose the
seams. A adds a new claim surface and should wait until the page has a way to
label assumptions per model, which it does not.

Do not layer B and A. One extraordinary moment.

## Numbered suggestions

1. Finish C. The width animations and the forced reflow are gone, and a
   sort's script now runs in 5 to 15ms at 4x throttle. Two pieces remain: the
   14 timers that draw the ripple on a re-sort nobody needs twice, and the
   layout pass that still costs 65 to 90ms, which is the open line in
   `docs/performance-budget.md`.
2. Add the sticky current-model verdict line only if it can be read by a
   screen reader without announcing on every scroll. If not, skip it.
3. Add the plan-price assumption control (Direction A) in a later release,
   with a visible "assumption, not a quote" caption and no change to the
   default ranking.

## Shipped (20 October 2026)

B and the hairline rule are in `build/build.py`, with `morph_check` and
`rule_check` guarding them in `build/check.py`.

- The tray and the compare header share one `view-transition-name`. They are
  never on screen together any more, so one name is always exactly one box:
  no clearing dance, and nothing else in the page is named. 240ms on one
  easing curve, opened and closed through `startViewTransition`.
- The old bar leaves in 100ms and the new one arrives after, rather than the
  two cross-fading in one box. A still frame of the midpoint showed both
  texts stacked and translucent.
- Reduced motion and a missing API both fall back to the instant swap. The
  page cross-fade is off, so the table behind the pair does not ghost.
- The tray now leaves while the comparison is open, which is what makes the
  move real. Clear moved into the panel's actions so nothing was lost, and
  focus lands on the panel's heading on open and back on the tray's Compare on
  close. Without that, the button that opened it left focus on the body; the
  section itself announced every cell, so the heading took the focus instead.

**Deviation from suggestion 3.** The three chosen rows are not named. In the
mockup the list is replaced by the panel, so a row can leave and arrive as a
column. On the real page the table stays, so a named row is painted twice for
the length of the transition, once in place and once flying to its column, or
it has to vanish for 240ms. One pair carries the moment; four would have made
it a crowd.

**Deviation from suggestion 4.** The rule is driven by a view timeline on the
table's box (`--tbl`, full cover range), not `scroll(root)`. Page progress and
table progress differ by the mast, the controls and the method block, and the
rule sits on the table's own top edge, where it is the header's hairline once
the header sticks.

## Mockup

`docs/mockups/overdrive-tray-table.html` is the prototype these came from: a
tray that lifts into the compare panel, named rows, and the hairline rule with
a feature readout, a reduced-motion path and an instant fallback. It stays as
the record of what was compared; the page is now the authority.

## What the build actually does

- Wrap the compare open and close state change in `document.startViewTransition`
  when it exists.
- One name on the tray and the compare header. They are mutually exclusive, so
  two elements never share it and no names have to be cleared.
- `::view-transition-group(cmp-tray)` runs 240ms on one easing curve. Old and
  new bars hand over instead of cross-fading. Reduced motion skips the call.
- Focus moves to the panel's heading on open and back to the tray on close,
  because the control that opened the panel is no longer on screen. Verified by
  keyboard: open, Tab reaches the panel's actions, close returns to Compare.
- The rule is a 2px sticky hairline inside the table's box, filled by a view
  timeline across the table's cover range, with `animation-range: cover`.
  Without timelines it is the plain hairline, and print hides it.

## Never

- No sound. No haptics on a web page without a clear reason.
- No scroll-jacking, no pinned sections, no parallax on a comparison table.
- No animation on filter or sort. The reader is working; the page should not
  perform.
- No glassmorphism, glow or gradient mesh. The visual world is editorial.
- No second extraordinary moment in the same release.

## Verify

- **The wow test:** show the tray-to-table transition to someone who has not
  seen the page. Do they notice the object continuity, or just a fade?
- **The removal test:** disable the transition. The page still works and still
  reads as considered. If it feels broken without it, the transition is
  masking a layout problem.
- **The device test:** a throttled mid-range phone, keyboard only, and reduced
  motion all behave.
- **The context test:** the motion reads as the reader's selection moving, not
  as decoration.

## Run notes

- Read-only. Only this document was written.
- The overdrive banner sits after the degraded marker because the audit is a
  document, and the marker must lead the file.
- Evidence: live preview at 1280 and 390, the generated page, the 19 October
  critique and delight audits, and the detector's 14 layout-transition
  warnings.
- Suggested follow-through: `$impeccable animate` for B, then `$impeccable
  optimize` for C.
