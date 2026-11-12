# Contributing

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/).

```
<type>(<scope>): <summary>
```

- `type` is one of `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
  `build`, `ci` or `chore`.
- `scope` is optional and names the area, for example `table`, `build` or
  `docs`.
- `summary` is imperative, lowercase, has no trailing period, and stays within
  72 characters.
- Leave one blank line, then write a body wrapped at 72 characters explaining
  why the change is needed. What changed is already in the diff.
- Add a `BREAKING CHANGE:` footer only when something outside the repo stops
  working. There is no published API here, so that is rare.

Example:

```
fix(table): keep prices aligned when a footnote widens

A two-digit source number pushed the figure left of the column edge.
The price cell now reserves a fixed slot for the footnote, so every
price ends on the same pixel.
```

## Author and attribution

Every commit is authored by Lyden Yardley
<lydenyardley@users.noreply.github.com>. Do not add co-author trailers,
generated-with lines, or tool attribution to commit messages.
`build/check_commits.py` refuses all three, so a message with one fails in the
hook below and again on the push.

## Data

`RAW_ROWS` in `build/rows.py` is the authored dataset, beside its sources and
the figures derived from them. `build/model.py` parses it once into the frozen
records the page and checks read; author in `RAW_ROWS`, not in the parsed
`ROWS`. The sourcing rules, including how to close a "Not yet
verified" note, are in [AGENTS.md](AGENTS.md).

## Generated files

`index.html`, `cameras/index.html`, `rings/index.html`, `printers/index.html`,
`pet-trackers/index.html`, `baby-monitors/index.html`, the `doorbells.html`
redirect, `assets/page.css`, `assets/page.js`, the CSVs and Markdown in `data/`
and `404.html` come from `build/build.py`. Run the build and commit the
generated files in the same commit as the source change, so every commit can
be deployed as it stands.
The asset URLs carry a content version; the files themselves keep their names,
so an old cached page can still load them.

## Before committing

- The pre-commit hook runs `python build/check.py --fast`, the 22 browser-free
  checks, and refuses a commit when the generator has changed a committed file.
  Enable it once per clone with the hook command below. Run the full
  `python build/check.py` before pushing. It recomputes every figure in the CSV
  from `ROWS`, type-checks `build/` with mypy, and then runs the accessibility,
  anchor, image, target-size, type-floor, phone-layout, compare and
  differences-only, shareable-shortlist, jump-announcement, the
  tray-to-comparison transition, the table's scroll rule, motion, score-bar,
  label, source-card, source-list, closing-line, performance-budget,
  no-JavaScript and overflow audit at every breakpoint, plus the structural
  half in Firefox. Fix anything it reports. `--only "<name>"` runs one named
  check and `--list` prints their names.
- Check the page at desktop and phone widths, and keep the numbers in
  [docs/performance-budget.md](docs/performance-budget.md) honest if you touch
  sorting, filtering or the compare table.
- Review the diff and fix what that review finds before committing.
- Keep commits small and logical, one concern each.
- Enable the hooks once per clone. The message hook runs the same rules as the
  push, so a bad subject fails while it is still one edit away; the pre-commit
  hook runs the fast gate:

  ```bash
  git config core.hooksPath .githooks
  ```

## Pull requests

CI runs `build/check_commits.py` over every commit in a pull request and over
every commit a push to `main` brings, and `build/check.py` on every pull request
and every push to `main`. To run them locally:

```bash
python build/check_commits.py origin/main..HEAD
```
