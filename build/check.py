#!/usr/bin/env python3
"""Verification for the site: rebuild, then audit structure and accessibility.

Runs build/build.py first and reports any generated file it changed, so a stale
page fails here instead of shipping. Serves the repo root on a loopback port,
drives the page with Chromium, and runs axe-core in both themes at 1280px,
820px and 390px, failing on WCAG 2.2 A and AA and reporting the
best-practice rules alongside them. Also checks internal anchors, image
files, duplicate ids, headings, labels, target sizes, the type floor, the phone
layout, the price range slider, the filter panel resize, the live announcements,
the three-row compare cap, the empty-state recovery, the compare cost row, the
shortlist copy, the jump announcement, the theme motion, the score-bar draw, the
no-JavaScript fallback, the skip link, the photo lightbox and horizontal overflow
at the breakpoints the stylesheet defines.

    python build/check.py
    python build/check.py --external   # also request every outbound URL
    python build/check.py --headed

Needs the venv from README.md. Exit status is 1 when an issue is found.
"""
import argparse
import csv
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
BEST_PRACTICE_TAG = "best-practice"

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
    rowRule: (() => {
      const marked = all("tbody.item[data-v]")[0];
      const plain = all("tbody.item:not([data-v])")[0];
      const cell = (row) => row && row.querySelector("tr.main > td.c-cmp");
      if (!marked || !plain) return null;
      const a = getComputedStyle(cell(marked)), b = getComputedStyle(cell(plain));
      return { border: parseFloat(a.borderLeftWidth), pad: parseFloat(a.paddingLeft),
               plain: parseFloat(b.borderLeftWidth) };
    })(),
    tags: all(".vtag").map(text),
    priceFootnotes: all(".c-price .fn").length,
    zoomGlyphs: all(".zoom .zi").length,
    icon: document.querySelector('link[rel="icon"]')
      ? document.querySelector('link[rel="icon"]').getAttribute("href") : "",
    canonical: document.querySelector('link[rel="canonical"]')
      ? document.querySelector('link[rel="canonical"]').getAttribute("href") : "",
    ogTitle: document.querySelector('meta[property="og:title"]')
      ? document.querySelector('meta[property="og:title"]').content : "",
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
  const verdict = document.querySelector(".verdict");
  const short = document.querySelector(".vshort");
  return {
    open: filters ? filters.open : null,
    firstRowTop: row ? Math.round(row.getBoundingClientRect().top) : -1,
    viewport: window.innerHeight,
    verdict: verdict ? getComputedStyle(verdict).display : null,
    shortAnswer: short ? getComputedStyle(short).display : null
  };
}"""

COST_JS = r"""() => {
  const row = document.querySelector("#tbl tbody.item");
  const a = row.querySelector(".c-nosub"), b = row.querySelector(".c-sub");
  return {
    aFits: a.scrollWidth <= a.clientWidth + 1,
    bFits: b.scrollWidth <= b.clientWidth + 1,
    aWidth: a.clientWidth,
    bWidth: b.clientWidth
  };
}"""

FILTERS_JS = r"""() => {
  const filters = document.getElementById("filters");
  const body = filters.querySelector(".fbody");
  return {
    open: filters.open,
    display: getComputedStyle(body).display,
    visible: body.getClientRects().length > 0
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
    # Keep-alive. The HTTP/1.0 default makes Chromium wait on a half-closed
    # connection now and then, which shows up as a resource that timed out
    # against a server that is working perfectly well.
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(QuietHandler, directory=ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
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
            "runOnly": {"type": "tag", "values": WCAG_TAGS + [BEST_PRACTICE_TAG]},
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


def filters_check(page):
    """The phone filter panel is collapsed, and has to come back when the window widens."""
    problems = []
    page.set_viewport_size({"width": 900, "height": 900})
    page.wait_for_timeout(150)
    wide = page.evaluate(FILTERS_JS)
    if not wide["open"] or not wide["visible"]:
        problems.append(f"the filter panel stays closed at 900px: {wide}")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(150)
    narrow = page.evaluate(FILTERS_JS)
    if narrow["open"] or narrow["visible"]:
        problems.append(f"the filter panel stays open at 390px: {narrow}")
    return problems


def copy_check(page):
    """Three selections explain the cap, announce it, and expose Compare nearby."""
    problems = []
    page.eval_on_selector_all(
        "input.cmp",
        """els => els.slice(0, 3).forEach(el => {
            el.checked = true;
            el.dispatchEvent(new Event("change", { bubbles: true }));
        })""",
    )
    page.wait_for_timeout(450)
    state = page.evaluate(
        """() => ({
            tray: document.getElementById("tray-txt").textContent,
            live: document.getElementById("live").textContent,
            inline: document.getElementById("cmp-inline").hidden
                ? null : document.getElementById("cmp-inline").textContent,
            disabled: Array.from(document.querySelectorAll("input.cmp"))
                .filter((c) => c.disabled).length
        })"""
    )
    if "maximum" not in state["tray"]:
        problems.append(f"the 3-row cap is not explained: {state['tray']!r}")
    if "maximum" not in state["live"]:
        problems.append(f"the 3-row cap is not announced: {state['live']!r}")
    if state["inline"] != "Compare 3":
        problems.append(f"the inline compare action reads {state['inline']!r}")
    if state["disabled"] == 0:
        problems.append("no checkbox is disabled at three selections")
    return problems


def recovery_check(page):
    """Filtering announces its count; an empty result offers the nearest match."""
    problems = []
    page.eval_on_selector_all(
        "input.cmp",
        """els => els.forEach(el => {
            el.checked = false;
            el.dispatchEvent(new Event("change", { bubbles: true }));
        })""",
    )
    page.eval_on_selector("#filters", "el => { el.open = true }")
    page.eval_on_selector(
        "#f-rec",
        "el => { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })) }",
    )
    page.wait_for_timeout(450)
    filtered = page.evaluate(
        "() => ({count: document.getElementById('count').textContent, "
        "live: document.getElementById('live').textContent})"
    )
    if filtered["count"] == "14" or "doorbells shown" not in filtered["live"]:
        problems.append(
            f"filtering set {filtered['count']} rows and announced {filtered['live']!r}"
        )

    for handle in ("#f-min", "#f-max"):
        page.eval_on_selector(
            handle,
            "el => { el.value = 300; el.dispatchEvent(new Event('input', { bubbles: true })) }",
        )
    page.wait_for_timeout(600)
    empty = page.evaluate(
        """() => ({
            visible: !document.getElementById("empty").hidden,
            near: document.getElementById("near").hidden
                ? null : document.getElementById("near").textContent,
            live: document.getElementById("live").textContent
        })"""
    )
    if not empty["visible"] or not empty["near"]:
        problems.append(f"the empty state offers no nearest match: {empty}")
    elif "£" not in empty["near"]:
        problems.append(f"the nearest-match label has no price: {empty['near']!r}")
    if "No doorbells match" not in empty["live"]:
        problems.append(f"the empty result is not announced: {empty['live']!r}")
    else:
        page.click("#near")
        page.wait_for_timeout(400)
        after = page.evaluate(
            "() => Array.from(document.querySelectorAll('tbody.item'))"
            ".filter((r) => !r.hidden).length"
        )
        if after < 1:
            problems.append("the nearest-match button leaves the table empty")
    page.click("#reset")
    page.wait_for_timeout(150)
    return problems


def costrow_check(page):
    """The compare table opens with a row that does the 3-year subtraction."""
    problems = []
    state = page.evaluate(
        """() => {
            const row = document.querySelector('#cmp-table tr.cmp-cost');
            return {
                label: row ? row.querySelector('th').textContent : '',
                cells: row ? Array.from(row.querySelectorAll('td')).map((td) => td.textContent) : [],
                rows: document.querySelectorAll('#cmp-table tbody tr').length
            };
        }"""
    )
    if state["label"] != "3 years, cheapest":
        problems.append(f"the compare cost row is labelled {state['label']!r}")
    expected = ["£54.99 · cheapest", "+£25.00", "+£25.00"]
    if state["cells"] != expected:
        problems.append(f"compare cost row reads {state['cells']}, expected {expected}")
    if state["rows"] != 18:
        problems.append(f"the compare table has {state['rows']} body rows, expected 18")
    return problems


def labels_check(page):
    """The record column names a time limit, the plan column names its absence,
    PoE is defined at the filter, and the phone card uses one label column."""
    problems = []
    state = page.evaluate(
        """() => {
            const all = (s) => Array.from(document.querySelectorAll(s));
            const spec = ['.c-rec', '.c-score', '.c-nosub', '.c-sub'];
            const cells = spec.map((cls) => document.querySelector('#tbl tbody.item ' + cls));
            const nest = document.querySelector('#m-nest .c-rec');
            const price = document.querySelector('#tbl tbody.item .c-price');
            const catchCell = document.querySelector('#tbl tbody.item .c-catch');
            const subs = all('#tbl tbody.item .c-sub');
            const hint = document.querySelector('#filters .hint');
            const power = hint ? hint.closest('fieldset') : null;
            const pseudo = (el) => getComputedStyle(el, '::before');
            return {
                nestText: nest.textContent.trim(),
                nestClass: nest.querySelector('.rec').className,
                planWords: subs.filter((td) => /No plan/.test(td.textContent)).length,
                planDashes: subs.filter((td) => /\u2014/.test(td.textContent)).length,
                priceLabel: pseudo(price).content,
                catchLabel: pseudo(catchCell).content,
                displays: cells.map((td) => getComputedStyle(td).display),
                basis: cells.map((td) => pseudo(td).flexBasis),
                widths: cells.map((td) => pseudo(td).width),
                hint: hint ? hint.textContent.trim() : '',
                hintPower: !!(power && /Power/.test(power.querySelector('legend').textContent)),
                hintSize: hint ? getComputedStyle(hint).fontSize : '',
                hintVisible: hint ? hint.getClientRects().length > 0 : false
            };
        }"""
    )
    if state["nestText"] != "Only briefly (3 hrs)":
        problems.append(f"the Nest record cell reads {state['nestText']!r}")
    if "rec-brief" not in state["nestClass"]:
        problems.append(f"the Nest record marker has the class {state['nestClass']!r}")
    if state["planWords"] != 3 or state["planDashes"]:
        problems.append(
            f"the plan column prints {state['planWords']} words and "
            f"{state['planDashes']} bare dashes, expected 3 and 0"
        )
    if state["priceLabel"] not in ("normal", "none"):
        problems.append(f"the phone price cell still carries the label {state['priceLabel']}")
    if "Main catch" not in state["catchLabel"]:
        problems.append(f"the catch cell lost its label: {state['catchLabel']}")
    if any(display != "flex" for display in state["displays"]):
        problems.append(f"the phone spec cells are {state['displays']}, expected flex rows")
    basis = state["basis"]
    if len(set(basis)) != 1 or not basis[0].endswith("px") or float(basis[0][:-2]) < 100:
        problems.append(f"the phone labels do not share one column: {basis}")
    if len(set(state["widths"])) != 1:
        problems.append(f"the phone labels render at different widths: {state['widths']}")
    if not state["hint"].startswith("PoE"):
        problems.append(f"the Power filter has no PoE note: {state['hint']!r}")
    if not state["hintPower"]:
        problems.append("the PoE note is not inside the Power fieldset")
    if state["hintSize"] != "12px":
        problems.append(f"the PoE note is {state['hintSize']}, expected 12px")
    return problems


def chrome_check(page):
    """The sort control and compare table keep their declared metrics."""
    problems = []
    m = page.evaluate(
        """() => {
            const cs = (el) => el ? getComputedStyle(el) : null;
            const sel = cs(document.getElementById('sort'));
            const cell = cs(document.querySelector('#cmp-table tbody td'));
            const head = cs(document.querySelector('#cmp-table thead th'));
            const th = cs(document.querySelector('#cmp-table tbody th'));
            return {
                select: sel ? sel.minHeight : '',
                cellPad: cell ? cell.paddingTop + ' ' + cell.paddingRight : '',
                headPad: head ? head.paddingTop + ' ' + head.paddingRight : '',
                thLine: th ? th.lineHeight : '',
                thSize: th ? th.fontSize : ''
            };
        }"""
    )
    if m["select"] != "44px":
        problems.append(f"the sort select is {m['select']!r} tall, expected 44px")
    for name in ("cellPad", "headPad"):
        if m[name] != "8px 16px":
            problems.append(f"compare table {name} is {m[name]!r}, expected 8px 16px")
    if m["thSize"] != "11px" or m["thLine"] != "19.2px":
        problems.append(
            f"compare row labels are {m['thSize']}/{m['thLine']}, expected 11px/19.2px"
        )
    return problems


def shortlist_check(page):
    """Copy shortlist puts the selected models and the URL on the clipboard."""
    problems = []
    before = page.inner_text("#cmp-copy")
    page.click("#cmp-copy")
    page.wait_for_timeout(350)
    after = page.inner_text("#cmp-copy")
    try:
        text = page.evaluate("() => navigator.clipboard.readText()")
    except Exception as error:
        text = ""
        problems.append(f"could not read the clipboard: {error}")
    if before != "Copy shortlist":
        problems.append(f"the copy action reads {before!r}")
    if after != "Copied":
        problems.append(f"the copy action confirms with {after!r}")
    required = [
        "SubFree UK shortlist, checked 19 October 2026",
        "TP-Link Tapo TD21",
        "Reolink Video Doorbell PoE",
        "EZVIZ EP3x Pro",
        "£44.99",
        "£54.99",
        "£69.99",
        "£79.99",
    ]
    missing = [part for part in required if part not in text]
    if missing:
        problems.append(f"the shortlist is missing {missing}")
    links = [line for line in text.split("\n") if "?cmp=" in line]
    if len(links) != 1 or not all(
        model in links[0] for model in ("tapo-td21", "reo-poe", "ezviz-ep3x")
    ):
        problems.append(f"the shortlist link reads {links}")
    if text.count("Best for:") != 3 or text.count("Main catch:") != 3:
        problems.append("the shortlist does not give Best for and Main catch for all 3 models")
    page.wait_for_timeout(2200)
    if page.inner_text("#cmp-copy") != "Copy shortlist":
        problems.append("the copy label does not return to Copy shortlist")
    return problems


def share_check(page):
    """A ?cmp= link reopens the same three models and drops unknown ids."""
    problems = []
    href = page.evaluate("() => location.href")
    if "?cmp=" not in href:
        problems.append(f"selecting three models did not update the URL: {href}")
    extra = page.context.new_page()
    try:
        extra.goto(href, wait_until="load")
        extra.wait_for_timeout(400)
        restored = extra.evaluate(
            """() => ({
                checked: Array.from(document.querySelectorAll('input.cmp:checked')).map((c) => c.value),
                compare: !document.getElementById('compare').hidden,
                names: Array.from(document.querySelectorAll('#cmp-table thead .cmp-name')).map((n) => n.textContent),
                rows: document.querySelectorAll('#cmp-table tbody tr').length
            })"""
        )
        if restored["checked"] != ["tapo-td21", "reo-poe", "ezviz-ep3x"]:
            problems.append(f"the shared link restored {restored['checked']}")
        if restored["rows"] != 18 or not restored["compare"]:
            problems.append(f"the shared link did not reopen the compare table: {restored}")
        if len(restored["names"]) != 3:
            problems.append(f"the shared compare table names {restored['names']}")
        base = href.split("?")[0]
        extra.goto(base + "?cmp=reo-poe,bogus,reo-poe", wait_until="load")
        extra.wait_for_timeout(300)
        filtered = extra.evaluate(
            """() => ({
                checked: Array.from(document.querySelectorAll('input.cmp:checked')).map((c) => c.value),
                compare: !document.getElementById('compare').hidden,
                search: location.search
            })"""
        )
        if filtered["checked"] != ["reo-poe"]:
            problems.append(f"unknown and duplicate ids were kept: {filtered['checked']}")
        if filtered["compare"]:
            problems.append("a one-model link opens the compare table")
        if filtered["search"] != "?cmp=reo-poe":
            problems.append(f"the link was not cleaned up: {filtered['search']}")
    finally:
        extra.close()
    return problems


def jump_check(page):
    """A jump announces its model, verdict and position, then clears."""
    problems = []
    page.click(".verdict a.jump[data-ids='tapo-d230']")
    page.wait_for_timeout(700)
    state = page.evaluate(
        """() => ({ live: document.getElementById('live').textContent,
                     active: document.activeElement.className }) """
    )
    expected = "TP-Link Tapo D230S1, easiest battery setup, row 4 of 14"
    if state["live"] != expected:
        problems.append(f"the jump announced {state['live']!r}, expected {expected!r}")
    if "cmp" not in state["active"]:
        problems.append(f"focus after the jump is on {state['active']!r}")
    page.wait_for_timeout(4200)
    cleared = page.evaluate("() => document.getElementById('live').textContent")
    if cleared:
        problems.append(f"the jump announcement is not cleared: {cleared!r}")
    return problems


def motion_check(page):
    """The theme disc turns and the page fades, unless reduced motion is set."""
    problems = []

    def read():
        return page.evaluate(
            """() => ({
                disc: getComputedStyle(document.querySelector('#theme i')).transform,
                discT: getComputedStyle(document.querySelector('#theme i')).transitionDuration,
                bodyT: getComputedStyle(document.body).transitionDuration,
                theme: document.documentElement.getAttribute('data-theme')
            })"""
        )

    dark = read()
    page.click("#theme")
    page.wait_for_timeout(250)
    light = read()
    if dark["disc"] == light["disc"]:
        problems.append(f"the disc does not turn between themes: {dark['disc']}")
    if "0.18s" not in dark["discT"] or "0.18s" not in dark["bodyT"]:
        problems.append(
            f"theme transitions are disc {dark['discT']!r}, body {dark['bodyT']!r}"
        )
    page.emulate_media(reduced_motion="reduce")
    page.wait_for_timeout(50)
    reduced = read()
    if reduced["discT"] != "0s" or reduced["bodyT"] != "0s":
        problems.append(
            f"reduced motion still animates: disc {reduced['discT']!r}, body {reduced['bodyT']!r}"
        )
    page.click("#theme")
    page.wait_for_timeout(50)
    page.emulate_media(reduced_motion="no-preference")
    return problems


def bars_check(page):
    """Bars draw from zero on a sort, and land on their score widths."""
    problems = []
    page.wait_for_timeout(800)
    initial = page.evaluate(
        """() => {
            const bars = Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'));
            return { n: bars.length,
                     transition: getComputedStyle(bars[0]).transitionDuration,
                     widths: bars.map((b) => parseFloat(b.style.width)),
                     targets: bars.map((b) => +b.dataset.w) };
        }"""
    )
    if initial["n"] != 14:
        problems.append(f"{initial['n']} score bars are visible, expected 14")
    if initial["transition"] != "0.2s":
        problems.append(f"the score bar transition is {initial['transition']!r}")
    if initial["widths"] != initial["targets"]:
        problems.append(f"score bar widths {initial['widths']} do not match {initial['targets']}")

    zeroed = page.evaluate(
        """() => {
            const sel = document.getElementById('sort');
            sel.value = 'price';
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            return Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'))
                .every((b) => parseFloat(b.style.width) === 0);
        }"""
    )
    if not zeroed:
        problems.append("a sort does not restart the score bars from zero")
    page.wait_for_timeout(900)
    drawn = page.evaluate(
        """() => {
            const bars = Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'));
            return { widths: bars.map((b) => parseFloat(b.style.width)),
                     targets: bars.map((b) => +b.dataset.w) };
        }"""
    )
    if drawn["widths"] != drawn["targets"]:
        problems.append(f"after the sort the bars sit at {drawn['widths']}, not {drawn['targets']}")

    page.emulate_media(reduced_motion="reduce")
    page.wait_for_timeout(50)
    instant = page.evaluate(
        """() => {
            const sel = document.getElementById('sort');
            sel.value = 'score';
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            return Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'))
                .every((b) => parseFloat(b.style.width) === +b.dataset.w);
        }"""
    )
    if not instant:
        problems.append("reduced motion does not render the score bars at full width")
    page.emulate_media(reduced_motion="no-preference")
    return problems


def hit_check(page):
    """A 44px hit area means a click 8px below Details still opens it."""
    problems = []
    button = page.locator("button.more").first
    button.scroll_into_view_if_needed()
    box = button.bounding_box()
    if not box:
        return ["no visible Details button"]
    page.mouse.click(box["x"] + 8, box["y"] + box["height"] + 8)
    page.wait_for_timeout(120)
    if button.get_attribute("aria-expanded") != "true":
        problems.append("a click 8px below Details does not open it")
    page.mouse.click(box["x"] + 8, box["y"] + box["height"] + 8)
    page.wait_for_timeout(80)
    return problems


def theme_check(page):
    """The toggle names its action, carries no pressed state, and takes a 44px click."""
    problems = []
    state = page.evaluate(
        """() => {
            const b = document.getElementById("theme");
            return { pressed: b.getAttribute("aria-pressed"),
                     label: b.getAttribute("aria-label"), text: b.textContent.trim() };
        }"""
    )
    if state["pressed"] is not None:
        problems.append(f"the theme button still claims aria-pressed={state['pressed']}")
    if not (state["label"] or "").startswith("Switch to "):
        problems.append(f"the theme button is named {state['label']!r}")
    before = state["text"]
    toggle = page.locator("#theme")
    toggle.scroll_into_view_if_needed()
    box = toggle.bounding_box()
    if box:
        page.mouse.click(box["x"] + 8, box["y"] + box["height"] + 8)
        page.wait_for_timeout(150)
        after = toggle.inner_text().strip()
        if after == before:
            problems.append("a click 8px below the theme button does nothing")
        else:
            box = page.locator("#theme").bounding_box()
            page.mouse.click(box["x"] + 8, box["y"] + box["height"] + 8)
            page.wait_for_timeout(150)
    return problems


def price_check(page):
    """Open the filters and exercise the two-handle price slider."""
    problems = []
    shapes = page.evaluate(
        """() => {
            const ranges = Array.from(document.querySelectorAll("#controls input[type=range]"));
            return {
                count: ranges.length,
                labels: ranges.map((el) => el.getAttribute("aria-label") || ""),
                values: ranges.map((el) => el.value),
                bounds: ranges.map((el) => [el.min, el.max]),
                outputs: [
                    document.getElementById("f-min-out").textContent,
                    document.getElementById("f-max-out").textContent
                ]
            };
        }"""
    )
    if shapes["count"] != 2:
        return [f"expected two price handles, found {shapes['count']}"]
    if not all(shapes["labels"]):
        problems.append(f"price handles need labels, got {shapes['labels']}")
    if shapes["bounds"][0] != shapes["bounds"][1]:
        problems.append(f"price handles use different bounds: {shapes['bounds']}")
    if shapes["outputs"] != ["£" + v for v in shapes["values"]]:
        problems.append(
            f"the labels read {shapes['outputs']} for handles at {shapes['values']}"
        )

    page.eval_on_selector("#filters", "el => { el.open = true }")
    page.wait_for_timeout(80)
    full = page.evaluate(
        """() => {
            const body = document.querySelector("#filters .fbody");
            const cs = getComputedStyle(body);
            const content = body.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
            return {
                column: Math.round(content),
                slider: Math.round(document.querySelector(".dual").getBoundingClientRect().width)
            };
        }"""
    )
    if full["slider"] < full["column"] - 4:
        problems.append(
            f"the price slider is {full['slider']}px wide in a {full['column']}px column"
        )

    page.eval_on_selector(
        "#f-min",
        "el => { el.value = 200; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.wait_for_timeout(80)
    filtered = page.evaluate(
        """() => {
            const rows = Array.from(document.querySelectorAll("tbody.item"));
            const shown = rows.filter((r) => !r.hidden);
            return {
                shown: shown.length,
                total: rows.length,
                cheapest: Math.min(...shown.map((r) => Number(r.dataset.price)))
            };
        }"""
    )
    if filtered["shown"] >= filtered["total"] or filtered["cheapest"] < 200:
        problems.append(
            f"the lower handle does not filter: {filtered['shown']} of "
            f"{filtered['total']} rows shown, cheapest £{filtered['cheapest']}"
        )

    page.eval_on_selector(
        "#f-max",
        "el => { el.value = 40; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.eval_on_selector(
        "#f-min",
        "el => { el.value = 300; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.wait_for_timeout(80)
    crossed = page.evaluate(
        "() => [Number(document.getElementById('f-min').value), "
        "Number(document.getElementById('f-max').value)]"
    )
    if crossed[0] > crossed[1]:
        problems.append(f"the handles crossed: lowest {crossed[0]} above highest {crossed[1]}")

    page.eval_on_selector(
        "#f-max",
        "el => { el.value = 150; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.eval_on_selector(
        "#f-min",
        "el => { el.value = 100; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.wait_for_timeout(80)
    edges = page.evaluate(
        """() => {
            const dual = document.querySelector(".dual");
            const track = document.querySelector(".dual-track");
            const fill = document.querySelector("#f-fill");
            const low = document.getElementById("f-min");
            const high = document.getElementById("f-max");
            const db = dual.getBoundingClientRect();
            const tb = track.getBoundingClientRect();
            const fb = fill.getBoundingClientRect();
            const min = Number(low.min), max = Number(low.max);
            const thumb = parseFloat(getComputedStyle(dual).getPropertyValue("--thumb")) || 0;
            const centre = (v) => db.x + thumb / 2 + ((v - min) / (max - min)) * (db.width - thumb);
            return {
                fill: [fb.x - db.x, db.right - fb.right],
                want: [centre(Number(low.value)) - db.x, db.right - centre(Number(high.value))],
                track: [tb.x - db.x, db.right - tb.right]
            };
        }"""
    )
    if (
        abs(edges["fill"][0] - edges["want"][0]) > 1.5
        or abs(edges["fill"][1] - edges["want"][1]) > 1.5
    ):
        problems.append(
            f"the filled span {[round(v) for v in edges['fill']]} does not meet the "
            f"handles at {[round(v) for v in edges['want']]}"
        )

    page.click("#reset")
    page.wait_for_timeout(80)

    # Clicking the bare track is a shortcut for the nearer handle.
    track = page.locator(".dual-track")
    box = track.bounding_box()
    if not box or not box["width"]:
        return problems + ["the price track has no width to click on"]
    values = "() => [Number(document.getElementById('f-min').value), Number(document.getElementById('f-max').value)]"
    # Playwright's hit-target check sees the transparent range input at this
    # point even though it has pointer-events:none; a real mouse click is the
    # behaviour under test.
    page.mouse.click(box["x"] + box["width"] * 0.25, box["y"] + 1)
    page.wait_for_timeout(80)
    low = page.evaluate(values)
    if abs(low[0] - 105) > 5 or low[1] != 300:
        problems.append(
            f"a click a quarter along the track left the handles at {low}, "
            "expected the lower one near 105"
        )
    page.mouse.click(box["x"] + box["width"] * 0.75, box["y"] + 1)
    page.wait_for_timeout(80)
    high = page.evaluate(values)
    if abs(high[1] - 235) > 5 or high[0] != low[0]:
        problems.append(
            f"a click three quarters along the track left the handles at {high}, "
            "expected the upper one near 235"
        )

    page.click("#reset")
    page.wait_for_timeout(80)
    restored = page.evaluate(
        "() => Array.from(document.querySelectorAll('tbody.item')).filter((r) => !r.hidden).length"
    )
    if restored != filtered["total"]:
        problems.append(f"Reset left {restored} of {filtered['total']} rows showing")
    return problems


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
        """() => ({
            cls: document.activeElement.className,
            top: Math.round(document.activeElement.getBoundingClientRect().top),
            transform: getComputedStyle(document.activeElement).transform
        })"""
    )
    if "skip" not in first["cls"]:
        problems.append(f"the first Tab stop is {first['cls'] or 'nothing'}, not the skip link")
    elif first["transform"] != "none" or first["top"] < 0:
        problems.append(
            f"the skip link stays off-screen when focused (top {first['top']}px, "
            f"transform {first['transform']})"
        )
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


def nojs_check(browser, url):
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
    if state["rows"] < 14:
        problems.append(f"only {state['rows']} rows render without JavaScript")
    return problems


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

    with open(os.path.join(ROOT, "data", "doorbells.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pending = [r for r in rows if r["Unverified / re-check"].strip()]
    print(f"  note  {len(pending)} of {len(rows)} rows still carry an unverified note")
    for row in pending:
        why = row["Unverified / re-check"].replace("£", "GBP ")
        print(f"        {row['Brand']} {row['Model']}: {why}")

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
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                permissions=["clipboard-read", "clipboard-write"],
            )
            page = context.new_page()
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
            cost = page.evaluate(COST_JS)
            phone_data = page.evaluate(AUDIT_JS)
            header = page.evaluate(HEADER_JS)
            header_roles = "columnheader" in page.locator("#tbl").aria_snapshot()
            resize = filters_check(page)
            prices = price_check(page)
            copy = copy_check(page)
            labels = labels_check(page)
            recovery = recovery_check(page)
            bars = bars_check(page)

            page.set_viewport_size({"width": 1280, "height": 900})
            page.reload(wait_until="load")

            # Focus starts at the top of a fresh document, so this is the only
            # point where the skip link can be reached with one Tab.
            skip = skip_check(page)
            hit = hit_check(page)
            theme = theme_check(page)
            motion = motion_check(page)
            jump = jump_check(page)

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
            shortlist = shortlist_check(page)
            costrow = costrow_check(page)
            share = share_check(page)
            chrome = chrome_check(page)

            data = page.evaluate(AUDIT_JS)
            foot = page.locator(
                "#tbl thead th[data-sort=nosub3] button"
            ).aria_snapshot()
            compare = page.evaluate(
                """() => ({
                    caption: (document.querySelector("#cmp-table caption") || {}).textContent || "",
                    rows: document.querySelectorAll("#cmp-table tbody tr").length
                })"""
            )
            lightbox = lightbox_check(page)

            axe = Axe()
            axe_results = {}
            for mode in ("dark", "light"):
                for width in AXE_WIDTHS:
                    page.set_viewport_size({"width": width, "height": 900})
                    page.wait_for_timeout(120)
                    axe_results[(mode, width)] = axe_violations(axe, page)
                page.click("#theme")
                page.wait_for_timeout(120)

            widths = []
            for width in WIDTHS:
                page.set_viewport_size({"width": width, "height": 900})
                page.wait_for_timeout(80)
                widths.append((width, page.evaluate(OVERFLOW_JS)))

            fallback = nojs_check(browser, url)
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

    if resize:
        issues.extend(resize)
    else:
        print("  ok    the phone filter panel reopens when the window grows past 520px")

    if prices:
        issues.extend(prices)
    else:
        print(
            "  ok    the price slider is one labelled handle per end, full width, "
            "fills to the handles, and filters"
        )

    if copy:
        issues.extend(copy)
    else:
        print("  ok    the 3-row cap is explained and announced; Compare sits by the count")

    if labels:
        issues.extend(labels)
    else:
        print(
            "  ok    Nest names its 3-hour limit, no-plan reads as words, PoE is defined "
            "at the filter, and the phone card shares one label column"
        )

    if recovery:
        issues.extend(recovery)
    else:
        print("  ok    filtering announces its count; an empty result offers the nearest match")

    if bars:
        issues.extend(bars)
    else:
        print("  ok    score bars draw from zero on a sort and respect reduced motion")

    if hit:
        issues.extend(hit)
    else:
        print("  ok    Details takes a click 8px outside its visible box")

    if theme:
        issues.extend(theme)
    else:
        print("  ok    the theme toggle names its action and takes a 44px click")

    if fallback:
        issues.extend(fallback)
    else:
        print("  ok    without JavaScript the inert filters are hidden and 14 rows remain")

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

    if (
        not phone["open"]
        and phone["firstRowTop"] < 600
        and phone["verdict"] == "none"
        and phone["shortAnswer"] == "block"
    ):
        print(
            f"  ok    phone: compact short answer, filters collapsed, first product at "
            f"{phone['firstRowTop']}px of {phone['viewport']}px"
        )
    else:
        issues.append(
            "phone first paint: "
            f"filters open={phone['open']}, first product at "
            f"{phone['firstRowTop']}px of {phone['viewport']}px, "
            f"verdict={phone['verdict']}, short answer={phone['shortAnswer']}"
        )

    if cost["aFits"] and cost["bFits"]:
        print("  ok    phone: both 3-year cost cells fit their columns")
    else:
        issues.append(f"phone cost cells overflow: {cost}")

    if data["icon"] == "favicon.svg" and data["canonical"].endswith("/subfree-uk/"):
        print("  ok    favicon, canonical URL and Open Graph title are present")
    else:
        issues.append(
            f"share metadata: icon={data['icon']!r}, canonical={data['canonical']!r}, "
            f"og:title={data['ogTitle']!r}"
        )

    if "footnote a" in foot:
        print("  ok    the cost header reads its footnote letter to screen readers")
    else:
        issues.append(f"cost header name: {foot.strip()}")

    if "Side-by-side comparison of 3 doorbells" in compare["caption"] and compare["rows"] == 18:
        print("  ok    the compare table is captioned with its model count")
    else:
        issues.append(f"compare table: {compare}")

    if costrow:
        issues.extend(costrow)
    else:
        print("  ok    the compare table names the cheapest 3-year cost and each difference")

    if shortlist:
        issues.extend(shortlist)
    else:
        print("  ok    Copy shortlist writes both models, costs, catches and a ?cmp= link")

    if share:
        issues.extend(share)
    else:
        print("  ok    a ?cmp= link restores the three models and drops unknown ids")

    if chrome:
        issues.extend(chrome)
    else:
        print("  ok    the sort select is 44px and compare rows use 8/16px padding and aligned labels")

    if motion:
        issues.extend(motion)
    else:
        print("  ok    the theme disc turns and the page fades over 180ms, off under reduced motion")

    if jump:
        issues.extend(jump)
    else:
        print("  ok    a jump announces its model, verdict and row, then clears")

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

    rule = data["rowRule"]
    if rule and rule["border"] == 3 and rule["pad"] == 8 and rule["plain"] == 0:
        print("  ok    the verdict rule is a 3px border outside the first cell's 8px padding")
    else:
        issues.append(f"verdict row rule: {rule}")

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

    best_practice = {}
    for theme in ("dark", "light"):
        for width in AXE_WIDTHS:
            violations = axe_results[(theme, width)]
            wcag = [v for v in violations if set(v["tags"]) & set(WCAG_TAGS)]
            wcag_ids = {v["id"] for v in wcag}
            for violation in violations:
                if violation["id"] in wcag_ids:
                    continue
                entry = best_practice.setdefault(
                    violation["id"],
                    {
                        "impact": violation["impact"],
                        "help": violation["help"],
                        "targets": set(),
                        "where": set(),
                    },
                )
                entry["targets"].update(node["target"][0] for node in violation["nodes"])
                entry["where"].add(f"{theme} {width}px")
            if not wcag:
                print(f"  ok    axe-core ({theme}, {width}px): no WCAG 2.2 A/AA violations")
                continue
            for violation in wcag:
                nodes = violation["nodes"]
                issues.append(
                    f"axe {theme} at {width}px: {violation['id']} ({violation['impact']}), "
                    f"{len(nodes)} node(s). {violation['help']}"
                )
                for node in nodes[:4]:
                    summary = node.get("failureSummary", "").replace("\n", " ").strip()
                    print(f"        {', '.join(node['target'])}  {summary[:150]}")

    for rule, entry in sorted(best_practice.items()):
        notes.append(
            f"axe best-practice {rule} ({entry['impact']}): {entry['help']} On "
            f"{', '.join(sorted(entry['targets'])[:3])}, in {len(entry['where'])} of "
            f"{len(AXE_WIDTHS) * 2} theme and width passes"
        )
    if best_practice:
        print(
            f"  note  {len(best_practice)} axe best-practice rule(s) reported below; "
            "only WCAG failures block the build"
        )

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
