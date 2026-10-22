"""The engines and the network: no JavaScript, Firefox, the console and outbound links."""
import urllib.error
import urllib.request

from .accessibility import axe_violations
from .context import WCAG_TAGS
from .js import AUDIT_JS, DESKTOP_ROWS_JS
from .registry import Check, Skip


def request_status(url):
    # Some shops answer 404 to HEAD and 200 to GET, so ask the way a reader
    # would and never read the body.
    request = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; subfree-uk-link-check/1.0)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code

def nojs_check(browser, url, row_count):
    """Without JavaScript the inert filters are hidden and the table still stands."""
    problems = []
    context = browser.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        page.goto(url, wait_until="load")
        page.wait_for_timeout(100)
        state = {
            "controls": page.locator(".controls").is_visible(),
            "note": page.locator(".nojs").inner_text()
            if page.locator(".nojs").count()
            else "",
            "rows": page.locator("#tbl tbody.item").count(),
            "theme": page.locator("#theme").is_visible(),
            "details": page.locator(".more-w").first.is_visible(),
        }
    finally:
        context.close()
    if state["controls"]:
        problems.append("filter controls stay visible without JavaScript")
    if state["theme"]:
        problems.append("the inert theme toggle stays visible without JavaScript")
    if state["details"]:
        problems.append("the inert Details buttons stay visible without JavaScript")
    if "need JavaScript" not in state["note"]:
        problems.append(f"no no-JavaScript note: {state['note']!r}")
    if state["rows"] < row_count:
        problems.append(f"only {state['rows']} rows render without JavaScript")
    return problems

def firefox_check(playwright, url, row_count):
    """The structural half in Firefox: the engine whose fallbacks differ.

    Chromium alone cannot prove content-visibility, the grid rows or the
    accessibility tree behave elsewhere; this loads the same page in Firefox and
    runs the same structure audit, axe and overflow checks.
    """
    problems = []
    from axe_playwright_python.sync_playwright import Axe
    try:
        browser = playwright.firefox.launch(headless=True)
    except Exception as error:
        return [f"Firefox did not start ({error}). Run: python -m playwright install firefox"]
    context = None
    try:
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(message.text) if message.type == "error" else None,
        )
        page.goto(url, wait_until="load")
        page.wait_for_timeout(500)
        phone = page.evaluate(AUDIT_JS)
        if phone["rows"] != row_count:
            problems.append(f"Firefox rendered {phone['rows']} rows")
        if phone["duplicateIds"] or phone["brokenAnchors"]:
            problems.append("Firefox: duplicate ids or broken anchors")
        if phone["emptyLinks"]:
            problems.append(f"Firefox: {len(phone['emptyLinks'])} links without a name")
        if set(phone["footRefs"]) != set(phone["footTargets"]):
            problems.append("Firefox: footnote references do not match their targets")
        if len(phone["headings"]) < 5:
            problems.append(f"Firefox: heading outline has {len(phone['headings'])} entries")
        if "columnheader" not in page.locator("#tbl").aria_snapshot():
            problems.append("Firefox: the table header is missing from the accessibility tree")
        card = page.evaluate(
            """() => ({
                visibility: getComputedStyle(document.querySelector('#tbl tbody.item')).contentVisibility,
                size: getComputedStyle(document.querySelector('#tbl tbody.item')).containIntrinsicSize,
                overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth
            })"""
        )
        if card["visibility"] != "auto" or not card["size"].startswith("auto "):
            problems.append(f"Firefox: the phone cards are not contained: {card}")
        if card["overflow"] > 0:
            problems.append(f"Firefox: {card['overflow']}px of horizontal overflow at 390px")

        axe = Axe()
        results = {}
        for theme in ("dark", "light"):
            for width in (390, 1280):
                page.set_viewport_size({"width": width, "height": 900})
                page.wait_for_timeout(150)
                results[(theme, width)] = axe_violations(axe, page)
            page.click("#theme")
            page.wait_for_timeout(150)
        for (theme, width), violations in results.items():
            for violation in violations:
                if set(violation["tags"]) & set(WCAG_TAGS):
                    problems.append(
                        f"Firefox axe {theme} at {width}px: {violation['id']} "
                        f"({violation['impact']}), {len(violation['nodes'])} node(s)"
                    )

        page.set_viewport_size({"width": 1280, "height": 900})
        page.wait_for_timeout(200)
        wide = page.evaluate(DESKTOP_ROWS_JS)
        if wide["display"] != "grid" or wide["tracks"] != 8:
            problems.append(
                f"Firefox at 1280px: a row is {wide['display']!r} with {wide['tracks']} tracks"
            )
        if wide["visibility"] != "auto":
            problems.append(f"Firefox at 1280px: rows are not contained ({wide['visibility']!r})")
        if wide["clipped"]:
            problems.append(f"Firefox at 1280px clips a cell: {wide['clipped'][0]}")
        if errors:
            problems.append(f"Firefox page errors: {errors[:3]}")
    finally:
        if context:
            context.close()
        browser.close()
    return problems

def external_links(ctx):
    if not ctx.external:
        raise Skip("--external was not passed")
    problems = []
    links = sorted(set(ctx.snapshot["externals"]))
    for link in links:
        try:
            status = request_status(link)
        except Exception as error:
            ctx.note(f"{link}: {error}")
            continue
        if status in (404, 410):
            problems.append(f"{link} returns {status}")
        elif status >= 400:
            ctx.note(f"{link} returns {status} (may block automated requests)")
    return problems


def console_errors(ctx):
    return [f"console error: {message}" for message in ctx.console_errors[:5]]

CHECKS = [
    Check(
        "no JavaScript", "post", 79,
        "without JavaScript the inert controls are hidden and every row remains",
        lambda ctx: nojs_check(ctx.browser, ctx.url, ctx.row_count),
    ),
    Check(
        "firefox structural pass", "post", 80,
        "Firefox renders the same structure, layout and axe results",
        lambda ctx: firefox_check(ctx.playwright, ctx.url, ctx.row_count),
    ),
    Check(
        "console errors", "report", 81, "no console or page errors",
        console_errors,
    ),
    Check(
        "external links", "report", 82,
        lambda ctx: f"requested {len(set(ctx.snapshot['externals']))} external links",
        external_links,
    ),
]

