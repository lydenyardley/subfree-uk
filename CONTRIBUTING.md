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

## Data

`ROWS` in `build/build.py` is the dataset. The sourcing rules, including how
to close a "Not yet verified" note, are in [AGENTS.md](AGENTS.md).

## Generated files

`index.html`, the `doorbells.html` redirect, `assets/page.css`,
`assets/page.js`, `data/doorbells.csv` and `data/doorbells.md` come from
`build/build.py`. Run the build and commit the regenerated files in the same
commit as the source change, so every commit can be deployed as it stands.
The asset URLs carry a content version; the files themselves keep their names,
so an old cached page can still load them.

## Before committing

- Run `python build/check.py`. It rebuilds the site, fails if a generated file
  is stale, recomputes every figure in the CSV from `ROWS`, and then runs the
  accessibility, anchor, image, target-size, type-floor, phone-layout, compare
  and differences-only, shareable-shortlist, jump-announcement, the
  tray-to-comparison transition, the table's scroll rule, motion, score-bar,
  label, source-list, closing-line, performance-budget, no-JavaScript and
  overflow audit at every breakpoint, plus the structural half in Firefox.
  Fix anything it reports. `--only "<name>"` runs one named check and `--list`
  prints their names.
- Check the page at desktop and phone widths, and keep the numbers in
  [docs/performance-budget.md](docs/performance-budget.md) honest if you touch
  sorting, filtering or the compare table.
- Review the diff and fix what that review finds before committing.
- Keep commits small and logical, one concern each.

## Pull requests

CI runs `build/check_commits.py` over every commit in a pull request, and
`build/check.py` on every pull request and every push to `main`. To run them
locally:

```bash
python build/check_commits.py origin/main..HEAD
```
