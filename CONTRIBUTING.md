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

## Generated files

`index.html`, `doorbells.html`, `data/doorbells.csv` and `data/doorbells.md`
come from `build/build.py`. Run the build and commit the regenerated files in
the same commit as the source change, so every commit can be deployed as it
stands.

## Before committing

- Run `python build/check.py`. It rebuilds the site, fails if a generated file
  is stale, then runs the accessibility, anchor, image, target-size and
  overflow audit. Fix anything it reports.
- Check the page at desktop and phone widths.
- Review the diff and fix what that review finds before committing.
- Keep commits small and logical, one concern each.

## Pull requests

CI runs `build/check_commits.py` over every commit in a pull request. To run it
locally:

```bash
python build/check_commits.py origin/main..HEAD
```
