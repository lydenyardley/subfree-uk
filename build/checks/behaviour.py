"""What the page does when it is used: the controls, the disclosures, the theme and the page's own text."""
import os

from .context import ROOT
from .js import BARS_JS, DESKTOP_ROWS_JS, FILTERS_JS, STUCK_JS
from .registry import Check


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

    # Three ways out: Escape, the button in the corner, and a tap anywhere off
    # the photo. The bar stays, because the name in it is there to be read.
    page.click(".zoom")
    page.wait_for_timeout(150)
    if not page.evaluate("() => document.getElementById('lightbox').open"):
        problems.append("the lightbox does not reopen for the close checks")
    else:
        page.click("#lb-x")
        page.wait_for_timeout(150)
        if page.evaluate("() => document.getElementById('lightbox').open"):
            problems.append("the close button in the corner does not close the photo")
        page.click(".zoom")
        page.wait_for_timeout(200)
        page.mouse.click(4, 4)
        page.wait_for_timeout(200)
        if page.evaluate("() => document.getElementById('lightbox').open"):
            problems.append("a tap off the photo does not close the lightbox")
        else:
            page.keyboard.press("Escape")
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
    """Three selections explain the cap, announce it, and refuse a fourth."""
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
    # A box that greys out looks broken. The box stays live and the refusal is
    # explained where the reader is looking.
    if state["disabled"]:
        problems.append(f"{state['disabled']} checkboxes are disabled at three selections")
    # A real tap, because the refusal is a reader's rule: a script that sets
    # the selection is not second-guessed. The box is centred first, so the
    # sticky header and the tray cannot stand in the way of the click.
    page.evaluate(
        """() => {
            const fourth = Array.from(document.querySelectorAll('input.cmp'))
                .find((el) => !el.checked);
            fourth.scrollIntoView({ block: 'center' });
        }"""
    )
    page.click("input.cmp:not(:checked)")
    page.wait_for_timeout(300)
    refused = page.evaluate(
        """() => ({
            ticked: Array.from(document.querySelectorAll("input.cmp"))
                .filter((c) => c.checked).length,
            cap: document.getElementById("cmp-cap").textContent.trim(),
            hidden: document.getElementById("cmp-cap").hidden
        })"""
    )
    if refused["ticked"] != 3:
        problems.append(f"{refused['ticked']} boxes are ticked after a fourth was tried")
    if refused["hidden"] or "3" not in refused["cap"]:
        problems.append(f"the refused fourth box says nothing: {refused['cap']!r}")
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
            text: document.getElementById("empty-txt").textContent.trim(),
            near: document.getElementById("near").hidden
                ? null : document.getElementById("near").textContent,
            live: document.getElementById("live").textContent
        })"""
    )
    if not empty["visible"] or not empty["near"]:
        problems.append(f"the empty state offers no nearest match: {empty}")
    elif "£" not in empty["near"]:
        problems.append(f"the nearest-match label has no price: {empty['near']!r}")
    # The message says which filter emptied the list, and the button says what
    # it moves, so one tap is enough to get out of the dead end.
    if "£" not in empty["text"] or "doorbell" not in empty["text"]:
        problems.append(f"the empty state does not name the filter: {empty['text']!r}")
    if empty["near"] and not any(
        word in empty["near"] for word in ("maximum", "minimum", "Show")
    ):
        problems.append(f"the recovery button does not say what it changes: {empty['near']!r}")
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

def labels_check(page, rec_label="Only briefly (3 hrs)"):
    """The record column names a time limit, the plan column names its absence,
    PoE is defined at the filter, and the phone card labels every figure."""
    problems = []
    state = page.evaluate(
        """() => {
            const all = (s) => Array.from(document.querySelectorAll(s));
            const spec = ['.c-rec', '.c-price', '.c-nosub', '.c-sub'];
            const cells = spec.map((cls) => document.querySelector('#tbl tbody.item ' + cls));
            const nest = document.querySelector('#m-nest .c-rec');
            const price = document.querySelector('#tbl tbody.item .c-price');
            const catchCell = document.querySelector('#tbl tbody.item .c-catch');
            const subs = all('#tbl tbody.item .c-sub');
            // The top of the figure itself, not of its cell: a wrapped label
            // pushes the number down inside a cell that still starts level.
            const figureTop = (td) => {
                const first = td.firstChild;
                if (!first) return -1;
                if (first.nodeType === 1) return Math.round(first.getBoundingClientRect().top);
                const range = document.createRange();
                range.selectNodeContents(first);
                return Math.round(range.getBoundingClientRect().top);
            };
            const figures = all('#tbl tbody.item')
                .filter((row) => row.getClientRects().length)
                .map((row) => {
                    const nosub = row.querySelector('.c-nosub'), sub = row.querySelector('.c-sub');
                    return {
                        id: row.id.slice(2),
                        nosub: {x: Math.round(nosub.getBoundingClientRect().x), y: figureTop(nosub)},
                        sub: {x: Math.round(sub.getBoundingClientRect().x), y: figureTop(sub)}
                    };
                });
            const hint = document.querySelector('#filters .hint');
            const power = hint ? hint.closest('fieldset') : null;
            const pseudo = (el) => getComputedStyle(el, '::before');
            return {
                nestText: nest.querySelector('.rec').textContent.trim(),
                nestClass: nest.querySelector('.rec').className,
                planWords: subs.filter((td) => /No plan/.test(td.textContent)).length,
                planRows: Array.from(document.querySelectorAll('#tbl tbody.item'))
                    .filter((row) => row.dataset.sub3 === '0').length,
                planDashes: subs.filter((td) => /\u2014/.test(td.textContent)).length,
                priceLabel: pseudo(price).content,
                catchLabel: pseudo(catchCell).content,
                displays: cells.map((td) => getComputedStyle(td).display),
                labels: cells.map((td) => pseudo(td).content),
                figures: figures,
                hint: hint ? hint.textContent.trim() : '',
                hintPower: !!(power && /Power/.test(power.querySelector('legend').textContent)),
                hintSize: hint ? getComputedStyle(hint).fontSize : '',
                hintVisible: hint ? hint.getClientRects().length > 0 : false
            };
        }"""
    )
    if state["nestText"] != rec_label:
        problems.append(f"the Nest record cell reads {state['nestText']!r}")
    if "rec-brief" not in state["nestClass"]:
        problems.append(f"the Nest record marker has the class {state['nestClass']!r}")
    if state["planWords"] != state["planRows"] or state["planDashes"]:
        problems.append(
            f"the plan column prints {state['planWords']} words for "
            f"{state['planRows']} rows without a plan, and "
            f"{state['planDashes']} bare dashes"
        )
    if "Price" not in state["priceLabel"]:
        problems.append(f"the phone price cell carries the label {state['priceLabel']}")
    if "Main catch" not in state["catchLabel"]:
        problems.append(f"the catch cell lost its label: {state['catchLabel']}")
    if any(display != "block" for display in state["displays"]):
        problems.append(f"the phone spec cells are {state['displays']}, expected block rows")
    for want in ("Records free?", "Price", "3 years, no plan", "3 years, with plan"):
        if not any(want in label for label in state["labels"]):
            problems.append(f"the phone labels read {state['labels']}, missing {want!r}")
    # The two 3-year figures are read against each other, so they sit side by
    # side and their numbers start on the same line in every card, whichever of
    # the two labels wraps.
    if len(state["figures"]) < 10:
        problems.append(f"only {len(state['figures'])} phone cards to measure")
    crooked = [
        f"{fig['id']} {fig['nosub']['y']}/{fig['sub']['y']}px"
        for fig in state["figures"]
        if abs(fig["nosub"]["y"] - fig["sub"]["y"]) > 2
    ]
    if crooked:
        problems.append(f"the two 3-year figures start on different lines: {crooked[:3]}")
    stacked = [fig["id"] for fig in state["figures"] if fig["nosub"]["x"] >= fig["sub"]["x"]]
    if stacked:
        problems.append(f"{len(stacked)} cards stack the two 3-year figures")
    if not state["hint"].startswith("PoE"):
        problems.append(f"the Power filter has no PoE note: {state['hint']!r}")
    if not state["hintPower"]:
        problems.append("the PoE note is not inside the Power fieldset")
    if state["hintSize"] != "12px":
        problems.append(f"the PoE note is {state['hintSize']}, expected 12px")
    return problems

def sources_check(page, source_count):
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
    if phone["count"] != source_count:
        problems.append(f"the source list holds {phone['count']} entries, expected {source_count}")
    if phone["values"] != list(range(1, source_count + 1)):
        problems.append(f"the footnote numbers are not 1 to 52: {phone['values'][:6]}")
    if phone["headingInSummary"] is False:
        problems.append("the Sources heading is no longer a heading inside the summary")
    if f"{source_count} links" not in phone["summary"]:
        problems.append(f"the summary reads {phone['summary']!r}")
    if phone["summaryHeight"] < 24:
        problems.append(f"the summary is {phone['summaryHeight']}px tall")
    if len(phone["groups"]) < 10:
        problems.append(f"the list has {len(phone['groups'])} host groups")
    if sum(group["n"] for group in phone["groups"]) != source_count:
        problems.append(f"the groups hold {[g['n'] for g in phone['groups']]}")
    foreign = [link for group in phone["groups"] for link in group["foreign"]]
    if foreign:
        problems.append(f"links sit under the wrong host: {foreign[:3]}")
    return problems

def footer_check(page, checked=None):
    """The page ends with the date, an owner, a contact route and a way back."""
    state = page.evaluate(
        """() => {
            const f = document.querySelector('footer.foot');
            if (!f) return null;
            return {
                text: f.textContent.replace(/\\s+/g, ' ').trim(),
                size: getComputedStyle(f).fontSize,
                border: parseFloat(getComputedStyle(f).borderTopWidth),
                links: Array.from(f.querySelectorAll('a')).map((a) => a.getAttribute('href')),
                paragraphs: f.querySelectorAll('p').length,
                height: Math.round(f.getBoundingClientRect().height),
                last: f === document.querySelector('main').lastElementChild
            };
        }"""
    )
    if not state:
        return ["the page has no closing line"]
    problems = []
    expected = f"Last checked {checked}" if checked else "Last checked "
    if not state["text"].startswith(expected):
        problems.append(f"the closing line reads {state['text'][:40]!r}")
    if "#tbl" not in state["links"]:
        problems.append(f"the closing line has no way back: {state['links']}")
    if not any((link or "").startswith("mailto:") for link in state["links"]):
        problems.append(f"the closing line has no email address: {state['links']}")
    if state["paragraphs"] < 2:
        problems.append("the closing line does not say who runs the site")
    if "SubFree UK is" not in state["text"]:
        problems.append("the closing line does not name the site")
    if state["size"] != "13px" or state["border"] != 1:
        problems.append(
            f"the closing line is {state['size']} with a {state['border']}px rule, "
            "expected 13px and 1px"
        )
    if not state["last"] or state["height"] > 320:
        problems.append(f"the closing line sits at {state['height']}px and is not last")

    # Back to top: out of the way above the table, offered once the reader is
    # into it, and it returns the reader and the keyboard to the heading.
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    top = page.evaluate(
        """() => {
            const b = document.getElementById('totop');
            return b ? { hidden: b.hidden, label: b.getAttribute('aria-label') } : null;
        }"""
    )
    if not top:
        problems.append("the page has no back-to-top button")
    else:
        if not top["hidden"]:
            problems.append("the back-to-top button is offered at the top of the page")
        if not (top["label"] or "").lower().startswith("back to top"):
            problems.append(f"the back-to-top button is named {top['label']!r}")
        # Past the sentinel, which sits above the table, so the button has a
        # reason to appear whatever the page's height happens to be.
        page.evaluate(
            """() => {
                const s = document.getElementById('totop-s');
                const y = s.getBoundingClientRect().top + window.scrollY;
                window.scrollTo(0, y + 600);
            }"""
        )
        shown = True
        try:
            page.wait_for_function(
                "() => !document.getElementById('totop').hidden", timeout=2000
            )
        except Exception:
            shown = False
        if not shown:
            problems.append("the back-to-top button never appears once the table has scrolled")
        else:
            page.click("#totop")
            page.wait_for_timeout(900)
            back = page.evaluate(
                """() => ({
                    y: Math.round(window.scrollY),
                    focus: document.activeElement ? document.activeElement.tagName : ''
                })"""
            )
            if back["y"] > 40:
                problems.append(f"Back to top left the page at {back['y']}px")
            if back["focus"] != "H1":
                problems.append(f"Back to top leaves focus on {back['focus'] or 'nothing'}")
    return problems

def rule_check(page, row_count):
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
    if not box["inWrapper"] or box["rows"] != row_count:
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

def sort_figure_check(page):
    """The order follows a figure the row bolds, and the note names it.

    The default sort is by the 3-year cost to keep recordings, which is not a
    column of its own: Ring's figure comes from its plan and Reolink PoE's from
    the card in its box. Without the bold cell and the note under the control,
    the list reads as mis-sorted. The other sorts bold what they order by, or
    nothing when the figure is a column of its own.
    """
    problems = []
    state = page.evaluate(
        """() => {
            const read = () => {
                const note = document.getElementById('sortnote');
                return {
                    note: (note.textContent || '').trim(),
                    rows: Array.from(document.querySelectorAll('#tbl tbody.item')).map((t) => ({
                        id: t.id.slice(2),
                        basis: t.dataset.keep,
                        bold: Array.from(t.querySelectorAll('.c-nosub,.c-sub'))
                            .filter((c) => c.classList.contains('keep'))
                            .map((c) => (c.classList.contains('c-sub') ? 'sub' : 'nosub'))
                    }))
                };
            };
            const sort = document.getElementById('sort');
            const pick = (value) => {
                sort.value = value;
                sort.dispatchEvent(new Event('change', { bubbles: true }));
            };
            const states = {};
            pick('keep3');
            states.keep = read();
            pick('price');
            states.price = read();
            pick('nosub3');
            states.nosub = read();
            pick('sub3');
            states.sub = read();
            pick('keep3');
            return states;
        }"""
    )
    keep = state["keep"]
    if "3-year cost to keep recordings" not in keep["note"]:
        problems.append(f"the note under the sort control reads {keep['note']!r}")
    for row in keep["rows"]:
        if len(row["bold"]) != 1:
            problems.append(
                f"{row['id']} bolds {len(row['bold'])} cost cells at the default sort"
            )
        elif row["bold"][0] != row["basis"]:
            problems.append(
                f"{row['id']} bolds its {row['bold'][0]} figure but keeps records on the {row['basis']} one"
            )
    if state["price"]["note"] != "Order: price, low to high.":
        problems.append(f"the price sort note reads {state['price']['note']!r}")
    still = [r["id"] for r in state["price"]["rows"] if r["bold"]]
    if still:
        problems.append(f"{len(still)} rows keep a bold cost cell when sorting by price")
    for key, cell, words in (
        ("nosub", "nosub", "no plan"),
        ("sub", "sub", "with a plan"),
    ):
        wrong = [r["id"] for r in state[key]["rows"] if r["bold"] != [cell]]
        if wrong:
            problems.append(
                f"{len(wrong)} rows do not bold their {cell} figure when sorting by it"
            )
        if words not in state[key]["note"].lower():
            problems.append(f"the {cell} sort note reads {state[key]['note']!r}")
    return problems

def price_link_check(page):
    """Each price is the link to the page it came from.

    The intro promises that every price links to its source. A plain number
    under that promise is the one thing a reader checking a price cannot use,
    and the details name their sources by shop rather than by number.
    """
    problems = []
    state = page.evaluate(
        """() => {
            const rows = Array.from(document.querySelectorAll('#tbl tbody.item'));
            return {
                rows: rows.length,
                prices: rows.map((t) => {
                    const cell = t.querySelector('.c-price');
                    const a = cell.querySelector('a');
                    return {
                        id: t.id.slice(2),
                        text: (cell.textContent || '').trim(),
                        href: a ? a.getAttribute('href') : '',
                        rel: a ? (a.getAttribute('rel') || '') : '',
                        name: a ? (a.getAttribute('aria-label') || '') : '',
                        target: a ? (a.getAttribute('target') || '') : ''
                    };
                }),
                sourceNames: Array.from(document.querySelectorAll('#m-reo-poe .srcs a'))
                    .map((a) => a.textContent.trim())
            };
        }"""
    )
    if len(state["prices"]) < 2:
        return [f"found {len(state['prices'])} price cells to check"]
    unlinked = [p["id"] for p in state["prices"] if not p["href"].startswith("http")]
    if unlinked:
        problems.append(f"prices with no link to their source: {unlinked[:3]}")
    unpriced = [p["id"] for p in state["prices"] if "£" not in p["text"]]
    if unpriced:
        problems.append(f"price cells with no figure in them: {unpriced[:3]}")
    unnamed = [p["id"] for p in state["prices"] if " at " not in p["name"]]
    if unnamed:
        problems.append(f"price links without a shop in their name: {unnamed[:3]}")
    loose = [p["id"] for p in state["prices"]
             if "nofollow" not in p["rel"] or "noopener" not in p["rel"]]
    if loose:
        problems.append(f"price links without nofollow noopener: {loose[:3]}")
    numeric = [name for name in state["sourceNames"] if len(name) < 4 or name.isdigit()]
    if numeric:
        problems.append(f"the details name their sources by number: {numeric[:3]}")
    return problems

def page_key_check(page):
    """The row colours are explained in words, where the rows are.

    A green, blue and red rule down the left of a row carries a verdict, and a
    reader who cannot tell the three apart still needs to know what the colour
    beside the badge means. On a phone the three coloured lines of the short
    answer say the same thing, so the key would only repeat them.
    """
    problems = []
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(150)
    wide = page.evaluate(
        """() => {
            const k = document.getElementById('vkey');
            if (!k) return null;
            const cs = getComputedStyle(k);
            return {
                display: cs.display,
                text: k.textContent.replace(/\\s+/g, ' ').trim(),
                marks: k.querySelectorAll('span').length
            };
        }"""
    )
    if wide is None:
        problems.append("the page has no key to its row colours")
    elif wide["display"] == "none":
        problems.append("the row-colour key is hidden at 1280px")
    else:
        for word in ("Green", "Blue", "Red"):
            if word not in wide["text"]:
                problems.append(f"the row-colour key never says {word!r}: {wide['text']!r}")
        if wide["marks"] != 3:
            problems.append(f"the row-colour key has {wide['marks']} entries, expected 3")
        if "colour" in wide["text"].lower() or "bold" in wide["text"].lower():
            problems.append("the row-colour key describes the styling rather than the verdict")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(200)
    narrow = page.evaluate(
        """() => {
            const k = document.getElementById('vkey');
            const short = document.querySelector('.vshort');
            const lines = short ? Array.from(short.querySelectorAll('span')) : [];
            return {
                key: k ? getComputedStyle(k).display : 'missing',
                short: short ? getComputedStyle(short).display : 'missing',
                lines: lines.filter((s) => !s.classList.contains('vlab')).length,
                text: short ? short.textContent.replace(/\\s+/g, ' ').trim() : ''
            };
        }"""
    )
    if narrow["key"] != "none":
        problems.append(f"the key is {narrow['key']!r} at 390px, where the short answer carries it")
    if narrow["short"] == "none" or narrow["lines"] < 3:
        problems.append(f"the phone short answer has {narrow['lines']} lines: {narrow['short']!r}")
    for word in ("best", "battery", "plan"):
        if word not in narrow["text"].lower():
            problems.append(f"the phone short answer never says {word!r}")
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(150)
    return problems

def details_check(page):
    """The details panel says each row in a sentence, in two aligned columns."""
    problems = []
    page.evaluate(
        """() => {
            const b = document.querySelector('#m-reo-poe .more');
            if (b.getAttribute('aria-expanded') !== 'true') b.click();
        }"""
    )
    page.wait_for_timeout(200)
    state = page.evaluate(
        """() => {
            const panel = document.querySelector('#m-reo-poe tr.detail');
            const pairs = Array.from(panel.querySelectorAll('.dspec .pair'));
            const left = (el) => Math.round(el.getBoundingClientRect().left);
            const value = (i) => (pairs[i] ? pairs[i].querySelector('dd').textContent.trim() : '');
            return {
                hidden: panel.hidden,
                pairs: pairs.length,
                columns: Array.from(new Set(pairs.map(left))).sort((a, b) => a - b),
                power: value(0),
                storage: value(2),
                labels: pairs.map((p) => p.querySelector('dt').textContent.trim())
            };
        }"""
    )
    if state["hidden"]:
        problems.append("Details did not open")
    if state["pairs"] < 12:
        problems.append(f"the details panel lists {state['pairs']} rows, expected 13")
    if len(state["columns"]) != 2:
        problems.append(
            f"the details panel's pairs sit at {state['columns']}, expected two columns"
        )
    # A sentence rather than a data string: long, punctuated, and not a list of
    # terms joined by punctuation.
    for name, text in (("power", state["power"]), ("storage", state["storage"])):
        if len(text) < 40 or not text.rstrip().endswith("."):
            problems.append(f"the {name} line reads {text!r}")
        if " / " in text or ";" in text:
            problems.append(f"the {name} line is still a list of terms: {text!r}")
    for want in ("Power", "Storage", "Wi-Fi", "History without a plan"):
        if want not in state["labels"]:
            problems.append(f"the details panel has no {want!r} row")
    page.evaluate(
        """() => {
            const b = document.querySelector('#m-reo-poe .more');
            if (b.getAttribute('aria-expanded') === 'true') b.click();
        }"""
    )
    page.wait_for_timeout(120)
    return problems

def print_check(page):
    """On paper each figure sits under its own heading.

    Printing drops the compare box. A grid cell that is hidden leaves its
    track behind, so the seven cells that remain start one track left of where
    the seven remaining headings start, and every value prints under the
    heading of the column before it. The page is also narrower on paper than
    on screen, so this is measured at 1123px: A4 landscape, the width at which
    the numbered columns are laid out as columns at all.
    """
    problems = []
    page.set_viewport_size({"width": 1123, "height": 900})
    page.emulate_media(media="print")
    try:
        page.wait_for_timeout(200)
        state = page.evaluate(
            """() => {
                const row = document.querySelector('#tbl tbody.item tr.main');
                const left = (el) => Math.round(el.getBoundingClientRect().left);
                const shown = (el) => getComputedStyle(el).display !== 'none';
                const headings = Array.from(document.querySelectorAll('#tbl thead th')).filter(shown);
                const values = Array.from(row.children).filter(shown);
                const th = document.querySelector('#tbl thead th.c-cmp');
                const td = row.querySelector('td.c-cmp');
                return {
                    headings: headings.map(left),
                    values: values.map(left),
                    box: [th, td].map((el) => (el ? getComputedStyle(el).display : 'missing')),
                    badge: getComputedStyle(document.querySelector('.zi')).display
                };
            }"""
        )
    finally:
        page.emulate_media(media="screen")
        page.set_viewport_size({"width": 1280, "height": 900})
        page.wait_for_timeout(150)
    if state["box"] != ["none", "none"]:
        problems.append(f"the compare column prints as {state['box']}")
    if len(state["headings"]) != len(state["values"]):
        problems.append(
            f"{len(state['headings'])} headings print over {len(state['values'])} cells"
        )
    else:
        shifted = [
            heading
            for heading, value in zip(state["headings"], state["values"])
            if abs(heading - value) > 1
        ]
        if shifted:
            problems.append(
                f"printed cells start at {state['values']}, headings at {state['headings']}"
            )
    if state["badge"] != "none":
        problems.append("the photo's magnifier badge prints beside every photo")
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

def bars_check(page, row_count):
    """Score bars are painted once at their score and never redrawn on a sort."""
    problems = []
    page.wait_for_timeout(800)
    initial = page.evaluate(BARS_JS)
    if initial["n"] != row_count:
        problems.append(f"{initial['n']} score bars are visible, expected {row_count}")
    if initial["transition"] != "0s":
        problems.append(
            f"the score bar still transitions {initial['property']} over {initial['transition']!r}"
        )
    off = [(a, b) for a, b in zip(initial["scales"], initial["targets"]) if abs(a - b) > 0.01]
    if off:
        problems.append(f"a bar is scaled {off[0][0]:.2f}, not its score {off[0][1]:.2f}")

    # A sort must not touch them: no zero phase, no timers, no redraw. Keyed by
    # row, because the sort reorders the DOM under the selector.
    before = page.evaluate(
        """() => Object.fromEntries(Array.from(document.querySelectorAll('#tbl tbody.item .bar i'))
            .map((b) => [b.closest('tbody.item').id, b.style.transform]))"""
    )
    painted = page.evaluate(
        """() => {
            const sel = document.getElementById('sort');
            sel.value = 'price';
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            return Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'))
                .map((b) => getComputedStyle(b).transform);
        }"""
    )
    page.wait_for_timeout(400)
    after = page.evaluate(
        """() => Object.fromEntries(Array.from(document.querySelectorAll('#tbl tbody.item .bar i'))
            .map((b) => [b.closest('tbody.item').id, b.style.transform]))"""
    )
    moved = [k for k in before if before[k] != after.get(k)]
    if moved:
        problems.append(f"a sort rewrites the bar transforms on {len(moved)} rows")
    if not painted or not all(t.startswith("matrix") for t in painted):
        problems.append(f"a bar has no computed transform after the sort: {painted[:2]}")

    page.emulate_media(reduced_motion="reduce")
    page.wait_for_timeout(80)
    reduced = page.evaluate(BARS_JS)
    off = [(a, b) for a, b in zip(reduced["scales"], reduced["targets"]) if abs(a - b) > 0.01]
    if off:
        problems.append(f"reduced motion shows a bar at {off[0][0]:.2f}, not {off[0][1]:.2f}")
    page.emulate_media(reduced_motion="no-preference")
    return problems

def contain_check(page, row_count):
    """Off-screen phone cards skip layout, with an intrinsic size to stand in."""
    problems = []
    got = page.evaluate(
        """() => {
            const card = document.querySelector('#tbl tbody.item');
            const cs = getComputedStyle(card);
            const cards = Array.from(document.querySelectorAll('#tbl tbody.item'));
            return { visibility: cs.contentVisibility,
                     size: cs.containIntrinsicSize,
                     n: cards.length,
                     hidden: cards.filter((c) => c.hidden).length };
        }"""
    )
    if got["visibility"] != "auto":
        problems.append(f"a phone card's content-visibility is {got['visibility']!r}, expected auto")
    if got["size"] != "auto 330px":
        problems.append(f"the phone card's intrinsic size is {got['size']!r}, expected 'auto 330px'")
    if got["n"] != row_count or got["hidden"]:
        problems.append(
            f"{got['n']} cards with {got['hidden']} hidden, expected {row_count} shown"
        )
    return problems

def desktop_rows_check(page, row_count):
    """At desktop widths a row is a contained grid track, and its columns line up.

    The table's own column widths cannot survive a sort cheaply, so the rows are
    grid tracks with the widths the table chose; a mistyped track silently
    squeezes a column or breaks the row rule, which nothing else catches.
    """
    problems = []
    for width in (1440, 1280, 1100, 1000, 900):
        page.set_viewport_size({"width": width, "height": 900})
        page.wait_for_timeout(120)
        got = page.evaluate(DESKTOP_ROWS_JS)
        if got["display"] != "grid" or got["tracks"] != 8:
            problems.append(
                f"at {width}px a row is {got['display']!r} with {got['tracks']} tracks, "
                "expected a grid of 8"
            )
        if got["cardDisplay"] != "block":
            problems.append(f"at {width}px a row group is {got['cardDisplay']!r}, expected block")
        if got["visibility"] != "auto" or not got["size"].startswith("auto "):
            problems.append(
                f"at {width}px the rows are not contained: {got['visibility']!r} {got['size']!r}"
            )
        if len(got["rows"]) != row_count:
            problems.append(
                f"at {width}px {len(got['rows'])} of {row_count} rows are showing"
            )
            continue
        skew = max(
            abs(left - head)
            for row in got["rows"]
            for left, head in zip(row["lefts"], got["head"])
        )
        if skew > 1:
            problems.append(f"at {width}px a row's columns sit {skew:.0f}px off the header's")
        ragged = [row["id"] for row in got["rows"] if max(row["heights"]) - min(row["heights"]) > 1]
        if ragged:
            problems.append(f"at {width}px the row rule breaks in {ragged[0]}")
        if got["clipped"]:
            problems.append(f"at {width}px a cell clips its text: {got['clipped'][0]}")
        if got["overflow"] > 1:
            problems.append(f"at {width}px the table overflows by {got['overflow']}px")
    # A sticky cell cannot outrun its parent, so the header row has to stick as
    # a block here; sticking the cells leaves the table header behind on scroll.
    page.evaluate("document.getElementById('tbl').scrollIntoView()")
    page.mouse.wheel(0, 900)
    page.wait_for_timeout(300)
    stuck = page.evaluate(STUCK_JS)
    if stuck["top"] != 0 or not stuck["covers"]:
        problems.append(f"the header leaves the top of the page when the table scrolls: {stuck}")
    page.evaluate("window.scrollTo(0, 0)")

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(160)
    cards = page.evaluate(DESKTOP_ROWS_JS)
    # A phone card is three tracks: the compare box, then two columns of
    # figures. The two 3-year costs share a row, so a card is a third shorter
    # than it was when each figure had a line of its own.
    if cards["tracks"] != 3:
        problems.append(f"at 390px a row has {cards['tracks']} tracks, expected the 3-track card")
    for row in cards["rows"]:
        if abs(row["pair"]["ny"] - row["pair"]["sy"]) > 2 or row["pair"]["nx"] == row["pair"]["sx"]:
            problems.append(f"at 390px the two 3-year figures in {row['id']} are not side by side")
            break
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(120)
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
    # White photo tiles glare against the near-black page, so dark mode dims the
    # tile behind each photo as well as the photo itself.
    was = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
    page.evaluate("() => document.documentElement.setAttribute('data-theme', 'dark')")
    page.wait_for_timeout(120)
    tile = page.evaluate(
        """() => {
            const el = document.querySelector('.ph');
            return el ? getComputedStyle(el).backgroundColor : '';
        }"""
    )
    page.evaluate(
        """(was) => {
            if (was === null) document.documentElement.removeAttribute('data-theme');
            else document.documentElement.setAttribute('data-theme', was);
        }""",
        was,
    )
    numbers = [int(part) for part in tile.replace("rgb(", "").replace(")", "").replace(" ", "").split(",") if part.isdigit()]
    if len(numbers) < 3 or max(numbers[:3]) > 90:
        problems.append(f"the photo tile in dark mode is {tile!r}, expected a dim tile")
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
                ],
                range: (document.getElementById("f-range") || {}).textContent || ""
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
    # Two thumbs on top of each other read as one grey track, so the range is
    # also printed as words above the slider.
    expected_range = f"£{shapes['values'][0]} to £{shapes['values'][1]}"
    if shapes["range"] != expected_range:
        problems.append(f"the range reads {shapes['range']!r}, expected {expected_range!r}")

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
    moved = page.evaluate("() => (document.getElementById('f-range') || {}).textContent || ''")
    if "£200" not in moved:
        problems.append(f"the range text does not follow the handles: {moved!r}")

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

CHECKS = [
    Check(
        "filter panel", "phone", 13,
        "the phone filter panel reopens when the window grows past 520px",
        lambda ctx: filters_check(ctx.page),
    ),
    Check(
        "price slider", "phone", 14,
        "the price slider is one labelled handle per end, fills to the handles, and filters",
        lambda ctx: price_check(ctx.page),
    ),
    Check(
        "compare cap", "phone", 15,
        "the 3-row cap is explained and announced; Compare sits by the count",
        lambda ctx: copy_check(ctx.page),
    ),
    Check(
        "labels", "phone", 16,
        "Nest names its 3-hour limit, no-plan reads as words, PoE is defined at the filter",
        lambda ctx: labels_check(
            ctx.page, ctx.dataset.REC_LABEL["brief"] if ctx.dataset else None
        ),
    ),
    Check(
        "closing line", "phone", 17,
        "the page ends on one line with the date, an issue link and a way back",
        lambda ctx: footer_check(ctx.page, ctx.checked),
    ),
    Check(
        "empty result", "phone", 18,
        "filtering announces its count; an empty result offers the nearest match",
        lambda ctx: recovery_check(ctx.page),
    ),
    Check(
        "score bars", "phone", 19,
        "score bars are painted at their score and a sort never redraws them",
        lambda ctx: bars_check(ctx.page, ctx.row_count),
    ),
    Check(
        "source list", "phone", 21,
        "the sources sit in a host-grouped disclosure, closed below 821px and open above it",
        lambda ctx: sources_check(ctx.page, ctx.source_count),
    ),
    Check(
        "compare header at 390", "phone", 22,
        "the compare heading stays on one line and its links in one row",
        lambda ctx: head_check(ctx.page),
    ),
    Check(
        "skip link", "desktop", 30,
        "the skip link is the first Tab stop and Enter lands on the table",
        lambda ctx: skip_check(ctx.page),
    ),
    Check(
        "details hit area", "desktop", 31,
        "Details takes a click 8px outside its visible box",
        lambda ctx: hit_check(ctx.page),
    ),
    Check(
        "theme toggle", "desktop", 32,
        "the theme toggle names its action and takes a 44px click",
        lambda ctx: theme_check(ctx.page),
    ),
    Check(
        "theme motion", "desktop", 34,
        "the theme disc turns and the page fades over 180ms, off under reduced motion",
        lambda ctx: motion_check(ctx.page),
    ),
    Check(
        "jump announcement", "desktop", 35,
        "a jump announces its model, verdict and row, then clears",
        lambda ctx: jump_check(ctx.page),
    ),
    Check(
        "desktop rows", "desktop", 36,
        "desktop rows are contained grid tracks: columns line up with the header, no cell clips, 900 to 1440px",
        lambda ctx: desktop_rows_check(ctx.page, ctx.row_count),
    ),
    Check(
        "scroll rule", "desktop", 38,
        "a hairline along the table follows scroll, with a plain rule where timelines are missing",
        lambda ctx: rule_check(ctx.page, ctx.row_count),
    ),
    Check(
        "compare header at 1280", "desktop", 39,
        "the compare heading stays on one line and its links in one row at 1280",
        lambda ctx: head_check(ctx.page),
    ),
    Check(
        "sort figure", "compare", 48,
        "the note under the sort control names the figure, and each row bolds the cell the order uses",
        lambda ctx: sort_figure_check(ctx.page),
    ),
    Check(
        "price links", "compare", 49,
        "every price opens the page it came from, and the details name their sources by shop",
        lambda ctx: price_link_check(ctx.page),
    ),
    Check(
        "page key", "compare", 50,
        "the row colours are explained in words at 1280 and by the phone's three lines at 390",
        lambda ctx: page_key_check(ctx.page),
    ),
    Check(
        "details panel", "compare", 51,
        "a details panel says power and storage in sentences, in two aligned columns",
        lambda ctx: details_check(ctx.page),
    ),
    Check(
        "print", "compare", 53,
        "on paper each figure prints under its own heading, with no compare box",
        lambda ctx: print_check(ctx.page),
    ),
    Check(
        "photo lightbox", "compare", 75,
        lambda ctx: f"{ctx.lightbox['buttons']} photos open in the lightbox, named, "
        "sized from the large file, and Esc closes it",
        lambda ctx: ctx.lightbox["problems"],
    ),
]

