#!/usr/bin/env python3
"""Run the full local price refresh and stop before anything unsafe ships.

The hosted runner cannot read several UK shops. This script is the local
counterpart: it runs the browser probe with its Firefox fallback, applies only
confirmed readings to the ledger, rebuilds the generated site, and runs the
full audit. A dirty tree, a failed probe, a failed build or a failed audit
stops the run before a commit exists.

    python build/price_refresh.py
    python build/price_refresh.py --no-push
    python build/price_refresh.py --allow-dirty

The scheduled task calls this with no arguments. It pulls with `--ff-only`
first, commits only when the tree changed, and pushes the commit on success.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)


def say(message: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    say("$ " + " ".join(command))
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def checked(command: list[str]) -> bool:
    result = run(command, check=False)
    if result.returncode:
        say(result.stdout.strip())
        say(result.stderr.strip())
        return False
    if result.stdout.strip():
        say(result.stdout.strip())
    return True


def git_output(*args: str) -> str:
    result = run(["git", *args])
    return result.stdout.strip()


def park_changes(started_clean: bool) -> None:
    """Keep a failed run out of the next one without throwing it away."""
    if not started_clean or not git_output("status", "--porcelain"):
        return
    message = f"price refresh failed {datetime.now():%Y-%m-%d %H:%M}"
    result = run(
        ["git", "stash", "push", "--include-untracked", "-m", message],
        check=False,
    )
    if result.returncode:
        say("Could not park the failed changes; the tree needs attention.")
        say(result.stderr.strip())
    else:
        say(f"Parked the failed changes in a stash: {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="commit locally but leave the commit unpushed",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="continue even if the working tree already has changes",
    )
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args(argv)

    dirty = git_output("status", "--porcelain")
    started_clean = not dirty
    if dirty and not args.allow_dirty:
        say("The working tree is not clean; refusing to mix a price run with it.")
        say(dirty)
        return 2

    if not checked(["git", "pull", "--ff-only"]):
        park_changes(started_clean)
        return 3

    if not checked(
        [
            str(PYTHON),
            "build/price_watch.py",
            "--apply",
            "--concurrency",
            str(max(1, min(args.concurrency, 6))),
        ]
    ):
        park_changes(started_clean)
        return 4

    if not checked([str(PYTHON), "build/build.py"]):
        park_changes(started_clean)
        return 5

    if not checked([str(PYTHON), "build/check.py"]):
        park_changes(started_clean)
        return 6

    changed = git_output("status", "--porcelain")
    if not changed:
        say("No price or generated file changed; nothing to commit.")
        ahead = git_output("rev-list", "--count", "@{u}..HEAD")
        if not args.no_push and ahead != "0":
            if not checked(["git", "push"]):
                say("A local commit is waiting; the push failed and needs attention.")
                return 9
            say(f"Pushed {ahead} pending commit(s).")
        return 0

    say("Changed files:")
    say(changed)
    if not checked(["git", "add", "-A"]):
        park_changes(started_clean)
        return 7

    message = f"chore(prices): refresh the price ledger for {datetime.now():%d %B %Y}"
    if not checked(["git", "commit", "-m", message]):
        park_changes(started_clean)
        return 8

    if args.no_push:
        say("Committed locally; --no-push left it unpushed.")
        return 0

    if not checked(["git", "push"]):
        say("The commit is local; the push failed and needs attention.")
        return 9
    say("Price refresh committed and pushed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
