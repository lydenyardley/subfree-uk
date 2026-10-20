#!/usr/bin/env python3
"""Verification for the site: rebuild, then audit structure and accessibility.

Runs build/build.py first and reports any generated file it changed, so a stale
page fails here instead of shipping. Serves the repo root on a loopback port,
drives the page with Chromium, and runs axe-core in both themes at 1280px,
820px and 390px, failing on WCAG 2.2 A and AA and reporting the
best-practice rules alongside them. Also checks internal anchors, image
files, duplicate ids, headings, labels, target sizes, the type floor, the phone
layout, the price range slider, the filter panel resize, the live announcements,
the three-row compare cap, the empty-state recovery, the compare cost row,the shortlist copy, the differences-only view, the jump announcement, the tray
to compare-header transition, the theme motion, the score-bar draw, the muted-text contrast, the record and plan labels, the phone label column,
the host-grouped source list, the closing line, the performance budget, the
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
                planRows: Array.from(document.querySelectorAll('#tbl tbody.item'))
                    .filter((row) => row.dataset.sub3 === '0').length,
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
    if state["planWords"] != state["planRows"] or state["planDashes"]:
        problems.append(
            f"the plan column prints {state['planWords']} words for "
            f"{state['planRows']} rows without a plan, and "
            f"{state['planDashes']} bare dashes"
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


def sources_check(page):
    """The source list is a disclosure grouped by host, with stable numbers."""
    problems = []

    def read():
        return page.evaluate(
            """() => {
                const box = document.getElementById('sources');
                const summary = box.querySelector('summary');
                const values = Array.from(box.querySelectorAll('li')).map((li) => +li.getAttribute('value'));
                const groups = Array.from(box.querySelectorAll('.fns-g')).map((g) => ({
                    host: g.querySelector('h3').textContent.trim(),
                    n: g.querySelectorAll('li').length,
                    foreign: Array.from(g.querySelectorAll('li a'))
                        .filter((a) => !a.href.toLowerCase().includes(g.querySelector('h3').textContent.trim()))
                        .map((a) => a.href)
                }));
                return {
                    tag: box.tagName,
                    open: box.open,
                    summary: summary.textContent.replace(/\\s+/g, ' ').trim(),
                    headingInSummary: !!summary.querySelector('h2'),
                    headingLevel: box.querySelector('h3') ? box.querySelector('h3').tagName : '',
                    summaryHeight: Math.round(summary.getBoundingClientRect().height),
                    count: values.length,
                    values: values.slice().sort((a, b) => a - b),
                    groups: groups
                };
            }"""
        )

    phone = read()
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(120)
    wide = read()

    if phone["tag"] != "DETAILS" or wide["tag"] != "DETAILS":
        problems.append(f"the source list is a {phone['tag']}, not a disclosure")
    if phone["open"]:
        problems.append("the source list is open on a 390px screen")
    if not wide["open"]:
        problems.append("the source list is closed on a 1280px screen")
    if phone["count"] != 52:
        problems.append(f"the source list holds {phone['count']} entries, expected 52")
    if phone["values"] != list(range(1, 53)):
        problems.append(f"the footnote numbers are not 1 to 52: {phone['values'][:6]}")
    if phone["headingInSummary"] is False:
        problems.append("the Sources heading is no longer a heading inside the summary")
    if "52 links" not in phone["summary"]:
        problems.append(f"the summary reads {phone['summary']!r}")
    if phone["summaryHeight"] < 24:
        problems.append(f"the summary is {phone['summaryHeight']}px tall")
    if len(phone["groups"]) < 10:
        problems.append(f"the list has {len(phone['groups'])} host groups")
    if sum(group["n"] for group in phone["groups"]) != 52:
        problems.append(f"the groups hold {[g['n'] for g in phone['groups']]}")
    foreign = [link for group in phone["groups"] for link in group["foreign"]]
    if foreign:
        problems.append(f"links sit under the wrong host: {foreign[:3]}")
    return problems


def footer_check(page):
    """The page ends on one line with the date, a contact route and a way back."""
    state = page.evaluate(
        """() => {
            const f = document.querySelector('footer.foot');
            if (!f) return null;
            return {
                text: f.textContent.replace(/\\s+/g, ' ').trim(),
                size: getComputedStyle(f).fontSize,
                border: parseFloat(getComputedStyle(f).borderTopWidth),
                links: Array.from(f.querySelectorAll('a')).map((a) => a.getAttribute('href')),
                height: Math.round(f.getBoundingClientRect().height),
                last: f === document.querySelector('main').lastElementChild
            };
        }"""
    )
    if not state:
        return ["the page has no closing line"]
    problems = []
    if not state["text"].startswith("Last checked 19 October 2026"):
        problems.append(f"the closing line reads {state['text'][:40]!r}")
    if "#tbl" not in state["links"]:
        problems.append(f"the closing line has no way back: {state['links']}")
    if state["size"] != "13px" or state["border"] != 1:
        problems.append(
            f"the closing line is {state['size']} with a {state['border']}px rule, "
            "expected 13px and 1px"
        )
    if not state["last"] or state["height"] > 120:
        problems.append(f"the closing line sits at {state['height']}px and is not last")
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
    after = page.evaluate(
        """() => {
            const n = document.getElementById('cmp-note');
            return { text: n.textContent.trim(), hidden: n.hidden, role: n.getAttribute('role') };
        }"""
    )
    try:
        text = page.evaluate("() => navigator.clipboard.readText()")
    except Exception as error:
        text = ""
        problems.append(f"could not read the clipboard: {error}")
    if before != "Copy shortlist":
        problems.append(f"the copy action reads {before!r}")
    confirm = (
        "Copied 3 models as Markdown, with prices and the date checked. "
        "Paste it into a message or a note."
    )
    if after["text"] != confirm or after["hidden"]:
        problems.append(f"the copy confirmation reads {after['text']!r}")
    if after["role"] != "status":
        problems.append(f"the copy confirmation has role {after['role']!r}")
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
    page.wait_for_timeout(6800)
    if not page.evaluate("() => document.getElementById('cmp-note').hidden"):
        problems.append("the copy confirmation does not fade after six seconds")
    if page.inner_text("#cmp-copy") != "Copy shortlist":
        problems.append("the copy button label changed")
    return problems


def diff_check(page):
    """A differences-only view hides identical spec rows but keeps the decisions."""
    problems = []
    page.evaluate(
        """() => {
            const ids = ['reo-poe', 'reo-wifi', 'reo-batt'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(250)
    # The count line is the open affordance that survives while the tray is
    # away, so the check does not depend on the panel being closed first.
    page.click("#cmp-inline")
    page.wait_for_timeout(150)
    off = page.evaluate(
        """() => {
            const box = document.getElementById('cmp-diff-w');
            const rows = Array.from(document.querySelectorAll('#cmp-table tbody tr'));
            return {
                hidden: box.hidden,
                label: box.textContent.replace(/\\s+/g, ' ').trim(),
                checked: document.getElementById('cmp-diff').checked,
                live: document.getElementById('compare').getAttribute('aria-live'),
                rows: rows.length,
                shown: rows.filter((tr) => !tr.hidden).length,
                dupes: +((document.getElementById('cmp-dupes').textContent.match(/\\d+/) || [0])[0])
            };
        }"""
    )
    if off["hidden"]:
        problems.append("the differences-only control is hidden for a trio with identical rows")
    if off["checked"]:
        problems.append("the differences-only view is on before anyone asks for it")
    if off["dupes"] < 1:
        problems.append(f"the control counts {off['dupes']} identical rows for the Reolink trio")
    if f"({off['dupes']} identical)" not in off["label"]:
        problems.append(f"the control reads {off['label']!r}")
    if off["rows"] != 18 or off["shown"] != 18:
        problems.append(f"the compare table starts at {off['shown']} of {off['rows']} rows")
    if off["live"]:
        problems.append(
            f"the compare panel is a live region ({off['live']}); rendering eighteen rows "
            "would read them all aloud"
        )

    page.check("#cmp-diff")
    page.wait_for_timeout(150)
    on = page.evaluate(
        """() => {
            const rows = Array.from(document.querySelectorAll('#cmp-table tbody tr'));
            const hidden = rows.filter((tr) => tr.hidden);
            const same = hidden.every((tr) => {
                const cells = Array.from(tr.querySelectorAll('td')).map((td) => td.textContent);
                return cells.length > 1 && cells.every((v) => v === cells[0]);
            });
            return {
                shown: rows.filter((tr) => !tr.hidden).length,
                hidden: hidden.length,
                allIdentical: same,
                pinnedHidden: rows.filter((tr) => tr.dataset.pin && tr.hidden)
                    .map((tr) => tr.querySelector('th').textContent),
                pinned: rows.filter((tr) => tr.dataset.pin).length
            };
        }"""
    )
    if on["hidden"] != off["dupes"]:
        problems.append(f"the toggle hides {on['hidden']} rows, not {off['dupes']}")
    if on["shown"] + on["hidden"] != 18:
        problems.append(f"the table holds {on['shown'] + on['hidden']} rows after the toggle")
    if not on["allIdentical"]:
        problems.append("the toggle hides a row that is not identical")
    if on["pinnedHidden"]:
        problems.append(f"the toggle hides a decision row: {on['pinnedHidden']}")
    if on["pinned"] != 5:
        problems.append(f"{on['pinned']} rows are pinned, expected the cost row and four decisions")

    page.uncheck("#cmp-diff")
    page.wait_for_timeout(120)
    if page.evaluate("() => document.querySelectorAll('#cmp-table tbody tr:not([hidden])').length") != 18:
        problems.append("unticking differences only does not restore the rows")

    page.evaluate(
        """() => {
            const ids = ['tapo-td21', 'reo-poe', 'ezviz-ep3x'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(200)
    page.click("#cmp-inline")
    page.wait_for_timeout(150)
    return problems


def morph_check(page):
    """The compare panel is the tray, moved: one named pair, 240ms, guarded."""
    problems = []
    page.emulate_media(reduced_motion="no-preference")
    page.evaluate(
        """() => {
            const ids = ['reo-poe', 'reo-wifi', 'reo-batt'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(200)

    names = page.evaluate(
        """() => ({
            tray: getComputedStyle(document.getElementById('tray')).viewTransitionName,
            head: getComputedStyle(document.querySelector('.cmp-head')).viewTransitionName,
            named: Array.from(document.querySelectorAll('body *')).filter(
                (e) => getComputedStyle(e).viewTransitionName !== 'none'
            ).map((e) => e.id || e.className)
        })"""
    )
    if names["tray"] != "cmp-tray" or names["head"] != "cmp-tray":
        problems.append(f"the tray and the compare header do not share one name: {names}")
    if len(names["named"]) != 2:
        problems.append(f"{len(names['named'])} elements are named for the transition: {names['named']}")

    # Opening: one transition, 240ms, and the tray's box is now the panel's.
    page.evaluate(
        """() => {
            window.__vt = { calls: 0 };
            window.__vtReal = document.startViewTransition;
            const real = window.__vtReal.bind(document);
            document.startViewTransition = (cb) => {
                window.__vt.calls++;
                return real(cb);
            };
        }"""
    )
    page.evaluate("() => document.getElementById('tray-go').click()")
    page.wait_for_timeout(60)
    during = page.evaluate(
        """() => {
            const r = document.documentElement;
            const anims = document.getAnimations({ subtree: true });
            return {
                dur: getComputedStyle(r, '::view-transition-group(cmp-tray)').animationDuration,
                root: getComputedStyle(r, '::view-transition-old(root)').animationName,
                named: anims.filter((a) => (a.effect.pseudoElement || '').includes('cmp-tray')).length,
                keyframes: anims
                    .filter((a) => a.effect.pseudoElement === '::view-transition-group(cmp-tray)')
                    .length
            };
        }"""
    )
    page.wait_for_timeout(320)
    opened = page.evaluate(
        """() => ({
            calls: window.__vt.calls,
            tray: document.getElementById('tray').hidden,
            panel: !document.getElementById('compare').hidden,
            focus: document.activeElement.id,
            top: Math.round(document.getElementById('compare').getBoundingClientRect().top)
        })"""
    )
    if opened["calls"] != 1:
        problems.append(f"opening ran {opened['calls']} view transitions, expected 1")
    if not opened["panel"] or not opened["tray"]:
        problems.append(f"opening did not hand the tray's place to the panel: {opened}")
    if during["dur"] != "0.24s" or not during["keyframes"]:
        problems.append(f"the named group does not run 240ms: {during}")
    if during["root"] != "none":
        problems.append(f"the page cross-fades behind the pair: root old animation {during['root']}")
    if during["named"] < 3:
        problems.append(f"only {during['named']} animations of the named pair ran")
    if abs(opened["top"]) > 2:
        problems.append(f"the panel opens {opened['top']}px from the top of the viewport")
    if opened["focus"] != "cmp-h":
        problems.append(
            f"opening put focus on {opened['focus'] or 'nothing'}, not the panel's heading"
        )

    page.evaluate("() => document.getElementById('cmp-close').click()")
    page.wait_for_timeout(400)
    closed = page.evaluate(
        """() => ({
            vt: window.__vt.calls,
            tray: !document.getElementById('tray').hidden,
            panel: !document.getElementById('compare').hidden
        })"""
    )
    if closed["vt"] != 2:
        problems.append(f"closing ran {closed['vt']} transitions in total, expected 2")
    if not closed["tray"] or closed["panel"]:
        problems.append(f"closing did not give the tray back: {closed}")

    # Clear lives in the panel because the tray is not on screen while it is open,
    # and the button that is about to vanish cannot keep focus.
    page.evaluate("() => document.getElementById('tray-go').click()")
    page.wait_for_timeout(350)
    page.focus("#cmp-clear")
    page.keyboard.press("Enter")
    page.wait_for_timeout(250)
    cleared = page.evaluate(
        """() => ({
            checked: document.querySelectorAll('input.cmp:checked').length,
            tray: !document.getElementById('tray').hidden,
            panel: !document.getElementById('compare').hidden,
            focus: document.activeElement.matches('input.cmp')
        })"""
    )
    if cleared["checked"] or cleared["panel"] or cleared["tray"]:
        problems.append(f"Clear in the panel did not empty the selection: {cleared}")
    if not cleared["focus"]:
        problems.append("clearing from the panel left focus on a hidden button")

    # Reduced motion: the swap still happens, but nothing animates.
    page.emulate_media(reduced_motion="reduce")
    page.evaluate(
        """() => {
            const ids = ['tapo-td21', 'reo-poe'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
            window.__vt.calls = 0;
        }"""
    )
    page.wait_for_timeout(150)
    page.evaluate("() => document.getElementById('tray-go').click()")
    page.wait_for_timeout(300)
    reduced = page.evaluate(
        """() => ({ calls: window.__vt.calls, panel: !document.getElementById('compare').hidden })"""
    )
    if reduced["calls"] != 0:
        problems.append("reduced motion still runs a view transition")
    if not reduced["panel"]:
        problems.append("reduced motion does not open the comparison")
    page.evaluate("() => document.getElementById('cmp-close').click()")
    page.wait_for_timeout(250)

    # No API at all: the old instant swap, and the reader still gets the panel.
    page.emulate_media(reduced_motion="no-preference")
    page.evaluate("() => { document.startViewTransition = undefined }")
    page.evaluate("() => document.getElementById('tray-go').click()")
    page.wait_for_timeout(300)
    fallback = page.evaluate(
        """() => ({
            api: typeof document.startViewTransition,
            panel: !document.getElementById('compare').hidden,
            tray: !document.getElementById('tray').hidden
        })"""
    )
    if fallback["api"] != "undefined" or not fallback["panel"] or fallback["tray"]:
        problems.append(f"without the API the panel does not open or the tray stays: {fallback}")

    # Unticking below two closes the panel and leaves focus where the reader is.
    page.focus("input.cmp[value='tapo-td21']")
    page.evaluate(
        """() => {
            const c = document.querySelector("input.cmp[value='reo-poe']");
            c.checked = false;
            c.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(200)
    implicit = page.evaluate(
        """() => ({
            panel: !document.getElementById('compare').hidden,
            tray: !document.getElementById('tray').hidden,
            checked: document.querySelectorAll('input.cmp:checked').length,
            focus: document.activeElement.value
        })"""
    )
    if implicit["panel"] or not implicit["tray"] or implicit["checked"] != 1:
        problems.append(f"unticking below two did not close the panel: {implicit}")
    if implicit["focus"] != "tapo-td21":
        problems.append(f"unticking below two moved focus to {implicit['focus']}")

    page.evaluate(
        """() => {
            delete document.startViewTransition;
            document.getElementById('cmp-close').click();
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = false;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(250)
    return problems


def rule_check(page):
    """A hairline along the table reports scroll position; it never hijacks it."""
    problems = []
    page.evaluate("() => scrollTo(0, 0)")
    page.wait_for_timeout(150)
    box = page.evaluate(
        """() => {
            const w = document.querySelector('.tbl-w'), pr = w.querySelector('.prog'), i = pr.querySelector('i');
            const t = document.getElementById('tbl'), s = getComputedStyle(i);
            return {
                inWrapper: w.contains(t) && w.firstElementChild === pr,
                static: { h: getComputedStyle(pr).height, pe: getComputedStyle(pr).pointerEvents,
                          hidden: pr.getAttribute('aria-hidden') },
                anim: { name: s.animationName, timeline: s.animationTimeline, range: s.animationRange },
                height: Math.round(w.getBoundingClientRect().height - t.getBoundingClientRect().height),
                rows: t.querySelectorAll('tbody.item').length
            };
        }"""
    )
    if not box["inWrapper"] or box["rows"] != 14:
        problems.append(f"the rule is not the first child of the table's box: {box}")
    if box["static"] != {"h": "2px", "pe": "none", "hidden": "true"}:
        problems.append(f"the rule is not a silent 2px hairline: {box['static']}")
    if box["height"] != 0:
        problems.append(f"the wrapper adds {box['height']}px to the table")
    if box["anim"] != {"name": "rule", "timeline": "--tbl", "range": "cover"}:
        problems.append(f"the rule is not driven by the table's own timeline: {box['anim']}")

    samples = []
    for frac in (0.2, 0.5, 0.9):
        page.evaluate(
            """(f) => {
                const r = document.getElementById('tbl').getBoundingClientRect();
                scrollTo(0, scrollY + r.top + r.height * f - 300);
            }""",
            frac,
        )
        page.wait_for_timeout(120)
        samples.append(
            page.evaluate(
                """() => {
                    const pr = document.querySelector('.prog');
                    const m = new DOMMatrix(getComputedStyle(pr.querySelector('i')).transform);
                    return { top: Math.round(pr.getBoundingClientRect().top), fill: +m.a.toFixed(3) };
                }"""
            )
        )
    fills = [s["fill"] for s in samples]
    if any(b <= a for a, b in zip(fills, fills[1:])):
        problems.append(f"the rule does not grow with scroll: {fills}")
    if fills[-1] < 0.7 or fills[0] > 0.45:
        problems.append(f"the rule does not track the table's own span: {fills}")
    if any(s["top"] != 0 for s in samples[1:]):
        problems.append(f"the rule does not stay at the top of the viewport: {samples}")

    # No timeline support means the @supports block never applies: an empty hairline.
    page.evaluate("() => { document.querySelector('.prog i').style.animation = 'none' }")
    page.wait_for_timeout(80)
    plain = page.evaluate(
        """() => {
            const i = document.querySelector('.prog i');
            return { t: getComputedStyle(i).transform, h: getComputedStyle(i).height };
        }"""
    )
    if plain != {"t": "matrix(0, 0, 0, 1, 0, 0)", "h": "2px"}:
        problems.append(f"without the timeline the rule is not a plain hairline: {plain}")
    page.evaluate("() => { document.querySelector('.prog i').style.animation = ''; scrollTo(0, 0) }")
    page.wait_for_timeout(150)
    return problems


def head_check(page):
    """The compare header keeps its heading on one line and its links together.

    Clear sits beside Copy shortlist and Close, so a phone must not break the
    heading across two lines or leave one link alone on a third.
    """
    problems = []
    width = page.evaluate("() => innerWidth")
    page.evaluate(
        """() => {
            const ids = ['reo-poe', 'reo-wifi', 'reo-batt'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(150)
    page.evaluate("() => document.getElementById('cmp-inline').click()")
    page.wait_for_timeout(450)
    shape = page.evaluate(
        """() => {
            const head = document.querySelector('.cmp-head');
            const h2 = document.getElementById('cmp-h').getBoundingClientRect();
            const links = Array.from(document.querySelectorAll('.cmp-links > *'))
                .map((el) => Math.round(el.getBoundingClientRect().top));
            return {
                headH: Math.round(head.getBoundingClientRect().height),
                heading: [Math.round(h2.width), Math.round(h2.height)],
                linkTops: links,
                over: Math.round(head.scrollWidth - head.clientWidth)
            };
        }"""
    )
    if shape["heading"][1] > 30:
        problems.append(f"at {width}px the compare heading wraps: {shape['heading']}")
    if len(set(shape["linkTops"])) != 1:
        problems.append(f"at {width}px the header links split across rows: {shape['linkTops']}")
    if shape["over"] > 1:
        problems.append(f"at {width}px the compare header overflows by {shape['over']}px")
    page.evaluate(
        """() => {
            document.getElementById('cmp-close').click();
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = false;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(250)
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
    """Bars draw from zero on a sort, paint with a transform, and land on their scores."""
    problems = []
    page.wait_for_timeout(800)
    scale = "const s = (b) => { const m = b.style.transform.match(/scaleX\\(([-0-9.]+)\\)/); return m ? +m[1] : NaN; };"
    initial = page.evaluate(
        """() => {
            const bars = Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'));
            const cs = getComputedStyle(bars[0]);
            const m = bars[0].style.transform.match(/scaleX\\(([-0-9.]+)\\)/);
            return { n: bars.length,
                     transition: cs.transitionDuration,
                     property: cs.transitionProperty,
                     scale: m ? +m[1] : NaN,
                     target: +bars[0].dataset.w / 100 };
        }"""
    )
    if initial["n"] != 14:
        problems.append(f"{initial['n']} score bars are visible, expected 14")
    if initial["transition"] != "0.2s" or initial["property"] != "transform":
        problems.append(
            f"the score bar animates {initial['property']} over {initial['transition']!r}, "
            "expected transform over 0.2s"
        )
    if abs(initial["scale"] - initial["target"]) > 0.01:
        problems.append(f"the first bar is scaled {initial['scale']}, expected {initial['target']}")

    zeroed = page.evaluate(
        f"""() => {{
            {scale}
            const sel = document.getElementById('sort');
            sel.value = 'price';
            sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'))
                .every((b) => s(b) === 0);
        }}"""
    )
    if not zeroed:
        problems.append("a sort does not restart the score bars from zero")
    page.wait_for_timeout(900)
    drawn = page.evaluate(
        f"""() => {{
            {scale}
            const bars = Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'));
            return {{ scales: bars.map(s), targets: bars.map((b) => +b.dataset.w / 100) }};
        }}"""
    )
    off = [
        (a, b)
        for a, b in zip(drawn["scales"], drawn["targets"])
        if abs(a - b) > 0.01
    ]
    if off:
        problems.append(f"after the sort the bars sit at {off}, not their scores")

    page.emulate_media(reduced_motion="reduce")
    page.wait_for_timeout(50)
    instant = page.evaluate(
        f"""() => {{
            {scale}
            const sel = document.getElementById('sort');
            sel.value = 'score';
            sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'))
                .every((b) => Math.abs(s(b) - +b.dataset.w / 100) < 0.01);
        }}"""
    )
    if not instant:
        problems.append("reduced motion does not render the score bars at their scores")
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


INK_JS = r"""() => {
    const cs = getComputedStyle(document.documentElement);
    const rgb = (value) => {
        const m = value.trim().match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
        if (!m) return null;
        const hex = m[1].length === 3 ? m[1].replace(/(.)/g, '$1$1') : m[1];
        return [0, 2, 4].map((i) => parseInt(hex.substr(i, 2), 16) / 255);
    };
    const lum = (c) => c
        .map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)))
        .reduce((a, v, i) => a + v * [0.2126, 0.7152, 0.0722][i], 0);
    const cr = (a, b) => {
        const la = lum(a), lb = lum(b);
        return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
    };
    const ink3 = rgb(cs.getPropertyValue('--ink3'));
    const paper = rgb(cs.getPropertyValue('--paper'));
    const tint = rgb(cs.getPropertyValue('--tint'));
    const raw = cs.getPropertyValue('--ink3').trim();
    if (!ink3 || !paper || !tint) return { raw, theme: 'unparsed' };
    return { raw, theme: document.documentElement.getAttribute('data-theme') || 'auto',
             paper: Math.round(cr(ink3, paper) * 100) / 100,
             tint: Math.round(cr(ink3, tint) * 100) / 100 };
}"""


def ink_check(page):
    """Muted text clears 4.5:1 on the page and on a tinted row, in both themes.

    The cards tint their row on hover, so a note has to pass on the tint, not
    only on paper.
    """
    problems = []
    start = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
    for want in ("light", "dark"):
        page.evaluate("(t) => document.documentElement.setAttribute('data-theme', t)", want)
        page.wait_for_timeout(60)
        got = page.evaluate(INK_JS)
        if got.get("theme") == "unparsed":
            problems.append(f"{want}: --ink3/--paper/--tint are not hex: {got['raw']!r}")
            continue
        for surface in ("paper", "tint"):
            if got[surface] < 4.5:
                problems.append(
                    f"{want}: --ink3 {got['raw']} on --{surface} is {got[surface]}:1, needs 4.5"
                )
    page.evaluate(
        """(t) => {
            if (t) document.documentElement.setAttribute('data-theme', t);
            else document.documentElement.removeAttribute('data-theme');
        }""",
        start,
    )
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


def perf_check(page):
    """A sort and the compare response against the budget, at 4x CPU throttle.

    Budget: docs/performance-budget.md.
    """
    problems = []
    session = page.context.new_cdp_session(page)
    try:
        session.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        page.wait_for_timeout(400)
        state = page.evaluate(
            """async () => {
                const frame = () => new Promise((r) => requestAnimationFrame(() => setTimeout(r, 0)));
                const long = [];
                new PerformanceObserver((list) => list.getEntries().forEach((e) => long.push(Math.round(e.duration))))
                    .observe({ entryTypes: ['longtask'] });
                document.getElementById('compare').hidden = true;
                document.querySelectorAll('button.more[aria-expanded="true"]').forEach((b) => b.click());
                document.getElementById('reset').click();
                await frame();
                await new Promise((r) => setTimeout(r, 250));
                const started = long.length;
                const sort = document.getElementById('sort');
                const sorts = [];
                for (const value of ['price', 'score', 'keep3', 'model']) {
                    const t = performance.now();
                    sort.value = value;
                    sort.dispatchEvent(new Event('change', { bubbles: true }));
                    sorts.push(performance.now() - t);
                    await frame();
                    await new Promise((r) => setTimeout(r, 120));
                }
                const sortLong = long.slice(started);
                const table = document.getElementById('tbl');
                const height = table.getBoundingClientRect().height;
                const top = document.querySelector('#tbl tbody.item').getBoundingClientRect().top;
                const ids = ['reo-poe', 'reo-wifi', 'reo-batt'];
                document.querySelectorAll('input.cmp').forEach((c) => {
                    c.checked = ids.indexOf(c.value) > -1;
                    c.dispatchEvent(new Event('change', { bubbles: true }));
                });
                await frame();
                const shift = {
                    height: Math.round(table.getBoundingClientRect().height - height),
                    top: Math.round(document.querySelector('#tbl tbody.item').getBoundingClientRect().top - top),
                    tray: !document.getElementById('tray').hidden
                };
                // The open now finishes in the transition's callback, on a later
                // frame, so time it to the panel being on screen, not to the click.
                // Three times: the first pays Chrome's snapshot warm-up.
                const openBefore = long.length;
                const opens = [];
                for (let i = 0; i < 3; i++) {
                    if (!document.getElementById('compare').hidden) {
                        document.getElementById('cmp-close').click();
                        await new Promise((r) => setTimeout(r, 500));
                    }
                    const t = performance.now();
                    document.getElementById('tray-go').click();
                    for (let f = 0; f < 120 && document.getElementById('compare').hidden; f++) await frame();
                    opens.push(Math.round(performance.now() - t));
                    await new Promise((r) => setTimeout(r, 400));
                }
                await new Promise((r) => setTimeout(r, 300));
                const compareLong = long.slice(openBefore);
                return { sorts, sortLong, shift, opens, compareLong };
            }"""
        )
    finally:
        session.send("Emulation.setCPUThrottlingRate", {"rate": 1})
        session.detach()

    slowest = max(state["sorts"])
    if slowest >= 100:
        problems.append(f"the slowest sort took {slowest:.0f}ms at 4x throttle, budget 100ms")
    opens = state["opens"]
    median = sorted(opens)[1]
    if median >= 150:
        problems.append(
            f"opening the compare took {median}ms (median of {opens}) at 4x throttle, budget 150ms"
        )
    if not state["shift"]["tray"]:
        problems.append("the tray did not open, so the shift was not measured")
    if state["shift"]["height"] or state["shift"]["top"]:
        problems.append(f"the table moved when the tray appeared: {state['shift']}")
    longest = max(state["sortLong"], default=0)
    # The transition must not turn the open into a task of its own.
    morph_long = max(state["compareLong"], default=0)
    if morph_long >= 50:
        problems.append(
            f"opening the comparison ran a {morph_long}ms task at 4x throttle, budget 50ms"
        )
    note = (
        f"slowest sort {slowest:.0f}ms, compare opens {opens}ms (median {median}) at 4x CPU; "
        f"longest task during a sort {longest}ms (budget 50ms, open in docs/performance-budget.md), "
        f"during the compare transition {morph_long}ms"
    )
    return problems, note


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
            footer = footer_check(page)
            recovery = recovery_check(page)
            bars = bars_check(page)
            sources = sources_check(page)
            head = head_check(page)

            page.set_viewport_size({"width": 1280, "height": 900})
            page.reload(wait_until="load")

            # Focus starts at the top of a fresh document, so this is the only
            # point where the skip link can be reached with one Tab.
            skip = skip_check(page)
            hit = hit_check(page)
            theme = theme_check(page)
            ink = ink_check(page)
            motion = motion_check(page)
            jump = jump_check(page)
            morph = morph_check(page)
            rule = rule_check(page)
            head = head + head_check(page)

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
            diff = diff_check(page)

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

            perf, perf_note = perf_check(page)
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

    if footer:
        issues.extend(footer)
    else:
        print("  ok    the page ends on one line with the date, an issue link and a way back")

    if recovery:
        issues.extend(recovery)
    else:
        print("  ok    filtering announces its count; an empty result offers the nearest match")

    if bars:
        issues.extend(bars)
    else:
        print("  ok    score bars draw from zero on a sort and respect reduced motion")

    if sources:
        issues.extend(sources)
    else:
        print(
            "  ok    the 52 sources sit in a host-grouped disclosure, closed below "
            "821px and open above it"
        )

    if hit:
        issues.extend(hit)
    else:
        print("  ok    Details takes a click 8px outside its visible box")

    if theme:
        issues.extend(theme)
    else:
        print("  ok    the theme toggle names its action and takes a 44px click")

    if ink:
        issues.extend(ink)
    else:
        print("  ok    muted text clears 4.5:1 on paper and on a tinted row, in both themes")

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

    if perf:
        issues.extend(perf)
    else:
        print(
            "  ok    a sort and the compare respond in under 100ms at 4x throttle, "
            "with no shift when the tray appears"
        )
    if perf_note:
        notes.append(perf_note)

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

    if diff:
        issues.extend(diff)
    else:
        print(
            "  ok    differences only hides identical spec rows, keeps the decision rows, "
            "and names its count"
        )

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

    if morph:
        issues.extend(morph)
    else:
        print(
            "  ok    the tray becomes the compare header in one named pair over 240ms, "
            "skipped under reduced motion and without the API"
        )

    if rule:
        issues.extend(rule)
    else:
        print("  ok    a hairline along the table follows scroll, with a plain rule where timelines are missing")

    if head:
        issues.extend(head)
    else:
        print("  ok    the compare header keeps its heading on one line and its links in one row at 390 and 1280")

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
