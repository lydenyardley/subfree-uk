#!/usr/bin/env python3
"""Verification for the site: rebuild, recompute, then audit structure and behaviour.

The checks live in `build/checks/`, one module per family, and each one names
the page state it needs. This file is the runner: it rebuilds the site, imports
the data, serves the repo root on a loopback port, prepares each phase and
prints one named, timed result per check.

Runs build/build.py first and reports any generated file it changed, so a stale
page fails here instead of shipping. Recomputes every derived figure from ROWS
and compares it with the CSV, and refuses an open fact that does not name its
blocker. Drives the page with Chromium and Firefox: axe-core in both themes at
1280px, 820px and 390px, internal anchors, image files, duplicate ids, headings,
labels, target sizes, the type floor, the phone layout, the price range slider,
the filter panel, the live announcements, the three-row compare cap, the
empty-state recovery, the compare cost row, the shortlist copy, the
differences-only view, the focusable comparison scroller, the jump announcement,
the tray-to-comparison transition, the source card on every figure, the theme
motion, the static score bars, the
contained phone cards and desktop rows with their column alignment and the
catch's own row below 901px, the sticky
table header, the muted-text contrast, the record and plan labels, the phone
label column, the plan region marker, the host-grouped source list, the closing
line, the performance budget, the no-JavaScript fallback, the skip link, the
photo lightbox and horizontal overflow at the breakpoints the stylesheet
defines.

Each result is named and timed; --list prints the names and --only runs a
matching subset. A full run also starts Firefox and repeats the structural,
layout and axe pass there, because Chromium alone cannot prove a fallback.

    python build/check.py
    python build/check.py --only "derived figures,labels"
    python build/check.py --list
    python build/check.py --external   # also request every outbound URL
    python build/check.py --headed

Needs the venv from README.md. Exit status is 1 when an issue is found.
"""
import argparse
import importlib.util
import sys
import time

from checks.context import Context
from checks.data import load_rows, note_pending
from checks.registry import Skip, registry
from checks.runner import Audit, load_pages, rebuild, serve


def run_phase(checks, phase, ctx, audit):
    """Every wanted check in one phase, in order, each reported by name."""
    for check in checks:
        if check.phase != phase:
            continue
        if not audit.wants(check.name):
            audit.skip(check.name)
            continue
        start = time.perf_counter()
        try:
            problems = check.run(ctx)
        except Skip as reason:
            audit.skip(check.name, str(reason))
            continue
        except Exception as error:  # a check that crashes still names itself
            problems = [f"{check.name} raised {type(error).__name__}: {error}"]
        audit.add(check.name, problems, check.describe(ctx), time.perf_counter() - start)


def main():
    parser = argparse.ArgumentParser(description="Accessibility and link audit for the built site.")
    parser.add_argument("--external", action="store_true", help="also request every outbound URL")
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    parser.add_argument(
        "--only",
        metavar="NAME",
        help="run only checks whose name contains NAME (comma-separated)",
    )
    parser.add_argument("--list", action="store_true", help="list the check names and exit")
    args = parser.parse_args()

    checks = registry()
    if args.list:
        for check in checks:
            print(check.name)
        return 0

    missing = [
        package
        for package in ("playwright", "axe_playwright_python")
        if importlib.util.find_spec(package) is None
    ]
    if missing:
        print("Missing audit dependencies. Run: pip install -r build/requirements.txt")
        return 2

    from playwright.sync_api import sync_playwright

    audit = Audit(args.only)
    print("SubFree UK audit")
    if audit.only:
        print(f"  note  only checks matching {', '.join(audit.only)!r}")

    start = time.perf_counter()
    changed, build = rebuild()
    if changed is None:
        print("Rebuild failed:")
        print((build.stderr or build.stdout).strip())
        return 1
    dataset, dataset_error = load_rows()
    ctx = Context(
        audit,
        dataset,
        [dataset_error] if dataset_error else [],
        load_pages(),
        external=args.external,
    )
    ctx.rebuild_problems = [] if not changed else [
        "rebuild changed " + ", ".join(changed) + "; commit the regenerated files"
    ]

    run_phase(checks, "static", ctx, audit)
    note_pending(ctx)

    wanted = {check.phase for check in checks if audit.wants(check.name)}
    if wanted - {"static"}:
        httpd = serve()
        ctx.url = f"http://127.0.0.1:{httpd.server_address[1]}/index.html"
        try:
            with sync_playwright() as playwright:
                ctx.playwright = playwright
                try:
                    ctx.browser = playwright.chromium.launch(headless=not args.headed)
                except Exception as error:
                    print(f"Could not start Chromium: {error}")
                    print("Run: python -m playwright install chromium")
                    return 2
                context = ctx.browser.new_context(
                    viewport={"width": 390, "height": 844},
                    permissions=["clipboard-read", "clipboard-write"],
                )
                page = context.new_page()
                page.add_init_script("try { localStorage.setItem('theme', 'dark') } catch (e) {}")
                page.on("pageerror", lambda error: ctx.console_errors.append(str(error)))
                page.on(
                    "console",
                    lambda message: ctx.console_errors.append(message.text)
                    if message.type == "error"
                    else None,
                )
                ctx.page = page

                if "phone" in wanted:
                    page.goto(ctx.url, wait_until="load")
                    run_phase(checks, "phone", ctx, audit)

                if wanted & {"desktop", "compare"}:
                    page.set_viewport_size({"width": 1280, "height": 900})
                    page.goto(ctx.url, wait_until="load")
                    page.wait_for_timeout(200)
                if "desktop" in wanted:
                    run_phase(checks, "desktop", ctx, audit)
                if "compare" in wanted:
                    ctx.ensure_compare()
                    run_phase(checks, "compare", ctx, audit)
                run_phase(checks, "post", ctx, audit)
                ctx.browser.close()
        finally:
            httpd.shutdown()
            httpd.server_close()

    run_phase(checks, "report", ctx, audit)

    for note in audit.notes:
        print(f"  note  {note}")

    slowest = audit.slowest()
    if slowest and len(audit.results) > 3:
        print(
            "  note  slowest: "
            + ", ".join(f"{result['name']} {result['seconds'] * 1000:.0f}ms" for result in slowest)
        )
    if audit.skipped:
        print(f"  note  skipped {len(audit.skipped)} check(s) outside --only")

    issues = audit.failed()
    print()
    if issues:
        print(f"Result: FAIL, {len(issues)} issue(s)")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(f"Result: PASS, {len(audit.results)} checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
