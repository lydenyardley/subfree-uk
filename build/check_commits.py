#!/usr/bin/env python3
"""Check commit messages against the rules in CONTRIBUTING.md.

    python build/check_commits.py <base>..<head>
    python build/check_commits.py HEAD~3..HEAD

Merge commits are skipped; every other commit in the range must have a
`type(scope): summary` subject of 72 characters or fewer, a lowercase summary
without a trailing period, and body lines wrapped at 72 characters.

Exit status is 1 when any commit breaks the format. The pull request workflow
in .github/workflows/commits.yml runs the same command.
"""
import re
import subprocess
import sys

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore"
SUBJECT = re.compile(rf"^({TYPES})(\([a-z0-9][a-z0-9 ./-]*\))?: ([a-z0-9].*)$")
MAX_LINE = 72


def git(*args):
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def problems_in(message):
    lines = message.rstrip("\n").split("\n")
    subject = lines[0].strip()
    problems = []

    if len(subject) > MAX_LINE:
        problems.append(f"subject is {len(subject)} characters, limit {MAX_LINE}")
    match = SUBJECT.match(subject)
    if not match:
        problems.append(
            "subject must be 'type(scope): summary' with a lowercase summary "
            f"and one of the types {TYPES.replace('|', ', ')}"
        )
    elif match.group(3).endswith("."):
        problems.append("subject ends with a period")

    for number, line in enumerate(lines[1:], start=2):
        if len(line) > MAX_LINE:
            problems.append(f"line {number} is {len(line)} characters, limit {MAX_LINE}")

    return problems


def main():
    if len(sys.argv) != 2 or ".." not in sys.argv[1]:
        print("usage: check_commits.py <base>..<head>", file=sys.stderr)
        return 2

    revision_range = sys.argv[1]
    commits = [line for line in git("rev-list", "--no-merges", revision_range).split("\n") if line]
    if not commits:
        print(f"No commits to check in {revision_range}.")
        return 0

    failures = 0
    for commit in commits:
        message = git("log", "-1", "--format=%B", commit)
        problems = problems_in(message)
        if not problems:
            continue
        failures += 1
        subject = message.split("\n", 1)[0]
        print(f"{commit[:7]}  {subject}")
        for problem in problems:
            print(f"        {problem}")

    if failures:
        print(f"\n{failures} of {len(commits)} commit(s) do not follow CONTRIBUTING.md.")
        return 1
    print(f"All {len(commits)} commit(s) follow CONTRIBUTING.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
