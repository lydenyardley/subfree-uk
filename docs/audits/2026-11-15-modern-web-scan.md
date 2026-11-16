# Modern Web Guidance scan, 15 November 2026

A read-only pass with `npx modern-web-guidance@latest legacy-scan .`, run on
15 November 2026 against this repo. No site code was changed.

## Method

The scanner is part of Modern Web Guidance 1.0. It checked 33 guides (35
deterministic rules, about 20% of the catalogue) and reported three matches
across two guides, `dark-mode-toggle` and `dialog`. Those matches are
provisional: each was read back against its keep/drop rubric, the retrieved
guide (`npx modern-web-guidance retrieve <id>`), and the source that emits the
page — `build/page.js`, `build/page.css` and `build/build.py` — not only the
generated `assets/` copies the scanner pointed at.

This is a public site, so a suggestion is kept only when Safari and Firefox
already support the feature, or when the guide itself supplies a light
fallback. Volatile or Chromium-only features are out.

## Relation to earlier audits

This pass does not reopen work that is already recorded elsewhere:

- `docs/performance-budget.md` holds the byte and interaction ceilings. They
  already pass, and the deterministic scan found no speed finding to add.
- `docs/decisions/0007-the-audits-twenty-findings.md` through
  `docs/decisions/0029-the-architecture-audits-six-findings.md` record the
  October and mid-November audits that were implemented and then deleted.
  ADR 8 already covers the theme toggle and the lightbox's three ways out;
  ADR 24 already chose `<dialog showModal()>` for the source card and
  declined the Popover API. Those decisions stand.
- `docs/audits/2026-10-28-design-critique.md` is still in the tree. Its
  comparison-header and score-card notes are design work, not legacy-API
  work.
- Three later audits sit uncommitted in the owner's checkout and are not on
  `main`: `docs/audits/2026-11-07-deep-app-audit.md`,
  `docs/audits/2026-11-07-impeccable-route-critique.md` and
  `docs/audits/2026-11-11-visual-audit.md`. They already cover the privacy
  wording around GoatCounter, the comparison losing model names when the
  header scrolls away, and category discovery. Nothing below repeats them.

The scanner only looks for a subset of legacy patterns. It is not a
substitute for those audits, and it reported no SEO finding.

## Findings

Ranked by user impact (comfort and accessibility first; none of the three is
a speed or SEO issue). Edit the build sources, then regenerate; do not patch
`assets/page.js` or the HTML by hand.

### 1. Keep the theme toggle, but let it follow the system again

- **Impact:** accessibility and mobile comfort. A visitor whose phone switches
  scheme at night can currently stay pinned to the opposite theme after a
  single tap.
- **Scanner:** `dark-mode-toggle`, `assets/page.js:17`. Verified keep: the
  script stores an override in `localStorage` and sets `data-theme` without
  ever updating `<meta name="color-scheme">`.
- **Already in place.** Every category page already ships
  `<meta name="color-scheme" content="light dark">`. An inline script, run
  before paint, restores a stored `data-theme` so the first frame is right.
  `build/page.css` already sets `color-scheme: light` or `dark` to match, and
  the button's two labels live in the markup so the first frame is labelled
  correctly too. The `theme toggle` check and ADR 8 finding 16 hold the
  visible control and the dimmed photo tiles. Do not remove the header
  button; that would be a product change, not a modernization.
- **The gap.** The click handler always writes `"light"` or `"dark"` to
  `localStorage`. It never clears the entry, so once someone has toggled they
  no longer follow the operating system. The `<meta>` stays `light dark`
  even when the page is pinned, so browser chrome (scrollbars, form
  controls) can disagree with the page. The guide's two-state rule is: store
  the override only when it differs from the current system preference, and
  remove it when the user toggles back to what the system is showing now, so
  a later OS change is followed again. On each change, set the meta content
  to `light`, `dark`, or `light dark`, and keep CSS `color-scheme` in sync.
  The base rule should be `color-scheme: light dark`, with the pinned values
  applied when the meta (or the existing `data-theme` attribute) says so, so
  a browser with no script still follows the system.
- **Browser support.** `color-scheme` is Baseline widely available (Chrome 98,
  Firefox 96, Safari 13). `light-dark()` is Baseline newly available since
  13 May 2024 (Chrome 123, Firefox 120, Safari 17.5). `:has()` is Baseline
  2023. Switching the custom properties over to `light-dark()` is optional
  and can wait; if it is done, keep the current `prefers-color-scheme`
  blocks or wrap the new function in `@supports (color: light-dark(white,
  black))`, which is the fallback the `dark-mode` guide requires. Do not use
  `light-dark()` for images: image values for that function only became
  Baseline in September 2026 (Chrome 150, Firefox 150, Safari 27) and are
  too new for a public page without a fallback.

### 2. Light-dismiss the source card with `closedby="any"`, and keep a Safari fallback

- **Impact:** accessibility. Light-dismiss already works; the gain is a
  correct outside click (the current `event.target === card` test misses
  clicks on the dialog's own padding) and less custom close logic to keep
  true. Small for most readers.
- **Scanner:** `dialog`, `assets/page.js:764`. Verified keep: a click
  listener on the source-card `<dialog>` closes it when `event.target` is
  the dialog itself, which is the pattern the guide wants replaced.
- **What to do.** Add `closedby="any"` on the source-card dialog in the HTML
  emitter. Keep the existing close button, Escape behaviour and the `close`
  listener that returns focus. Behind `if (!('closedBy' in
  HTMLDialogElement.prototype))`, ship the guide's pointer-position fallback
  (press and release outside the dialog's box, so a text-selection drag that
  ends on the backdrop does not dismiss). That fallback is mandatory:
  `closedby` is in Chrome 134, Edge 134 and Firefox 141 (July 2025), and is
  **not in Safari**. Without it this change would drop light-dismiss for
  every Safari reader.
- **Leave alone.** ADR 24 declined the Popover API for this card; do not
  reopen that. The custom focus return on `close` must also stay. The dialog
  guide says the browser will return focus to the invoker, but this page
  already handles the case where the invoking figure has been filtered out
  of the table (design critique, and the comment above the `close` listener
  in `build/page.js`). Removing that code would regress an accessibility
  fix the audits already paid for.

### 3. Add the same `closedby` hint to the photo lightbox, but keep its click handler

- **Impact:** accessibility, lower than item 2, because most of the lightbox
  close behaviour has to remain custom either way.
- **Scanner:** `dialog`, `assets/page.js:680`. Partial keep. The listener
  does close on a backdrop click, which `closedby="any"` can own, but it
  also closes on a tap in the space around the photo and leaves the name bar
  alone. That is ADR 8 finding 17, held by the `photo lightbox` check: a
  close button, a tap anywhere off the photo, and Escape.
- **What to do.** Add `closedby="any"` on the lightbox dialog, with the same
  Safari feature-detect fallback as item 2. Do not delete the click
  listener, or a tap on the padding around the photo will stop closing it
  and the check will fail. A later change can teach the fallback and the
  remaining listener to share one "outside the photo, not on the bar" test,
  but that is a behaviour-preserving tidy, not a requirement of this scan.

## Suggested order

If this list is implemented later: item 1 first (it is the only one a reader
can feel without opening a dialog), then 2, then 3. Pair each change with
an assertion in the check family that already owns it (`theme toggle`,
`source card`, `photo lightbox`), as `AGENTS.md` requires. Leave this
document uncommitted until the owner asks otherwise.
