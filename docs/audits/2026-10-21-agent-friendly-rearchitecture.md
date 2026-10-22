# Agent-friendly re-architecture, 2026-10-21

Repo `subfree-uk` at local `main`, 27 commits ahead of `origin/main`. Read-only pass on 21 October 2026. The repo is owned by the Side Hustle CEO agent, so each task below is a recommendation for that owner. No code changed; this file is the only write.

## Status

The page is correct and fast, and the 2026-10-20 audit closed into ADR-0007 with a check or a recorded decision for each of its twenty findings. The full check passes: 64 named checks in 93 s, measured today. ADR-0007 says about a minute.

The remaining agent costs are structural:

- **Import side effects.** Loading the data rewrites committed files. `build/check.py` loads `build/build.py` with `exec_module` (line 2081). `build.py` writes `data/doorbells.csv` and `data/doorbells.md` at module level (lines 369 and 399), outside its `__main__` guard.
- **Mixed files.** The data and the page template share one 673-line file, and every check shares one 2,991-line file. They changed in 29 and 27 of the repo's 67 commits.
- **Unchecked commits.** The commit rule is checked only on pull requests, and all 67 commits went straight to `main`. 10 of them fail the repo's own `build/check_commits.py`.

There are four tasks: two architecture and two static checks. Nothing here needs a skill yet.

## Evidence

- **Freebuff.** The `subfree-uk` store has 1 thread on this repo path, with 20 user messages. 12 contain "until consensus" and 6 ask for completed items to be pruned. The one data correction, #25, asked for unverified facts to be sourced. ADR-0007 now enforces that: an open fact must name its blocker.
- **Git.** 67 commits and no merges. `build/check_commits.py` over the full range exits 1 for 10 commits, for example `7b9cb4d` "Review pass: tighten two assertions, and keep the docs' numbers true". `commits.yml` runs on `pull_request` only.
- **Measured.** `build/check.py` takes 93 s for the full run and 4.5 s for `--only "dataset,derived figures,data freshness"`. The desktop was shared with other agents.

## Tasks

1. **Make the data importable without building the page.**
   - **Tier.** 1, architecture.
   - **Problem.** `ROWS`, the required keys and the derivations live in `build/build.py` beside the HTML template and the file writers. The CSV and markdown writers run at import time, so any tool that reads `ROWS` rewrites two committed files. A date check can also raise `SystemExit` during import, which `load_build()` has to catch. An agent changing one price has to read the template, and an agent changing the template is one line away from the data.
   - **Change.** Move `ROWS`, `REQUIRED_ROW_KEYS`, `CHECKED_ISO` and the derivation functions into `build/rows.py`, with no writes and no exits. Type a row as a `TypedDict` or frozen dataclass so an unknown key fails at construction. Move the CSV and markdown writers into `write()`. `check.py` then imports `rows`, not `build`.
   - **Benefit.** A data edit touches one small file, reading the data has no side effects, and the key check moves from a runtime assertion into the type.

2. **Split `check.py` by check family behind one registry.**
   - **Tier.** 1, architecture.
   - **Problem.** All 64 checks are in one 2,991-line file, changed in 27 of 67 commits. `AGENTS.md` says a page change needs a matching assertion, so most changes edit this file. The nearest example an agent copies may be 2,000 lines away from the family it belongs to.
   - **Change.** One module per family (data, structure, accessibility, performance, browsers) under `build/checks/`, each registering its checks by name. `check.py` keeps the runner, `--only` and `--list`. Make `--only` with the family's names the documented edit loop, and keep the full run for CI and before push.
   - **Benefit.** Adding a check means reading one family module, not the whole file. The edit loop drops from 93 s to a few seconds.

3. **Check commit messages where commits actually land.**
   - **Tier.** 2, static analysis.
   - **Problem.** `.github/workflows/commits.yml` runs on `pull_request` only. Every commit has gone to `main` directly, so the check has never seen one, and 10 of 67 fail it, 8 of those on 20 October. There are no git hooks. Music and TrainBudgetExplorer also refuse a Codebuff credit at commit time. No commit here carries one yet, and nothing would stop one.
   - **Change.** Add `push: branches: [main]` to `commits.yml`, checking the pushed range. Add a `.githooks/commit-msg` that runs `build/check_commits.py` on the message, plus the credit refusal ported from TrainBudgetExplorer's `tools/check_commit_message.py`.
   - **Benefit.** A bad subject fails while it is still one edit away, and the documented rule matches the practice.

4. **Delete one of the two screenshot scripts.**
   - **Tier.** 2, static analysis (deletion).
   - **Problem.** `build/shots.py` (1,941 bytes) and `build/shots2.py` (2,176 bytes) were both added in `c04bc3a` and differ by 33 lines. An agent looking for how screenshots are taken finds two answers.
   - **Change.** Keep the one the owner uses and delete the other, or fold the difference in as a flag.
   - **Benefit.** One nearest example.

## Previous audit status

The 2026-10-20 full audit was deleted when it closed. Its twenty findings are recorded in `docs/decisions/0007-the-audits-twenty-findings.md`. I spot-checked these against the code:

| 10-20 item | Status now | Evidence |
|---|---|---|
| 1.1 Figures recomputed | Fixed | The `derived figures` check passes |
| 1.2 Date is data | Fixed | The `data freshness` check passes |
| 5.1 CI runs the audit | Fixed | `audit.yml` runs on pull request and on push to `main` |
| 5.2 Named, timed checks | Fixed | `--list` prints 64 names and `--only` works (4.5 s for three) |
| 6.1 CSS and JavaScript as files | Fixed | `build/page.css` and `build/page.js` |
| 6.2 Rows checked before read | Fixed, could be stronger | A runtime assertion. Task 1 moves it into the type |
| The others | Recorded in ADR-0007 | Not re-verified one by one |

## Open questions for Lyden

1. This repo belongs to the Side Hustle CEO agent. Should these tasks go to that agent, or wait for you?
2. 27 commits are unpushed. Is that intended?
