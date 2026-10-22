# 12. The agent-facing structure lands

- Status: Accepted
- Date: 22 October 2026
- Source: the agent-friendly re-architecture audit of 21 October 2026, its
  four tasks, now closed.

## Context

The 21 October audit found the page correct and fast but expensive to change:
loading the data rewrote two committed files, the data and the page template
shared one file, every check shared one 2,991-line file, the commit rule ran
only on pull requests while every commit went to `main`, and two screenshot
scripts differed by 33 lines.

## Decision

- `build/rows.py` holds `ROWS`, `S`, `CHECKED_ISO` and every derived figure,
  with no writes and no exits. `build/build.py` imports it and writes the
  files; `build/check.py` imports it and recomputes them.
- The audit is one module per family under `build/checks/` (`data`,
  `structure`, `behaviour`, `compare`, `accessibility`, `performance`,
  `browsers`). Each registers named checks with a phase and an order, and
  `registry()` refuses a duplicate name or order. `build/check.py` keeps the
  runner, `--only` and `--list`.
- `.github/workflows/commits.yml` checks the range a push to `main` brings as
  well as a pull request, with a floor at the commit that last touched the
  workflow, so history the rule never saw is not re-litigated.
  `.githooks/commit-msg` runs the same rules on one message, and
  `build/check_commits.py` refuses a co-author trailer, a generated-with line
  or a bot line.
- `build/shots2.py` is the only screenshot script.

The audit also suggested typing a row as a `TypedDict` or frozen dataclass so
an unknown key fails at construction. That was declined: Python does not check
a `TypedDict` at runtime, the repo runs no type checker, and `row_problems()`
still fails an unknown key by name in the build and in the audit. A type hint
would add a second, unenforced description of the row.

## Consequences

- A data edit touches one small file, and reading the data has no side
  effects.
- Adding a check means reading one family module. `--only` with the family's
  names is the edit loop; the full run stays for CI and before a push.
- AGENTS.md now names `build/checks/` as the place a CSS or JavaScript change
  needs its assertion, because the runner is no longer where they live.
- The audit document is deleted with this record. Its evidence was a snapshot
  of 67 commits and a 93-second run; the structure it asked for is now the
  repository, and the numbers it measured are in `docs/performance-budget.md`
  and the check names themselves.
