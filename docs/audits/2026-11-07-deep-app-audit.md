# Deep app audit, 7 November 2026

This is a read-only review of the four published comparison routes, the generated HTML and data, the shared renderer and script, the verification suite, and the delivery and documentation surface. It records defects and improvement opportunities. It does not implement them.

## Scope and method

- Read `README.md`, `AGENTS.md`, `build/catalog.py`, `build/build.py`, `build/rows.py`, the shared page sources and audit families, the generated routes, and the existing architecture decisions and October audits.
- Ran `python build/check.py`. It passed all 97 checks, including `category page behaviour`, which opens each non-root category, sorts, compares, opens a source card and checks its assets and console.
- Inspected `/`, `/cameras/`, `/rings/`, `/printers/`, `/404.html`, and the legacy `doorbells.html` route in Chromium. Measured shared mobile layout at 390×844 and desktop layout at 1440×1000. Opened a three-model comparison and scrolled the full document to verify the desktop comparison-header behavior.
- Did not run `python build/check.py --external`; source links therefore have not had a live HTTP status sweep in this review.
- `/impeccable critique` could not be run. The skill loader does not expose an `impeccable-critique` skill, and `impeccable` is not installed on PATH. No detector results are claimed.
- Finding order reflects user impact and confidence. P1 is a user-facing trust/access issue; P2 is a material usability or maintenance risk; P3 is an improvement opportunity. Measurements and direct observations are labelled as such.

## Findings

### 1. [P1, confirmed] The privacy claim conflicts with the actual analytics request

`README.md:7` says "No tracking, cookies ... or third-party scripts." The generated category pages load `https://gc.zgo.at/count.js` (`build/build.py:720`), and their metadata says visits are counted by GoatCounter (`build/build.py:631`). `build/build.py:255-257` permits that external script, image host and connect host in the CSP. Chromium on the local preview emitted `ERR_NAME_NOT_RESOLVED` for the GoatCounter script, which confirms the requested external dependency but not how the hosted service processes visits.

**Impact.** A reader relying on the README's privacy promise is not told that page visits are counted by an external service until they read the page metadata. The repo's own policy comment still calls "No third-party code" the promise, while its CSP explicitly allows GoatCounter.

**Opportunity.** Decide and document the precise promise. Either describe privacy-preserving, cookie-free analytics as third-party measurement, or remove the analytics and its CSP allowances. If retaining it, make the repository statement consistent with the user-facing disclosure and vendor policy.

### 2. [P1, confirmed] The desktop comparison loses model identity while the reader scans its long spec table

`build/page.css:335,345` styles `.cmp-t thead th` with `position:relative`; only the first pinned spec header is sticky at phone width (`:585-586`). At 1440px, the opened comparison was about 961px tall for the tested three doorbells. After scrolling the document to 2,200px, the model header's top was −1,567px, so all three names were above the viewport while the user was among the comparison rows.

**Impact.** Once the header leaves view, a reader comparing several similar models must remember which column belongs to which model. The problem is larger when columns have been rearranged, one of the comparison's main interactions.

**Opportunity.** Keep the model-name portion of each comparison column visible while scrolling the comparison, or provide another persistent column identity that does not obscure its rows. Preserve the horizontally scrollable table and its column handles.

### 3. [P3, verification gap] The phone first-paint check accepts a barely visible first row

`build/checks/structure.py:79-100` passes when the first row's top is less than or equal to the viewport height. This allows a row beginning at y=843 in an 844px viewport to pass, even though almost none of the product card is visible. A fresh mobile-width load of the root route in this review put the first row at y=615px, so this is a weakness in the acceptance predicate, not a current root-page failure.

**Impact.** A later content or copy change could push almost the entire first card below the fold while the `phone first paint` check remains green.

**Opportunity.** Set a contentful first-screen target that accounts for a useful part of the row, not just its top coordinate. Check fresh mobile-width loads so responsive setup runs before measurement.

### 4. [P3, confirmed] The main audit skips external links, and its optional pass does not fail on inconclusive results

`build/checks/browsers.py:168-183` skips the external-link check unless `--external` is passed. In that optional pass, HTTP 404 and 410 fail, while other 400+ statuses and all request exceptions become notes and the run continues. The project does have a separate weekly check: `.github/workflows/refresh.yml` runs `build/links.py`, which labels dead, blocked, server, unreachable and other outcomes and fails on dead pages or server errors.

**Impact.** A green local `python build/check.py` says nothing about external source availability, while a scheduled sweep can report blocked or unreachable sources without failing the job. That behavior is deliberate for vendor bot walls, but means an inconclusive destination can remain open until a person reads the report.

**Opportunity.** Keep the distinction between dead and blocked links, but make the local check's skipped status prominent and make sure the scheduled summary's blocked and unreachable items are reviewed. No evidence here shows the weekly sweep is absent; this is a workflow visibility and interpretation risk, not a missing checker.

### 5. [P2, confirmed] The cold-load performance measurement is not a regression gate

`docs/performance-budget.md:128-133` describes one cold-load sample from 23 October 2026, including FCP, LCP, CLS and bytes over the wire, and explicitly says no check holds first paint. The automated performance check (`build/checks/performance.py`) gates sort and comparison interactions, while the transfer check gates only gzipped HTML, CSS and JavaScript. It does not gate image weight, image request count, first paint, or CLS.

**Impact.** The site can meet every recorded performance gate while a later image or rendering change materially worsens what a new visitor sees first. Product images dominate bytes beyond the three-file transfer budget.

**Opportunity.** Decide whether cold-load behavior is a product requirement. If so, add a repeatable, noise-tolerant check for a narrowly chosen metric and representative image loading. If not, label the old sample historical and avoid presenting it as current performance evidence.

### 6. [P2, confirmed] Shared browser regression checks mostly exercise the root category

`build/checks/context.py` intentionally builds the common fixtures from `CATEGORIES[0]`. Most interaction and accessibility checks run against that root page. `category.py:page_behaviour()` verifies each non-root route's row count, one price sort, compare open, source card, assets, and console, but it does not run the full phone, axe, keyboard, details, share/restore, or print suite on cameras, rings, and printers. The existing decision records describe the checks as general even where their fixture is doorbell-specific.

**Impact.** A category override or content shape can regress in an interaction state that is only exercised on the doorbell route, while the full suite stays green. This is a risk, not an observed route failure; the current static and category checks all passed.

**Opportunity.** Keep the costly shared browser suite parameterized over representative category traits, or add small targeted route fixtures for category-specific behavior. Use the existing property-selected fixture approach so new product ids do not become brittle expected values.

### 7. [P2, confirmed] The 404 experience is outside the shared site shell

The generated `404.html` has a stylesheet and links to each route, but it omits the category menu, theme control, canonical/social metadata and the page's established issue/contact routes. At 390px, the browser rendered it in the browser-default Times New Roman rather than the site's serif/sans hierarchy because the stylesheet does not apply the site's body font stack to this page shape. `build/checks/structure.py:notfound_check()` only verifies the heading, root link, `noindex`, stylesheet presence and absence of a GitHub destination. The full suite passes.

**Impact.** A mistaken or stale link leads to a visually and functionally different page, with no dark-mode control and no direct route back to the repo's issue/contact mechanism. It is a fallback, so this has lower frequency than the main routes.

**Opportunity.** Treat the 404 as another route in visual and accessibility review. Share the site shell where it improves wayfinding, and assert that its typography and navigation remain intentional rather than merely checking that a stylesheet link exists.

### 8. [P3, improvement opportunity] The generated files and asset hashes form a large, broad rebuild surface

`build/build.py:373-385` serializes every category's product data into one shared JavaScript asset. Any content change in any category rebuilds that common script and changes its version on every route. `build/build.py:837-872` writes pages and data outputs and removes old `page-*.css` and `page-*.js` assets from the assets directory. The current generated files are approximately 205KB, 159KB, 90KB and 77KB raw HTML for root, cameras, rings and printers; the single JS file is approximately 128KB raw. The transfer budget records 70,443 gzipped bytes across root HTML, CSS and the combined script.

**Impact.** An unrelated category's data invalidates the same JS resource for every visitor, and the shared script must embed all categories. The build also owns cleanup behavior in a directory that may hold unrelated user assets matching the legacy naming pattern.

**Opportunity.** Reassess asset ownership and category data delivery when further categories or row growth make the current cache invalidation costly. Keep cleanup scoped to files the build demonstrably owns. This is a future scale concern; current resource budgets pass and there is no measured user-facing regression in this review.

### 9. [P3, improvement opportunity] The shared renderer has many category-specific branches in one large catalog and build path

`build/catalog.py` is 1,311 lines and contains four large category records alongside shared wording and render configuration. `build/build.py` is an 877-line renderer. This is an intentional, documented single-build architecture, not a defect by itself. The area to watch is that differences such as score vocabulary, short answer, method copy, sort names, CSV schema and printer/ring labels are represented through optional record keys and conditional rendering.

**Impact.** A new category can be data-only when it matches the existing shape, but a genuinely different data domain requires more optional branches and implicit conventions. A maintainer must understand both generic field meaning and category overrides before changing shared output.

**Opportunity.** Continue the catalog-driven approach while measuring where new category-specific conditionals actually recur. Only deepen the category interface when at least two consumers need a stable seam; splitting files for size alone would add navigation without proving a better model.

## Positive evidence

- The four category records and all brand current/previous maps are checked. The 7 November run reports expected unresolved lineup notes for brands with no predecessor row.
- Data-derived totals, source keys, affiliate annotations, content policy, generated file freshness, route asset paths, photo existence, accessible names, no-JavaScript rendering, the 320px overflow threshold, print alignment, and the shared category flows are covered by named checks.
- `python build/check.py` passed all 97 checks. Its optional external URL sweep was not run.
- No code changes were made during this audit.
