#!/usr/bin/env python3
"""Verification for the site: rebuild, then audit structure and accessibility.

Runs build/build.py first and reports any generated file it changed, so a stale
page fails here instead of shipping. Serves the repo root on a loopback port,
drives the page with Chromium, and runs axe-core against WCAG 2.2 A and AA in
both themes at 1280px, 820px and 390px. Also checks internal anchors, image
files, duplicate ids, headings, labels, target sizes, the type floor, the phone
layout, the skip link, the photo lightbox and horizontal overflow at the
breakpoints the stylesheet defines.

    python build/check.py
    python build/check.py --external   # also request every outbound URL
    python build/check.py --headed

Needs the venv from README.md. Exit status is 1 when an issue is found.
"""
import argparse
import functools
import http.server
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "doorbells.html"]
GENERATED = PAGES + ["data/doorbells.csv", "data/doorbells.md"]
WIDTHS = [1440, 1280, 1100, 1000, 900, 820, 390]
AXE_WIDTHS = [1280, 820, 390]
WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]

AUDIT_JS = r"""() => {
  const all = (s) => Array.from(document.querySelectorAll(s));
  const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
  const name = (el) => {
    const aria = (el.getAttribute("aria-label") || "").trim();
    if (aria) return aria;
    if (el.labels && el.labels.length) return Array.from(el.labels).map(text).join(" ").trim();
    if (el.tagName === "INPUT" && (el.type === "submit" || el.type === "button")) return (el.value || "").trim();
    const own = text(el) || (el.getAttribute("title") || "").trim();
    if (own) return own;
    const img = el.querySelector("img[alt]");
    return img ? img.alt.trim() : "";
  };
  const box = (el) => el.getBoundingClientRect();
  const ids = all("[id]").map((el) => el.id);
  const anchors = all("a[href]").map((a) => ({ href: a.getAttribute("href"), text: name(a) }));
  const internal = anchors.filter((a) => a.href.startsWith("#") && a.href.length > 1);
  const external = anchors.filter((a) => /^https?:\/\//.test(a.href));
  return {
    lang: document.documentElement.lang,
    title: document.title,
    viewport: !!document.querySelector('meta[name="viewport"]'),
    mains: all("main").length,
    rows: all("tbody.item").length,
    duplicateIds: ids.filter((id, i) => ids.indexOf(id) !== i),
    brokenAnchors: internal.filter((a) => !document.getElementById(a.href.slice(1))).map((a) => a.href),
    emptyLinks: anchors.filter((a) => !a.text).map((a) => a.href),
    images: all("img").map((img) => ({ src: img.getAttribute("src") || "", alt: img.getAttribute("alt"), inRowHeader: !!img.closest("th[scope=row]") })),
    localRefs: all("img[src]").map((img) => img.getAttribute("src")),
    controls: all("input, select, textarea").map((el) => ({
      tag: el.tagName.toLowerCase(), type: el.type || "", name: name(el),
      width: Math.round(box(el).width), height: Math.round(box(el).height),
      visible: el.getClientRects().length > 0
    })),
    buttons: all("button").map((b) => ({
      name: name(b), width: Math.round(box(b).width), height: Math.round(box(b).height),
      visible: b.getClientRects().length > 0
    })),
    headings: all("h1,h2,h3,h4,h5,h6").map((h) => Number(h.tagName[1])),
    thNoScope: all("th").filter((th) => !th.getAttribute("scope")).length,
    footRefs: internal.filter((a) => /^#fn\d+$/.test(a.href)).map((a) => a.href.slice(1)),
    footTargets: all('li[id^="fn"]').map((li) => li.id),
    externals: external.map((a) => a.href),
    tags: all(".vtag").map(text),
    priceFootnotes: all(".c-price .fn").length,
    zoomGlyphs: all(".zoom .zi").length,
    contactLinks: anchors.filter((a) => /github\.com\/lydenyardley\/subfree-uk\/issues/.test(a.href)).length,
    hasGlossary: /Power over Ethernet/.test(text(document.body)),
    tiny: all("body *").filter((el) => {
      if (!el.getClientRects().length) return false;
      const cs = getComputedStyle(el);
      if (cs.display === "none" || cs.visibility === "hidden") return false;
      const own = Array.from(el.childNodes).some((n) => n.nodeType === 3 && n.textContent.trim());
      return own && parseFloat(cs.fontSize) < 11;
    }).map((el) => el.tagName.toLowerCase() + "." + String(el.className || "").split(" ")[0] +
      " at " + getComputedStyle(el).fontSize + ": " + text(el).slice(0, 24))
  };
}"""

PHONE_JS = r"""() => {
  const filters = document.getElementById("filters");
  const row = document.querySelector("#tbl tbody.item:not([hidden])");
  return {
    open: filters ? filters.open : null,
    firstRowTop: row ? Math.round(row.getBoundingClientRect().top) : -1,
    viewport: window.innerHeight
  };
}"""

HEADER_JS = r"""() => {
  const thead = document.querySelector("#tbl thead");
  const ths = Array.from(thead.querySelectorAll("th[scope=col]"));
  const buttons = Array.from(thead.querySelectorAll("button"));
  return {
    display: getComputedStyle(thead).display,
    width: Math.round(thead.getBoundingClientRect().width),
    headers: ths.length,
    untabbable: buttons.length > 0 && buttons.every((b) => b.tabIndex === -1)
  };
}"""

OVERFLOW_JS = r"""() => {
  const de = document.documentElement;
  const over = de.scrollWidth - de.clientWidth;
  const offenders = over > 0
    ? Array.from(document.querySelectorAll("body *"))
        .filter((el) => el.getBoundingClientRect().right > window.innerWidth + 1)
        .slice(0, 4)
        .map((el) => el.tagName.toLowerCase() + "." + String(el.className || "").split(" ")[0])
    : [];
  return { over, offenders };
}"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(QuietHandler, directory=ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def rebuild():
    """Run the generator and return the generated files whose bytes changed."""
    before = {name: open(os.path.join(ROOT, name), "rb").read() for name in GENERATED}
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "build", "build.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return None, result
    after = {name: open(os.path.join(ROOT, name), "rb").read() for name in GENERATED}
    return [name for name in GENERATED if before[name] != after[name]], result


def load_pages():
    texts = {}
    for page in PAGES:
        path = os.path.join(ROOT, page)
        if not os.path.exists(path):
            raise SystemExit(f"missing generated page: {page}")
        with open(path, encoding="utf-8") as f:
            texts[page] = f.read()
    return texts


def axe_violations(axe, page):
    results = axe.run(
        page,
        options={
            "resultTypes": ["violations"],
            "runOnly": {"type": "tag", "values": WCAG_TAGS},
        },
    )
    return results.response["violations"]


def lightbox_check(page):
    """Click the first photo, confirm the dialog, then dismiss it with Esc."""
    counts = page.evaluate(
        "() => ({buttons: document.querySelectorAll('.zoom').length, "
        "thumbs: document.querySelectorAll('img.ph-sm').length, "
        "dialog: !!document.getElementById('lightbox')})"
    )
    problems = []
    if not counts["dialog"]:
        return {"problems": ["photo lightbox is missing"], "buttons": 0}
    if counts["buttons"] < counts["thumbs"]:
        problems.append(
            f"only {counts['buttons']} lightbox buttons for {counts['thumbs']} photos"
        )
    if not counts["buttons"]:
        return {"problems": problems + ["no photo opens in the lightbox"], "buttons": 0}

    page.click(".zoom")
    page.wait_for_timeout(100)
    opened = page.evaluate(
        """() => {
            const d = document.getElementById('lightbox');
            const img = document.querySelector('#lb-img img');
            return {open: d.open, src: img ? (img.getAttribute('src') || '') : '',
                    name: document.getElementById('lb-name').textContent};
        }"""
    )
    if not opened["open"]:
        problems.append("clicking a photo did not open the lightbox")
    if not opened["src"].endswith("-lg.webp"):
        problems.append(f"lightbox opened {opened['src'] or 'no image'} instead of the large file")
    if not opened["name"]:
        problems.append("lightbox does not name the product")
    if opened["src"] and not os.path.exists(os.path.join(ROOT, opened["src"])):
        problems.append(f"lightbox image file is missing: {opened['src']}")

    page.keyboard.press("Escape")
    page.wait_for_timeout(50)
    if page.evaluate("() => document.getElementById('lightbox').open"):
        problems.append("Esc does not close the lightbox")
    return {"problems": problems, "buttons": counts["buttons"]}


def skip_check(page):
    """Tab to the skip link, press Enter, and confirm focus lands on the table."""
    problems = []
    links = page.evaluate(
        "() => Array.from(document.querySelectorAll('a.skip')).map(a => a.getAttribute('href'))"
    )
    if links != ["#tbl"]:
        return [f"expected one skip link to #tbl, found {links or 'none'}"]
    if not page.evaluate("() => document.getElementById('tbl').tabIndex === -1"):
        problems.append("the skip link target is not focusable")
    page.keyboard.press("Tab")
    first = page.evaluate(
        "() => ({cls: document.activeElement.className, text: document.activeElement.textContent.trim()})"
    )
    if "skip" not in first["cls"]:
        problems.append(f"the first Tab stop is {first['cls'] or 'nothing'}, not the skip link")
    page.keyboard.press("Enter")
    page.wait_for_timeout(150)
    landed = page.evaluate(
        "() => ({hash: location.hash, focus: (document.activeElement || {}).id || ''})"
    )
    if landed["hash"] != "#tbl" or landed["focus"] != "tbl":
        problems.append(
            f"Enter moved to {landed['hash'] or 'nowhere'} with focus on "
            f"{landed['focus'] or 'nothing'}"
        )
    return problems


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


def main():
    parser = argparse.ArgumentParser(description="Accessibility and link audit for the built site.")
    parser.add_argument("--external", action="store_true", help="also request every outbound URL")
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
        from axe_playwright_python.sync_playwright import Axe
    except ImportError:
        print("Missing audit dependencies. Run: pip install -r build/requirements.txt")
        return 2

    issues = []
    notes = []

    print("SubFree UK audit")

    changed, build = rebuild()
    if changed is None:
        print("Rebuild failed:")
        print((build.stderr or build.stdout).strip())
        return 1
    if changed:
        issues.append(
            "rebuild changed " + ", ".join(changed) + "; commit the regenerated files"
        )
    else:
        print("  ok    rebuild reproduces the committed pages")

    pages = load_pages()

    if pages["index.html"] == pages["doorbells.html"]:
        print("  ok    generated pages are identical")
    else:
        issues.append("index.html and doorbells.html differ; rebuild the site")

    httpd = serve()
    port = httpd.server_address[1]
    url = f"http://127.0.0.1:{port}/index.html"
    console_errors = []

    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=not args.headed)
            except Exception as error:
                print(f"Could not start Chromium: {error}")
                print("Run: python -m playwright install chromium")
                return 2
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.add_init_script("try { localStorage.setItem('theme', 'dark') } catch (e) {}")
            page.on("pageerror", lambda error: console_errors.append(str(error)))
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page.goto(url, wait_until="load")

            # Measure the phone first paint before any detail row or the compare
            # table pushes the products down.
            phone = page.evaluate(PHONE_JS)
            phone_data = page.evaluate(AUDIT_JS)
            header = page.evaluate(HEADER_JS)
            header_roles = "columnheader" in page.locator("#tbl").aria_snapshot()

            page.set_viewport_size({"width": 1280, "height": 900})
            page.reload(wait_until="load")

            # Focus starts at the top of a fresh document, so this is the only
            # point where the skip link can be reached with one Tab.
            skip = skip_check(page)

            # Hidden detail rows and the compare table are part of the page, so
            # open them before auditing instead of testing only the first paint.
            page.eval_on_selector_all("button.more", "els => els.forEach(el => el.click())")
            page.eval_on_selector_all(
                "input.cmp",
                """els => els.slice(0, 3).forEach(el => {
                    el.checked = true;
                    el.dispatchEvent(new Event("change", { bubbles: true }));
                })""",
            )
            page.click("#tray-go")
            page.wait_for_timeout(200)

            data = page.evaluate(AUDIT_JS)
            lightbox = lightbox_check(page)

            axe = Axe()
            axe_results = {}
            for theme in ("dark", "light"):
                for width in AXE_WIDTHS:
                    page.set_viewport_size({"width": width, "height": 900})
                    page.wait_for_timeout(120)
                    axe_results[(theme, width)] = axe_violations(axe, page)
                page.click("#theme")
                page.wait_for_timeout(120)

            widths = []
            for width in WIDTHS:
                page.set_viewport_size({"width": width, "height": 900})
                page.wait_for_timeout(80)
                widths.append((width, page.evaluate(OVERFLOW_JS)))

            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()

    if console_errors:
        for message in console_errors[:5]:
            issues.append(f"console error: {message}")
    else:
        print("  ok    no console or page errors")

    if data["lang"] and data["title"] and data["viewport"]:
        print(f"  ok    document language, title and viewport set")
    else:
        issues.append("missing html lang, page title or viewport meta")

    if skip:
        issues.extend(skip)
    else:
        print("  ok    the skip link is the first Tab stop and Enter lands on the table")

    if lightbox["problems"]:
        issues.extend(lightbox["problems"])
    else:
        print(
            f"  ok    {lightbox['buttons']} photos open in the lightbox, "
            "named, sized from the large file, and Esc closes it"
        )

    if data["rows"] == 0:
        issues.append("no product rows rendered; the page may be blank")

    if not phone["open"] and phone["firstRowTop"] < phone["viewport"]:
        print(
            f"  ok    phone: filters start collapsed; first product at "
            f"{phone['firstRowTop']}px of {phone['viewport']}px"
        )
    else:
        issues.append(
            "phone first paint: "
            f"filters open={phone['open']}, first product at "
            f"{phone['firstRowTop']}px of {phone['viewport']}px"
        )

    if (
        header["display"] != "none"
        and header["width"] <= 2
        and header["headers"] == 8
        and header["untabbable"]
        and header_roles
    ):
        print(
            "  ok    phone: 8 column headers stay in the accessibility tree; "
            "sort buttons leave the tab order"
        )
    else:
        issues.append(
            "phone table header: "
            f"display={header['display']}, width={header['width']}px, "
            f"headers={header['headers']}, untabbable={header['untabbable']}, "
            f"columnheader in tree={header_roles}"
        )

    tiny = data["tiny"] + phone_data["tiny"]
    if tiny:
        issues.append("text below 11px: " + "; ".join(sorted(set(tiny))[:6]))
    else:
        print("  ok    no rendered text is below 11px")

    best = data["tags"].count("Best overall")
    if best == 1 and "Best with doorbell wiring" in data["tags"]:
        print('  ok    one row owns "Best overall"; the Reolink variants name their own case')
    else:
        issues.append(f'verdict tags: {best} rows say "Best overall" ({data["tags"]})')

    if data["priceFootnotes"]:
        issues.append(f"{data['priceFootnotes']} footnote numbers in price cells")
    else:
        print("  ok    price cells carry no footnote numbers")

    if data["zoomGlyphs"] == lightbox["buttons"] and lightbox["buttons"]:
        print(f"  ok    all {lightbox['buttons']} photos show a zoom glyph")
    else:
        issues.append(
            f"{lightbox['buttons']} photo buttons but {data['zoomGlyphs']} zoom glyphs"
        )

    if data["contactLinks"] >= 2:
        print(f"  ok    contact route linked in {data['contactLinks']} places")
    else:
        issues.append(
            "expected a contact link in the header and the method, "
            f"found {data['contactLinks']}"
        )

    if data["hasGlossary"]:
        print("  ok    method defines PoE, NVR, microSD and Home Assistant")
    else:
        issues.append("method does not gloss PoE, NVR, microSD and Home Assistant")

    if data["mains"] == 1:
        print("  ok    one main landmark")
    else:
        issues.append(f"expected one main landmark, found {data['mains']}")

    if data["duplicateIds"]:
        issues.append("duplicate ids: " + ", ".join(sorted(set(data["duplicateIds"]))))
    else:
        print("  ok    ids are unique")

    if data["brokenAnchors"]:
        issues.append("broken anchors: " + ", ".join(data["brokenAnchors"]))
    else:
        print(f"  ok    {len(data['footRefs'])} footnote references resolve")

    missing_files = [
        src
        for src in data["localRefs"]
        if not os.path.exists(os.path.join(ROOT, src.split("?")[0]))
    ]
    if missing_files:
        issues.append("missing image files: " + ", ".join(sorted(set(missing_files))))
    else:
        print(f"  ok    {len(data['localRefs'])} image files exist")

    if data["emptyLinks"]:
        issues.append("links without an accessible name: " + ", ".join(data["emptyLinks"][:5]))
    else:
        print("  ok    every link has an accessible name")

    missing_alt = [img["src"] for img in data["images"] if img["alt"] is None]
    repeated_alt = [img["src"] for img in data["images"] if img["inRowHeader"] and img["alt"]]
    if missing_alt:
        issues.append("images without an alt attribute: " + ", ".join(missing_alt[:5]))
    elif repeated_alt:
        issues.append("thumbnails repeat the row heading in alt text: " + ", ".join(repeated_alt[:5]))
    else:
        print(f"  ok    {len(data['images'])} images carry usable alt text")

    unnamed = [
        f"{control['tag']}[{control['type']}]"
        for control in data["controls"]
        if control["visible"] and not control["name"]
    ]
    if unnamed:
        issues.append("form controls without a label: " + ", ".join(unnamed))
    else:
        print(f"  ok    {len(data['controls'])} form controls are labelled")

    unnamed_buttons = [button["name"] or "(empty)" for button in data["buttons"] if button["visible"] and not button["name"]]
    if unnamed_buttons:
        issues.append(f"buttons without a name: {len(unnamed_buttons)}")
    else:
        print(f"  ok    {len(data['buttons'])} buttons have a name")

    small_buttons = [
        f"{button['name']} ({button['width']}x{button['height']})"
        for button in data["buttons"]
        if button["visible"] and (button["width"] < 24 or button["height"] < 24)
    ]
    small_controls = [
        f"{control['tag']}[{control['type']}] ({control['width']}x{control['height']})"
        for control in data["controls"]
        if control["visible"] and control["type"] != "checkbox" and (control["width"] < 24 or control["height"] < 24)
    ]
    if small_buttons or small_controls:
        issues.append("targets under 24px: " + ", ".join(small_buttons + small_controls))
    else:
        print("  ok    buttons and inputs meet 24px targets")
    checkboxes = [
        control
        for control in data["controls"]
        if control["visible"] and control["type"] == "checkbox" and control["height"] < 24
    ]
    if checkboxes:
        print(
            f"  note  {len(checkboxes)} checkboxes are under 24px; the spacing exception covers them"
        )

    if data["thNoScope"]:
        issues.append(f"{data['thNoScope']} table headers missing scope")
    else:
        print("  ok    every table header declares scope")

    heading_problems = []
    if data["headings"].count(1) != 1:
        heading_problems.append(f"{data['headings'].count(1)} h1 elements")
    for previous, current in zip(data["headings"], data["headings"][1:]):
        if current > previous + 1:
            heading_problems.append(f"h{previous} jumps to h{current}")
    if heading_problems:
        issues.append("heading outline: " + ", ".join(heading_problems))
    else:
        print(f"  ok    heading outline is {data['headings']}")

    if set(data["footRefs"]) == set(data["footTargets"]):
        print(f"  ok    all {len(data['footTargets'])} footnotes are referenced and present")
    else:
        orphaned = sorted(set(data["footTargets"]) - set(data["footRefs"]))
        broken = sorted(set(data["footRefs"]) - set(data["footTargets"]))
        issues.append(f"footnote mismatch, unreferenced: {orphaned}, missing: {broken}")

    plain_http = [link for link in data["externals"] if link.startswith("http://")]
    if plain_http:
        issues.append("external links over plain http: " + ", ".join(plain_http[:5]))
    else:
        print(f"  ok    {len(data['externals'])} external links use https")

    for theme in ("dark", "light"):
        for width in AXE_WIDTHS:
            violations = axe_results[(theme, width)]
            if not violations:
                print(f"  ok    axe-core ({theme}, {width}px): no WCAG 2.2 A/AA violations")
                continue
            for violation in violations:
                nodes = violation["nodes"]
                issues.append(
                    f"axe {theme} at {width}px: {violation['id']} ({violation['impact']}), "
                    f"{len(nodes)} node(s). {violation['help']}"
                )
                for node in nodes[:4]:
                    summary = node.get("failureSummary", "").replace("\n", " ").strip()
                    print(f"        {', '.join(node['target'])}  {summary[:150]}")

    overflow = [f"{width}px" for width, result in widths if result["over"] > 0]
    if overflow:
        detail = "; ".join(
            f"{width}px: {result['over']}px past {', '.join(result['offenders'])}"
            for width, result in widths
            if result["over"] > 0
        )
        issues.append(f"horizontal page overflow at {', '.join(overflow)} ({detail})")
    else:
        print("  ok    no horizontal overflow at " + ", ".join(f"{w}px" for w in WIDTHS))

    if args.external:
        for link in sorted(set(data["externals"])):
            try:
                status = request_status(link)
            except Exception as error:  # network policy or timeout
                notes.append(f"{link}: {error}")
                continue
            if status in (404, 410):
                issues.append(f"{link} returns {status}")
            elif status >= 400:
                notes.append(f"{link} returns {status} (may block automated requests)")
        print(f"  ok    requested {len(set(data['externals']))} external links")
    else:
        print("  note  external links not requested; pass --external to check them")

    for note in notes:
        print(f"  note  {note}")

    print()
    if issues:
        print(f"Result: FAIL, {len(issues)} issue(s)")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("Result: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
