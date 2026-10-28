"""The shape of the document and of the files the build writes."""
import hashlib
import os
import re

from catalog import CATEGORIES
from .behaviour import contain_check
from .compare import COMPARE_ROWS
from .context import ROOT, WIDTHS, open_compare
from .js import OVERFLOW_JS
from .registry import Check


def notfound_check():
    """A mistyped address lands on the site's own page, not on GitHub's."""
    path = os.path.join(ROOT, "404.html")
    if not os.path.exists(path):
        return ["404.html is missing"]
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    problems = []
    if "<h1>Page not found</h1>" not in text:
        problems.append("the 404 page has no 'Page not found' heading")
    if 'href="/subfree-uk/"' not in text:
        problems.append("the 404 page does not link back to the comparison")
    if "github.com" in text:
        problems.append("the 404 page still points at GitHub")
    if 'name="robots" content="noindex"' not in text:
        problems.append("the 404 page can be indexed")
    if "assets/page.css?v=" not in text:
        problems.append("the 404 page does not wear the site's stylesheet")
    return problems

def emitted_sources(pages):
    """The page loads the committed CSS and script by their own content hash.

    The hash is taken from the file, not from the module that wrote it, so a
    page pointing at an older version fails here even when the build itself is
    happy. `rebuild` covers the other half: that the committed file is what the
    build would write.
    """
    problems = []
    for cat in CATEGORIES:
        html = pages[cat["page"]]
        for name, link in (("assets/page.css", "href"), ("assets/page.js", "src")):
            path = os.path.join(ROOT, name)
            if not os.path.exists(path):
                problems.append(f"{name} is missing")
                continue
            text = open(path, encoding="utf-8").read()
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]
            # A nested route reaches the assets one level up, so only the file
            # and its hash are fixed.
            if not re.search(rf'{link}="(?:\.\./)*{re.escape(name)}\?v={digest}"', html):
                problems.append(f"{cat['page']} does not load {name}?v={digest}")
        if "<style>" in html:
            problems.append(f"{cat['page']} still inlines its stylesheet")
        if "@@DATA@@" in html or "@@CHECKED@@" in html:
            problems.append(f"a build placeholder leaked into {cat['page']}")
    return problems

def alias_problems(pages):
    problems = []
    for cat in CATEGORIES:
        alias = pages[cat["alias"]]
        if 'http-equiv="refresh"' not in alias or "url=./" not in alias:
            problems.append(f"{cat['alias']} is not a redirect to ./")
        if len(alias) > 1000:
            problems.append(
                f"{cat['alias']} is {len(alias)} bytes; it should be a redirect, not a copy"
            )
        if pages[cat["page"]] == alias:
            problems.append(f"{cat['page']} and {cat['alias']} are identical again")
    return problems

def phone_first_paint(phone):
    if (
        not phone["open"]
        and phone["firstRowTop"] < 600
        and phone["verdict"] == "none"
        and phone["shortAnswer"] == "block"
    ):
        return []
    return [
        "phone first paint: "
        f"filters open={phone['open']}, first product at "
        f"{phone['firstRowTop']}px of {phone['viewport']}px, "
        f"verdict={phone['verdict']}, short answer={phone['shortAnswer']}"
    ]

def short_answer_check(page):
    """The phone keeps all three recommendations, each on its own line.

    The desktop's longer verdict block is hidden on a phone. The audit's item 8
    was that the short answer had shrunk to one condensed sentence, dropping
    the reasons and the warning, so all three lines have to be there, in their
    own colours, and each has to fit in two lines.
    """
    state = page.evaluate(
        """() => {
            const short = document.querySelector('.vshort');
            const verdict = document.querySelector('.verdict');
            const spans = Array.from(short.querySelectorAll('span'));
            return {
                shown: getComputedStyle(short).display !== 'none',
                verdict: verdict ? getComputedStyle(verdict).display : 'none',
                lines: spans.map((s) => {
                    const cs = getComputedStyle(s);
                    return {
                        cls: s.className,
                        words: s.textContent.replace(/\s+/g, ' ').trim(),
                        border: parseFloat(cs.borderLeftWidth),
                        colour: cs.borderLeftColor,
                        height: s.getBoundingClientRect().height,
                        line: parseFloat(cs.lineHeight)
                    };
                })
            };
        }"""
    )
    problems = []
    if not state["shown"] or state["verdict"] != "none":
        problems.append(
            f"the phone shows the short answer={state['shown']} and the verdict "
            f"block={state['verdict']}"
        )
    if [line["cls"] for line in state["lines"]] != ["v-best", "v-batt", "v-avoid"]:
        problems.append(
            f"the phone's short answer lines are {[line['cls'] for line in state['lines']]}"
        )
    wants = (
        ("Reolink", "best overall"),
        ("Tapo", "easiest battery"),
        # The third line is the warning the condensed sentence dropped: Ring
        # needs a plan, and Blink and Arlo need hardware.
        ("Ring", "Blink", "Arlo"),
    )
    for line, needed in zip(state["lines"], wants):
        missing = [word for word in needed if word not in line["words"]]
        if missing:
            problems.append(f"the {line['cls']} line is missing {missing}: {line['words']!r}")
        if line["border"] < 2:
            problems.append(f"the {line['cls']} line has no colour rule: {line['border']}px")
        if line["line"] and line["height"] > line["line"] * 2 + 1:
            problems.append(
                f"the {line['cls']} line takes {line['height'] / line['line']:.1f} lines"
            )
    colours = {line["colour"] for line in state["lines"]}
    if len(colours) != 3:
        problems.append(f"the three short-answer lines share {len(colours)} colour(s): {colours}")
    return problems


def cost_cells(cost):
    return [] if cost["aFits"] and cost["bFits"] else [f"phone cost cells overflow: {cost}"]

def phone_header(header, roles):
    if (
        header["display"] != "none"
        and header["width"] <= 2
        and header["headers"] == 8
        and header["untabbable"]
        and roles
    ):
        return []
    return [
        "phone table header: "
        f"display={header['display']}, width={header['width']}px, "
        f"headers={header['headers']}, untabbable={header['untabbable']}, "
        f"columnheader in tree={roles}"
    ]

def share_meta(data):
    if data["icon"] == "favicon.svg" and data["canonical"].endswith("/subfree-uk/"):
        return []
    return [
        f"share metadata: icon={data['icon']!r}, canonical={data['canonical']!r}, "
        f"og:title={data['ogTitle']!r}"
    ]

def verdict_tags(data):
    best = data["tags"].count("Best overall")
    if best == 1 and "Best with doorbell wiring" in data["tags"]:
        return []
    return [f'verdict tags: {best} rows say "Best overall" ({data["tags"]})']

def row_rule(data):
    rule = data["rowRule"]
    if rule and rule["border"] == 3 and rule["gap"] >= 4 and rule["plain"] == 0:
        return []
    return [f"verdict row rule: {rule}"]

def filters_row_check(page):
    """The option groups read on one row, and the sort control never squeezes them.

    The details box used to size itself to its own content, so both groups
    wrapped and the price slider stopped at 178px with half the row unused.
    Taking the line fixed that at the wide end and left the middle squeezed:
    the filters need 794px beside a 290px sort control, so from 1101 to 1199
    the sort took a share and both groups wrapped again. Below 1280 the sort
    takes a line of its own, where it costs nothing, and the filters keep the
    whole line. That line starts under the option groups and the count closes
    it: placed at the end of the band the sort read as a caption for the price
    slider above it, with the count stranded at the other end. Each width is
    measured in the page's own font and again at Verdana, about 15% wider,
    because that is the font that hid the 1280 case.
    """
    widths = (821, 850, 900, 1101, 1200, 1279, 1280, 1440)
    read = """() => {
        const box = (el) => el.getBoundingClientRect();
        const body = document.querySelector('.fbody');
        const filters = box(document.querySelector('.filters'));
        const sort = box(document.querySelector('.sortby'));
        const count = box(document.querySelector('.count'));
        return {
            rows: Array.from(body.querySelectorAll('.opts')).map(
                (group) => new Set(Array.from(group.children).map((l) => Math.round(box(l).top))).size
            ),
            slider: Math.round(box(document.querySelector('.dual')).width),
            beside: Math.abs(filters.top - sort.top) < 3,
            overlap: filters.left < sort.right && sort.left < filters.right
                && filters.top < sort.bottom && sort.top < filters.bottom,
            sortIndent: Math.round(sort.left - filters.left),
            countShares: Math.abs(count.top - sort.top) <= 2 && count.left >= sort.right - 1
        };
    }"""
    problems = []
    wide = "Verdana, DejaVu Sans, sans-serif"
    for font, suffix in (("", ""), (wide, " under the wider fallback")):
        if font:
            page.evaluate(
                "(font) => document.documentElement.style.setProperty('--sans', font)", font
            )
        for width in widths:
            page.set_viewport_size({"width": width, "height": 900})
            page.wait_for_timeout(90)
            state = page.evaluate(read)
            where = f"at {width}px{suffix}"
            # At 821 and 850 the row is narrower than the three controls in a
            # font this wide: 866px against 789. The groups reflow to two rows,
            # which is the row's own limit and not the squeeze this fixes.
            if width >= 900 and state["rows"] != [1, 1]:
                problems.append(
                    f"{where} the option groups read in {state['rows']} rows, expected one each"
                )
            if state["overlap"]:
                problems.append(f"{where} the sort control overlaps the filters")
            if width < 1280:
                # The sort opens its own line under the option groups, and the
                # count shares it at the far end, so the band reads as one row
                # of controls rather than a caption for the price slider.
                if state["sortIndent"] != 0:
                    problems.append(
                        f"{where} the sort control starts {state['sortIndent']}px "
                        "off the filters' edge instead of under the option groups"
                    )
                if not state["countShares"]:
                    problems.append(
                        f"{where} the count is not on the sort control's line: {state}"
                    )
            if width < 1280 and state["beside"]:
                problems.append(f"{where} the sort control takes a share of the filters' line")
            if width >= 1280 and not state["beside"]:
                problems.append(f"{where} the sort control left the filters' line")
            floor = 300 if width == 1440 else 160
            if state["slider"] < floor:
                problems.append(
                    f"{where} the price slider is {state['slider']}px wide, expected {floor} or more"
                )
        if font:
            page.evaluate("() => document.documentElement.style.removeProperty('--sans')")
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(120)
    return problems

def price_cells(data):
    return (
        [f"{data['priceFootnotes']} footnote numbers in price cells"]
        if data["priceFootnotes"]
        else []
    )

def zoom_images(data, lightbox):
    if data["zoomGlyphs"] == lightbox["buttons"] and lightbox["buttons"]:
        return []
    return [f"{lightbox['buttons']} photo buttons but {data['zoomGlyphs']} zoom glyphs"]

def contact_routes(data):
    if data["contactLinks"] >= 2:
        return []
    return [f"expected a contact link in the header and the method, found {data['contactLinks']}"]

def landmarks_and_ids(data):
    problems = []
    if data["mains"] != 1:
        problems.append(f"expected one main landmark, found {data['mains']}")
    if data["duplicateIds"]:
        problems.append("duplicate ids: " + ", ".join(sorted(set(data["duplicateIds"]))))
    if data["brokenAnchors"]:
        problems.append("broken anchors: " + ", ".join(data["brokenAnchors"]))
    return problems

def image_files(data):
    missing = [
        src for src in data["localRefs"]
        if not os.path.exists(os.path.join(ROOT, src.split("?")[0]))
    ]
    return ["missing image files: " + ", ".join(sorted(set(missing)))] if missing else []

def secure_links(data):
    plain = [link for link in data["externals"] if link.startswith("http://")]
    return ["external links over plain http: " + ", ".join(plain[:5])] if plain else []

def overflow_problems(widths):
    overflow = [f"{width}px" for width, result in widths if result["over"] > 0]
    if not overflow:
        return []
    detail = "; ".join(
        f"{width}px: {result['over']}px past {', '.join(result['offenders'])}"
        for width, result in widths
        if result["over"] > 0
    )
    return [f"horizontal page overflow at {', '.join(overflow)} ({detail})"]

def tiny(snapshot, width):
    if not snapshot["tiny"]:
        return []
    return [f"text below 11px at {width}: " + "; ".join(sorted(set(snapshot["tiny"]))[:6])]


def cost_header_check(page):
    foot = page.locator("#tbl thead th[data-sort=nosub3] button").aria_snapshot()
    # The two cost headers are the columns a reader has to decode, so they are
    # written out at the same size as the rest, and the footnote letter is a link
    # to the working, in place.
    heads = page.evaluate(
        """() => {
            const read = (sort) => {
                const th = document.querySelector('#tbl thead th[data-sort=' + sort + ']');
                if (!th) return null;
                const button = th.querySelector('button');
                const mark = th.querySelector('.mk');
                const target = mark ? document.querySelector(mark.getAttribute('href')) : null;
                const style = getComputedStyle(button);
                return {
                    text: (button.textContent || '').trim(),
                    button: Math.round(button.getBoundingClientRect().width),
                    size: parseFloat(style.fontSize),
                    lines: Math.round(
                        button.getBoundingClientRect().height / parseFloat(style.lineHeight)
                    ),
                    mark: mark ? (mark.textContent || '').trim() : '',
                    markSize: mark ? parseFloat(getComputedStyle(mark).fontSize) : 0,
                    markBox: mark ? Math.round(mark.getBoundingClientRect().width) : 0,
                    href: mark ? mark.getAttribute('href') : '',
                    landed: !!target
                };
            };
            return { nosub: read('nosub3'), sub: read('sub3') };
        }"""
    )
    problems = [] if "footnote a" in foot else [f"cost header name: {foot.strip()}"]
    for key, letter, words in (("nosub", "a", "no plan"), ("sub", "b", "with plan")):
        head = heads[key]
        if not head:
            problems.append(f"the {key} cost header is missing")
            continue
        if head["text"].lower() != f"3-year cost, {words}":
            problems.append(f"the {key} cost header reads {head['text']!r}")
        if head["size"] < 12:
            problems.append(f"the {key} cost header is {head['size']}px")
        # The heading is the tallest in the table, so every extra line it takes
        # is a line off every row's first paint. Three is the most the words fit
        # in at 1280px, where each cost column is 152px: the widest common
        # fallback font needs about 100px of button, and the marker takes 16 of
        # the rest. A narrower track wrapped the words onto a fifth line.
        if head["lines"] > 3:
            problems.append(f"the {key} cost header takes {head['lines']} lines")
        # The line count above only fails on a font wide enough to run out of
        # room, so it passes on this machine's default and failed on CI's. The
        # button's width does not depend on the font: it is the column less the
        # marker's 16 and the padding's 32, so it states the same floor in the
        # unit the line count is decided by.
        if head["button"] < 100:
            problems.append(
                f"the {key} cost header has {head['button']}px for its words; "
                "the widest common fallback font needs 100"
            )
        if head["markSize"] > 12:
            problems.append(
                f"the {key} cost header's marker is {head['markSize']}px, not a footnote"
            )
        if head["markBox"] < 24:
            problems.append(
                f"the {key} cost header's marker is a {head['markBox']}px target"
            )
        if head["mark"] != letter or head["href"] != f"#m-{letter}":
            problems.append(
                f"the {key} cost header's marker is {head['mark']!r} to {head['href']!r}"
            )
        elif not head["landed"]:
            problems.append(f"the {key} cost header's marker points at nothing")
    return problems


def overflow_check(page):
    widths = []
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        page.wait_for_timeout(80)
        widths.append((width, page.evaluate(OVERFLOW_JS)))
    return overflow_problems(widths)


def table_name_check(page):
    """The table says what it is, and the skip link names the same table.

    A screen reader landed on an unnamed table of rows and columns, from a link
    that promised "the comparison table" and pointed at another table. Both
    names come from the category record, so a second one cannot inherit these.
    """
    cat = CATEGORIES[0]
    problems = []
    snap = page.locator("#tbl").aria_snapshot()
    if f'table "{cat["table_name"]}' not in snap:
        problems.append(f"the table is announced as {snap.splitlines()[0] if snap else 'nothing'}")
    skip = page.evaluate(
        """() => {
            const a = document.querySelector('a.skip');
            return { text: (a.textContent || '').trim(), href: a.getAttribute('href') };
        }"""
    )
    if skip["href"] != "#tbl" or skip["text"] != cat["skip"]:
        problems.append(f"the skip link reads {skip['text']!r} and points at {skip['href']!r}")
    return problems

def mast_remit_check(page):
    """The masthead keeps saying what the site is at 390, and the count says doorbells.

    The long remit is the masthead's only statement of scope and it is the first
    thing a phone drops, which left the narrowest width with no scope at all.
    """
    state = page.evaluate(
        """() => ({
            remit: Array.from(document.querySelectorAll('.mast > div > span'))
                .filter((s) => s.getBoundingClientRect().width > 1 && s.textContent.trim())
                .map((s) => s.textContent.trim()),
            count: ((document.querySelector('.count') || {}).textContent || '').trim()
        })"""
    )
    problems = []
    if not state["remit"]:
        problems.append("the masthead states no remit at 390")
    if f"{CATEGORIES[0]['nouns']} to compare" not in state["count"]:
        problems.append(f"the count line reads {state['count']!r}")
    return problems

def photo_names_check(page):
    """Two photos on one row get two names, so a reader knows which one opens.

    The thumbnail beside the name and the large photo in the details were both
    "View <model> photo full size", which is one name for two targets. Both
    open the same full-size image, so the pair says which photo the reader is
    on ("View <model> photo" and "View <model> photo full size") rather than
    calling the first one a thumbnail it does not open.
    """
    rows = page.evaluate(
        """() => Array.from(document.querySelectorAll('#tbl tbody.item')).map(
            (row) => Array.from(row.querySelectorAll('button.zoom')).map(
                (b) => (b.getAttribute('aria-label') || '').trim()
            )
        )"""
    )
    problems = []
    for index, names in enumerate(rows):
        if len(names) < 2:
            continue
        if any(not name for name in names):
            problems.append(f"row {index + 1} has a photo button without a name")
        elif len(set(names)) != len(names):
            problems.append(f"row {index + 1} names both photos {names[0]!r}")
        elif not names[1].endswith("full size"):
            problems.append(
                f"row {index + 1} names its two photos {names}, which do not say "
                "which photo the reader opened"
            )
    return problems

def compare_words_check(ctx):
    """Both cost columns are named as the table names them, and a delta says against what.

    The comparison wrote "3 YRS, NO PLAN" where the table wrote "3-year cost, no
    plan", and "cheapest" meant the lowest of the selected models in one place
    and the cheapest plan for one model in another. A delta read "+£15.00"
    with nothing to compare it to, and the cheapest column can be off the edge
    of a phone.
    """
    # The performance pass reloads the page, so the comparison a later check
    # needs is opened here rather than assumed open.
    open_compare(ctx.page)
    state = ctx.page.evaluate(
        """() => {
            const labels = Array.from(
                document.querySelectorAll('#cmp-table tbody th')
            ).map((th) => (th.textContent || '').trim());
            const cost = document.querySelector('#cmp-table tr.cmp-cost');
            const cells = Array.from(cost.querySelectorAll('td')).map((td) => ({
                total: (td.querySelector('b') || {}).textContent || '',
                diff: (td.querySelector('.cmp-diff') || {}).textContent || ''
            }));
            const notes = Array.from(document.querySelectorAll('#tbl .c-sub .note'))
                .map((n) => (n.textContent || '').trim());
            return { labels, cells, notes };
        }"""
    )
    problems = []
    for want in ("3-year cost, no plan", "3-year cost, with plan"):
        if want not in state["labels"]:
            problems.append(f"the comparison has no {want!r} row")
    cheapest = [c for c in state["cells"] if "cheapest of these 3" in c["diff"]]
    if len(cheapest) != 1:
        problems.append(f"{len(cheapest)} columns say 'cheapest of these 3', expected one")
    for cell in state["cells"]:
        if cell["diff"] and "cheapest of these 3" not in cell["diff"] and " more than " not in cell["diff"]:
            problems.append(f"the delta {cell['diff']!r} does not name its baseline")
    if not state["notes"] or not all("for this model" in note for note in state["notes"]):
        problems.append(f"the plan-is-cheapest notes read {state['notes']}")
    return problems

def compare_target_check(page):
    """The compare box's label is 44x44, on a desk as well as on a phone."""
    problems = []
    for width in (1280, 390):
        page.set_viewport_size({"width": width, "height": 900})
        page.wait_for_timeout(120)
        box = page.evaluate(
            """() => {
                const r = document.querySelector('#tbl tbody .cmp-w').getBoundingClientRect();
                return { w: Math.round(r.width), h: Math.round(r.height) };
            }"""
        )
        if box["w"] < 44 or box["h"] < 44:
            problems.append(
                f"at {width}px the compare label is {box['w']}x{box['h']}px, expected 44x44"
            )
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(120)
    return problems

def compare_caption_check(page):
    compare = page.evaluate(
        """() => ({
            caption: (document.querySelector("#cmp-table caption") || {}).textContent || "",
            rows: document.querySelectorAll("#cmp-table tbody tr").length
        })"""
    )
    cat = CATEGORIES[0]
    want = cat["cmp_caption"].replace("{count}", "3").replace("{nouns}", cat["nouns"])
    if want in compare["caption"] and compare["rows"] == COMPARE_ROWS:
        return []
    return [f"compare table: {compare}, expected a caption naming {want!r}"]

CHECKS = [
    Check(
        "emitted sources", "static", 4,
        "the page loads the committed CSS and script at its own content hash",
        lambda ctx: emitted_sources(ctx.pages),
    ),
    Check(
        "generated alias", "static", 5,
        "doorbells.html is a small redirect to the canonical index.html",
        lambda ctx: alias_problems(ctx.pages),
    ),
    Check(
        "not found", "static", 52,
        "a mistyped address lands on the site's own 404, not on GitHub's",
        lambda ctx: notfound_check(),
    ),
    Check(
        "phone first paint", "phone", 10, "",
        lambda ctx: phone_first_paint(ctx.phone["first paint"]),
    ),
    Check(
        "phone cost cells", "phone", 11, "",
        lambda ctx: cost_cells(ctx.phone["cost"]),
    ),
    Check(
        "phone short answer", "phone", 24,
        "all three recommendations are on the phone, in their own colours, one or two lines each",
        lambda ctx: short_answer_check(ctx.page),
    ),
    Check(
        "phone table header", "phone", 12,
        "8 column headers stay in the accessibility tree and the sort buttons leave the tab order",
        lambda ctx: phone_header(ctx.phone["header"], ctx.phone["roles"]),
    ),
    Check(
        "mast remit", "phone", 25,
        "the masthead keeps its remit at 390, and the count line says doorbells",
        lambda ctx: mast_remit_check(ctx.page),
    ),
    Check(
        "phone containment", "phone", 20,
        "off-screen phone cards skip layout, with a 445px estimate standing in",
        lambda ctx: contain_check(ctx.page, ctx.row_count),
    ),
    Check(
        "type floor at 390", "phone", 23,
        "no rendered text is below 11px at 390",
        lambda ctx: tiny(ctx.phone["page"], 390),
    ),
    Check(
        "structure at 1280", "compare", 54, "",
        lambda ctx: landmarks_and_ids(ctx.snapshot),
    ),
    Check(
        "verdict tags", "compare", 55,
        'one row owns "Best overall"; the Reolink variants name their own case',
        lambda ctx: verdict_tags(ctx.snapshot),
    ),
    Check(
        "row rule", "compare", 56,
        "the verdict rule is a 3px border, and the box clears it",
        lambda ctx: row_rule(ctx.snapshot),
    ),
    Check(
        "filters row", "compare", 50,
        "every option group reads on one row from 900 up, the sort control keeps its own line below 1280, and the slider takes the spare width",
        lambda ctx: filters_row_check(ctx.page),
    ),
    Check(
        "price cells", "compare", 57, "price cells carry no footnote numbers",
        lambda ctx: price_cells(ctx.snapshot),
    ),
    Check(
        "photo zoom", "compare", 58, "every photo shows a zoom glyph",
        lambda ctx: zoom_images(ctx.snapshot, ctx.lightbox),
    ),
    Check(
        "contact route", "compare", 59, "contact route linked in the header and the method",
        lambda ctx: contact_routes(ctx.snapshot),
    ),
    Check(
        "glossary", "compare", 60, "method defines PoE, NVR, microSD and Home Assistant",
        lambda ctx: [] if ctx.snapshot["hasGlossary"] else [
            "method does not gloss PoE, NVR, microSD and Home Assistant"
        ],
    ),
    Check(
        "share metadata", "compare", 61,
        "favicon, canonical URL and Open Graph title are present",
        lambda ctx: share_meta(ctx.snapshot),
    ),
    Check(
        "secure links", "compare", 62, "every external link uses https",
        lambda ctx: secure_links(ctx.snapshot),
    ),
    Check(
        "image files", "compare", 71, "every local image file exists",
        lambda ctx: image_files(ctx.snapshot),
    ),
    Check(
        "cost header name", "compare", 74,
        "the cost headers are written out at 12px in at most three lines at 1280px, and their letters link to the working",
        lambda ctx: cost_header_check(ctx.page),
    ),
    Check(
        "compare caption", "compare", 75,
        "the compare table is captioned with its model count",
        lambda ctx: compare_caption_check(ctx.page),
    ),
    Check(
        "table name", "compare", 84,
        "the doorbell table has a name, and the skip link says which table it skips",
        lambda ctx: table_name_check(ctx.page),
    ),
    Check(
        "photo names", "compare", 85,
        "two photos on one row are two names, and the details one says it is full size",
        lambda ctx: photo_names_check(ctx.page),
    ),
    Check(
        "compare words", "compare", 86,
        "the comparison names the cost columns as the table does, and every delta names its baseline",
        compare_words_check,
    ),
    Check(
        "compare target", "compare", 87,
        "the compare label is a 44x44 target at 1280 and at 390",
        lambda ctx: compare_target_check(ctx.page),
    ),
    Check(
        "overflow", "compare", 78,
        lambda ctx: "no horizontal overflow at " + ", ".join(f"{w}px" for w in WIDTHS),
        lambda ctx: overflow_check(ctx.page),
    ),
]

