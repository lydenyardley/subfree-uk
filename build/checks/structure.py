"""The shape of the document and of the files the build writes."""
import hashlib
import os

from .behaviour import contain_check
from .compare import COMPARE_ROWS
from .context import ROOT, WIDTHS
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
    html = pages["index.html"]
    problems = []
    for name, link in (("assets/page.css", "href"), ("assets/page.js", "src")):
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            problems.append(f"{name} is missing")
            continue
        text = open(path, encoding="utf-8").read()
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]
        if f'{link}="{name}?v={digest}"' not in html:
            problems.append(f"the page does not load {name}?v={digest}")
    if "<style>" in html:
        problems.append("the page still inlines its stylesheet")
    if "@@DATA@@" in html or "@@CHECKED@@" in html:
        problems.append("a build placeholder leaked into the page")
    return problems

def alias_problems(pages):
    alias = pages["doorbells.html"]
    problems = []
    if 'http-equiv="refresh"' not in alias or "url=./" not in alias:
        problems.append("doorbells.html is not a redirect to ./")
    if len(alias) > 1000:
        problems.append(f"doorbells.html is {len(alias)} bytes; it should be a redirect, not a copy")
    if pages["index.html"] == alias:
        problems.append("index.html and doorbells.html are identical again")
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
    """The filter groups share a line at 1440, and the slider takes the rest.

    The details box used to size itself to its own content, which came up a
    few pixels short of the option groups, so both wrapped and the price
    slider stopped at 178px with half the row unused. Measured at 1440 rather
    than 1280 because 1440 is the width that still has slack for a fallback
    font 15% wider: there the groups are one line each and the slider is
    337px, against 2, 2 and 178px on the old stylesheet.
    """
    problems = []
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(150)
    state = page.evaluate(
        """() => {
            const body = document.querySelector('.fbody');
            const top = (el) => el.getBoundingClientRect().top;
            return {
                rows: Array.from(body.querySelectorAll('.opts')).map(
                    (group) => new Set(Array.from(group.children).map(top)).size
                ),
                slider: Math.round(document.querySelector('.dual').getBoundingClientRect().width)
            };
        }"""
    )
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(120)
    if state["rows"] != [1, 1]:
        problems.append(
            f"at 1440px the option groups read in {state['rows']} rows, expected one each"
        )
    if state["slider"] < 300:
        problems.append(
            f"at 1440px the price slider is {state['slider']}px wide, expected 300 or more"
        )
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


def compare_caption_check(page):
    compare = page.evaluate(
        """() => ({
            caption: (document.querySelector("#cmp-table caption") || {}).textContent || "",
            rows: document.querySelectorAll("#cmp-table tbody tr").length
        })"""
    )
    if "Side-by-side comparison of 3 doorbells" in compare["caption"] and (
        compare["rows"] == COMPARE_ROWS
    ):
        return []
    return [f"compare table: {compare}"]

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
        "phone containment", "phone", 20,
        "off-screen phone cards skip layout, with a 330px estimate standing in",
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
        "the filter groups share a line at 1440 and the price slider takes the spare width",
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
        "overflow", "compare", 78,
        lambda ctx: "no horizontal overflow at " + ", ".join(f"{w}px" for w in WIDTHS),
        lambda ctx: overflow_check(ctx.page),
    ),
]

