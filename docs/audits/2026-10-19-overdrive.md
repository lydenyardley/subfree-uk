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
2. Add the tray-to-table View Transition behind a feature detect, with the
   reduced-motion and first-paint guards. Fall back to today's instant swap.
3. Name only the tray and the three compare rows for the transition. Do not
   name the 18 table rows; that turns one authored moment into a crowd.
4. Add a hairline progress rule along the table using `animation-timeline:
   scroll()` inside `@supports`, and a static rule otherwise. Never hijack
   scroll.
5. Add the sticky current-model verdict line only if it can be read by a
   screen reader without announcing on every scroll. If not, skip it.
6. Add the plan-price assumption control (Direction A) in a later release,
   with a visible "assumption, not a quote" caption and no change to the
   default ranking.

## Mockup

`docs/mockups/overdrive-tray-table.html` carries suggestions 2, 3 and 4 in one
standalone file: a tray that lifts into the compare panel through
`document.startViewTransition`, names only the tray and the chosen rows, and a
hairline rule driven by `animation-timeline: scroll()` inside `@supports`. It
has a feature readout, a reduced-motion path and an instant fallback. Open it,
tick two or three rows and press Compare.

## Implementation sketch for B

- Wrap the compare open and close state change in `document.startViewTransition`
  when it exists.
- Give the tray a stable `view-transition-name`, and give each selected row a
  name derived from its model slug. Clear the names before the next paint so
  two elements never share one.
- Set `::view-transition-group(...)` duration to 240ms and a single easing
  curve. Respect `prefers-reduced-motion` by skipping the call entirely.
- Do not change where focus lands. Check the current focus target and Escape
  behaviour before the change, and verify both again after it. The transition
  must not steal or delay focus.
- Measure with a performance trace on a mid-range Android profile; the
  transition itself should not add a long task.

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
