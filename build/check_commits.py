#!/usr/bin/env python3
"""Check commit messages against the rules in CONTRIBUTING.md.

    python build/check_commits.py <base>..<head>
    python build/check_commits.py HEAD~3..HEAD
    python build/check_commits.py --message-file .git/COMMIT_EDITMSG

Merge commits are skipped; every other commit in the range must have a
`type(scope): summary` subject of 72 characters or fewer, a lowercase summary
without a trailing period, and body lines wrapped at 72 characters.
CONTRIBUTING.md asks for one author and no tool credit, so a co-author trailer,
a generated-with line or a bot line is refused rather than merely noticed.

Exit status is 1 when any message breaks the rules. The pull request and push
workflows in .github/workflows/commits.yml run the range form, and
.githooks/commit-msg runs --message-file, so a bad message fails while it is
still one edit away.
"""
import argparse
import re
import subprocess
import sys

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore"
SUBJECT = re.compile(rf"^({TYPES})(\([a-z0-9][a-z0-9 ./-]*\))?: ([a-z0-9].*)$")
MAX_LINE = 72
ATTRIBUTION = (
    (re.compile(r"^co-authored-by:", re.IGNORECASE), "a co-author trailer"),
    (re.compile(r"\bgenerated with\b", re.IGNORECASE), "a generated-with line"),
    (re.compile("\N{ROBOT FACE}"), "a bot line"),
)


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

    for number, line in enumerate(lines, start=1):
        if len(line) > MAX_LINE:
            problems.append(f"line {number} is {len(line)} characters, limit {MAX_LINE}")
        for pattern, what in ATTRIBUTION:
            if pattern.search(line):
                problems.append(f"line {number} adds {what}")
                break

    return problems


def message_from_file(path):
    """The message a commit would get: git strips comment lines after the hook."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    kept = [line for line in text.split("\n") if not line.startswith("#")]
    return "\n".join(kept).strip()


def report(subject, problems):
    print(subject)
    for problem in problems:
        print(f"        {problem}")


def main():
    # A message can hold any character; the console can hold fewer than that,
    # and a hook that crashes on its own report is worse than the report.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Check commit messages against CONTRIBUTING.md.")
    parser.add_argument("range", nargs="?", metavar="BASE..HEAD", help="the commits to check")
    parser.add_argument(
        "--message-file",
        metavar="PATH",
        help="check one message file instead, as .githooks/commit-msg does",
    )
    args = parser.parse_args()

    if args.message_file:
        message = message_from_file(args.message_file)
        problems = problems_in(message)
        if problems:
            print(f"{args.message_file} does not follow CONTRIBUTING.md:")
            report(message.split("\n", 1)[0], problems)
            return 1
        return 0

    if not args.range or ".." not in args.range:
        parser.error("give a BASE..HEAD range, or --message-file PATH")

    commits = [line for line in git("rev-list", "--no-merges", args.range).split("\n") if line]
    if not commits:
        print(f"No commits to check in {args.range}.")
        return 0

    failures = 0
    for commit in commits:
        message = git("log", "-1", "--format=%B", commit)
        problems = problems_in(message)
        if not problems:
            continue
        failures += 1
        subject = message.split("\n", 1)[0]
        report(f"{commit[:7]}  {subject}", problems)

    if failures:
        print(f"\n{failures} of {len(commits)} commit(s) do not follow CONTRIBUTING.md.")
        return 1
    print(f"All {len(commits)} commit(s) follow CONTRIBUTING.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
