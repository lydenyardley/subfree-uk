"""The site: a page per category, its alias, `404.html`, the CSS and the script.

The dataset, its sources and every derived figure are in `rows.py`, which this
module imports. Everything here turns that data into files. Nothing is written
at import time, so an agent can read the page assembly without touching the
working tree; `write()` does all the writing.

A category is a record in `catalog.py`. `build(cat)` renders one, so a second
category is a second record and its rows rather than an edit here.
"""

import base64, csv, hashlib, html, io, json, os, re
from datetime import date
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
HERE = os.path.dirname(os.path.abspath(__file__))

ORIGIN = "https://lydenyardley.github.io"
SITE = "/subfree-uk/"   # where the site is published; the 404 page needs root-relative links
GITHUB = "https://github.com/lydenyardley/subfree-uk"
EMAIL = "lydenyardley+subfreeuk@posteo.net"

from catalog import CATEGORIES, words
from rows import (
    CARD, CHECKED, CHECKED_ISO, FN, MAXP, MINP, MONTHS, POWER_LABEL,
    REC_LABEL, REC_RANK, ROWS, S, SCORE_MAX, SCORE_PARTS, STICK,
    _CHECKED_DATE, money, order, row_problems,
)

# ---------- HTML ----------
e = html.escape
EU_NOTE = "EU price, not a UK quote"


def fn(keys):
    return ", ".join(
        f'<a class="fn" href="#fn{FN[k]}" title="{e(S[k][0])}">{FN[k]}</a>'
        for k in keys
    )


def srclinks(keys):
    """The row's own list of sources, as links to the pages themselves.

    A row names every page its record comes from, so that list leaves for those
    pages rather than for a numbered entry: it works with or without a script,
    and whether or not the register is on screen. `data-fn` still ties each link
    to its entry, which is what the audit counts.
    """
    return ", ".join(
        f'<a class="sref" href="{e(S[k][1])}" data-fn="{FN[k]}" title="{e(S[k][0])}" '
        f'rel="nofollow noopener noreferrer">{e(S[k][0])}</a>'
        for k in keys
    )


def claims(r):
    """What each of the row's figures rests on, as the card needs it.

    `keys` is the pages behind the figure, the first being the one the figure
    links to, and an empty value is dropped: a row with no plan has no plan
    sentence to show. The rest of the card is the row's own words.
    """
    out = {}

    def add(key, *keys, say="", arc="", note=""):
        out[key] = {
            "keys": [k for k in dict.fromkeys(keys) if k],
            "say": say, "arc": arc, "note": note,
        }

    # The sentence is the row's own words for the question the card's title
    # asks, which is not always the field that looks nearest. "Records free
    # without a plan" asks the recording question, so it prints the row's
    # history line; the storage line answers where footage is kept, and read
    # under that title it said "None" for the Nest doorbell, whose figure beside
    # it reads "Only briefly (3 hrs)". Where the sentence and the figure rest on
    # different pages, the card lists both, so the sentence stays checkable
    # where it says it came from.
    add("rec", r["rec_src"], r["history_src"], say=r["history"])
    add("price", r["price_src"], say=r["price_note"])
    # Both 3-year figures are sums, so their card carries the arithmetic and
    # every page it is built from, the sundries included: the doorbell, the hub
    # or recorder the sum adds where it adds one, the card or stick it buys, and
    # the recording that route keeps. Nothing in a sum is a figure the reader
    # has to take on trust.
    add("nosub", r["price_src"], r.get("kit_src", ""), r.get("extra_src", ""),
        r["rec_src"] if r["extra"] else r["history_src"],
        say=r["storage"] if r["extra"] else r["history"], arc=r["maths_free"])
    add("plan", r["plan_src"], r["price_src"] if r["sub"] is not None else "",
        say=r["sub_text"] if r["sub"] is not None else r["storage"],
        arc=r["maths_sub"], note=EU_NOTE if r["plan_region"] == "EU" else "")
    add("history", r["history_src"], say=r["history"])
    add("ha", r["ha_src"], say=r["ha_text"])
    return {k: {f: v for f, v in c.items() if f == "keys" or v} for k, c in out.items()}


def src_label(cl, key, words):
    """The figure's words and the page its card opens, so a screen reader hears
    where the click leads without going there first.

    `words` are the row's own and unescaped: a label is escaped once, in `fig`,
    which is what keeps an apostrophe an apostrophe in the words the reader
    hears rather than its entities.
    """
    return f"{words}, source: {', '.join(S[k][0] for k in cl[key]['keys'])}"


def fig(r, cl, key, text, label, cls="", attrs=""):
    """One figure with its source card on it.

    The anchor is a real link to the page the figure came from, so on paper and
    without a script it still goes where it says it goes; with a script the
    click opens the card instead, and the address is the one the card prints.
    `data-fn` is the register entry the card reads the name and URL from, so a
    URL is in the page once; `data-more` names the second page a total is built
    from. `label` is what the click says it does.
    """
    keys = cl[key]["keys"]
    more = "".join(f" data-more=\"{' '.join(str(FN[k]) for k in keys[1:])}\"" if len(keys) > 1 else "")
    return (f'<a class="src{" " + cls if cls else ""}" href="{e(S[keys[0]][1])}"{more}{attrs}'
            f' data-claim="{key}" data-id="{r["id"]}" data-fn="{FN[keys[0]]}" '
            f'rel="nofollow noopener noreferrer" aria-haspopup="dialog" '
            f'aria-label="{e(label)}">{text}</a>')


# Product photos: manufacturers' own images, processed by make_images.py into img/*.webp; sources in images.json
IMG = json.load(open(os.path.join(HERE, "images.json"), encoding="utf-8"))


def has_photo(r):
    return bool(IMG.get(r["id"], {})) and not IMG.get(r["id"], {}).get("placeholder")


def photo(r, size):
    name = f"{r['brand']} {r['model']}"
    w, h = (45, 60) if size == "sm" else (180, 240)
    m = IMG.get(r["id"], {})
    # The thumbnail sits beside the model name, so it is decorative and must not
    # repeat that name. The large photo is the only name in the details panel.
    if m.get("placeholder") or not m:
        attrs = 'aria-hidden="true"' if size == "sm" else f'role="img" aria-label="No photo available for {e(name)}"'
        return f'<span class="ph ph-{size}" {attrs} style="width:{w}px;height:{h}px"><span>No photo</span></span>'
    alt = "" if size == "sm" else e(name)
    return f'<img class="ph ph-{size}" src="img/{r["id"]}-{size}.webp" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{alt}">'


def zoom(r, size):
    # Both sizes are 2x files, so the lightbox shows the large one at its own
    # width. Placeholders stay plain: there is nothing bigger to open.
    m = IMG.get(r["id"], {})
    if m.get("placeholder") or not m:
        return photo(r, size)
    name = e(f"{r['brand']} {r['model']}")
    # Two photos on one row, so the two names say which one opens: the row's
    # thumbnail sits beside the name, the large one only inside the details.
    # Both open the full-size photo, so neither name claims to open a thumbnail.
    which = "photo" if size == "sm" else "photo full size"
    return (f'<button type="button" class="zoom" data-full="img/{r["id"]}-lg.webp" data-name="{name}" '
            f'aria-label="View {name} {which}">{photo(r, size)}<span class="zi" aria-hidden="true"></span></button>')


def vlink(ids, text):
    return f'<a class="jump" href="#m-{ids[0]}" data-ids="{" ".join(ids)}">{text}</a>'


ROW_FIG = re.compile(r"\{([pc]):([a-z0-9-]+)\}")
BY_ID = {r["id"]: r for r in ROWS}
ROW_LINK = re.compile(r"\{v:([a-z0-9-]+):([^}]+)\}")


def with_links(text):
    """`{v:ID:Words}` becomes a link to that row, so the editorial lead can
    name a product without the record holding markup for a specific id."""
    text = ROW_FIG.sub(lambda m: f"£{round(BY_ID[m.group(2)]['price' if m.group(1) == 'p' else 'nosub3']):,}", text)
    return ROW_LINK.sub(lambda m: vlink([m.group(1)], m.group(2)), text)


# The first row with the headline verdict is the page's recommendation, so its
# photo is the social preview: a renamed or removed row cannot leave the page
# claiming a picture it no longer recommends.
def hero(rows, cat):
    for r in rows:
        if r.get("verdict") == cat["headline"] and has_photo(r):
            return r
    for r in rows:
        if has_photo(r):
            return r
    return rows[0]


def kit_phrase(rows):
    """The add-on hardware the no-plan sums buy, each at the row's own price.

    `kit_price` is authored beside the row and checked against its `extra`, so
    the note prints a cited figure rather than one recovered by subtraction.
    """
    parts = []
    for r in rows:
        if not r.get("kit_src"):
            continue
        parts.append((r["brand"], f"{r['brand']}'s {r['kit_label']} at {money(r['kit_price'])}"))
    named = [text for _, text in sorted(parts, key=lambda pair: pair[0])]
    if not named:
        return ""
    # The sentence reads "Blink's Sync Module 2 at £39.99, Arlo's SmartHub at
    # £105.07, and a 64 GB card at £25.37 or a stick at £11.99".
    return ", ".join(named) + ", and "


def page_css():
    return open(os.path.join(HERE, "page.css"), encoding="utf-8").read()


def script_hash(js):
    return base64.b64encode(hashlib.sha256(js.encode("utf-8")).digest()).decode()


# The two inline scripts, kept as values so the policy can hash exactly what
# ships. Both have to be inline: the first runs before the stylesheet paints,
# and the second is the width query a phone needs before the first frame.
THEME_JS = ('document.documentElement.className="js";try{var t=localStorage.getItem("theme");'
            'if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}catch(e){}')
NARROW_JS = "if(window.matchMedia('(max-width:520px)').matches)document.getElementById('filters').open=false;"

# No third-party code is the page's promise, so the policy makes it enforceable.
# A meta policy is the only kind GitHub Pages allows, and it cannot carry
# frame-ancestors. `style-src` allows inline styles because the page positions
# the photo placeholders, the score bars and the price fill that way.
def policy():
    return (
        "default-src 'self'; "
        f"script-src 'self' 'sha256-{script_hash(THEME_JS)}' 'sha256-{script_hash(NARROW_JS)}'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self'; font-src 'self'; "
        "connect-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'"
    )


def content_version(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


# The sort indicator is drawn by the stylesheet, so the button keeps its word
# as its name and the mark carries no text of its own.
SI = '<span class="si" aria-hidden="true"></span>'

CSS_FILE, JS_FILE = "assets/page.css", "assets/page.js"


def md_cell(text):
    """One Markdown table cell: a pipe in the copy would add a column."""
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def build(cat):
    """Every file one category owns, as `{filename: text}`, plus its data rows."""
    cat = words(cat)
    rows = cat["rows"]
    n = len(rows)
    period, padj = cat["period"], cat["period_adj"]
    # A nested route needs the assets one level up; the root needs them plain.
    prefix = "../" * cat["route"].count("/")
    score_max = SCORE_MAX
    claims_by_id = {r["id"]: claims(r) for r in rows}

    rows_html = []
    for i, r in enumerate(rows):
        pw = " ".join(r["power"])
        sc = r["score_total"]
        tone = cat["verdicts"][r["verdict"]][1] if r["verdict"] else ""
        vattr = f' data-v="{tone}"' if tone else ""
        vtag = f'<span class="vtag v-{tone}">{cat["verdicts"][r["verdict"]][0]}</span>' if r["verdict"] else ""
        unv = f'<p class="unverified"><b>Not yet verified:</b> {e(r["unverified"])}</p>' if r["unverified"] else ""
        pnote = '. ' + e(r["power_note"]) if r.get("power_note") else ""
        cl = claims_by_id[r["id"]]
        # The price is the link to the page the price came from, so the promise
        # in the intro ("each one links to its source") is kept in the row
        # itself; with a script that click opens the price's card, which prints
        # the same address.
        pm = money(r["price"], None)
        psrc = S[r["price_src"]]
        price = fig(r, cl, "price", pm, f'{pm} at {psrc[0]}', cls="buy",
                    attrs=f' title="Check the price at {e(psrc[0])}"')
        # Each figure a reader might doubt carries its own card. The words are
        # the same ones the cell shows, so the card cannot drift from the figure.
        rec_lbl = REC_LABEL[r["rec"]]
        rec_fig = fig(r, cl, "rec", f'<span class="rec-t">{rec_lbl}</span>', src_label(cl, "rec", rec_lbl))
        nosub_words = money(r["nosub3"], None)
        nosub_fig = fig(r, cl, "nosub", nosub_words, src_label(cl, "nosub", nosub_words))
        sub_words = money(r["sub3"], None) if r["sub3"] is not None else "No plan"
        sub_fig = fig(r, cl, "plan", sub_words if r["sub3"] is not None else f'<span class="noplan">{sub_words}</span>',
                      src_label(cl, "plan", sub_words))
        hist_fig = fig(r, cl, "history", e(r["history"]), src_label(cl, "history", r["history"]))
        ha_fig = fig(r, cl, "ha", e(r["ha_text"]), src_label(cl, "ha", r["ha_text"]))
        plan_fig = fig(r, cl, "plan", e(r["sub_text"]), src_label(cl, "plan", r["sub_text"]))
        ncls = " keep" if r["keep_basis"] == "nosub" else ""
        scls = " keep" if r["keep_basis"] == "sub" else ""
        # The bold figure follows the sort. The default sort is the 3-year cost
        # to keep recordings, so the cell that figure comes from starts bold, and
        # the sort note says so. Where the plan is the cheapest way to record,
        # the cell says so too, or the bold number reads as the wrong figure.
        knote = '<span class="note">cheapest for this model: with plan</span>' if r["keep_basis"] == "sub" else ""
        rows_html.append(f'''<tbody class="item" id="m-{r['id']}" data-id="{r['id']}" data-keep="{r['keep_basis']}"{vattr} data-rec="{r['rec']}" data-recv="{REC_RANK[r['rec']]}" data-ha="{r['ha']}" data-power="{pw}" data-price="{r['price']}" data-keep3="{r['keep3']}" data-nosub3="{r['nosub3']}" data-sub3="{r['sub3'] if r['sub3'] is not None else 0}" data-score="{sc}" data-region="{r['plan_region']}" data-model="{e((r['brand']+' '+r['model']).lower())}" data-idx="{i}">
<tr class="main">
<td class="c-cmp"><label class="cmp-w"><input type="checkbox" class="cmp" value="{r['id']}" aria-label="Compare {e(r['brand'])} {e(r['model'])}"><span class="cmp-cap" aria-hidden="true">Compare</span></label></td>
<th scope="row" class="c-model"><div class="mcell">{zoom(r,"sm")}<div><span class="brand">{e(r['brand'])}</span> <span class="mname">{e(r['model'])}</span>{vtag}<span class="best">Best for: {e(r['best'])}</span></div></div></th>
<td class="c-rec" data-label="Records free?"><span class="rec rec-{r['rec']}">{rec_fig}{fn([r['rec_src']])}</span></td>
<td class="c-price num" data-label="Price">{price}</td>
<td class="c-score" data-label="Free features"><span class="score"><b>{sc}</b>/{score_max}</span><span class="bar" aria-hidden="true"><i style="transform:scaleX({sc/score_max:.3f})"></i></span></td>
<td class="c-nosub num{ncls}" data-label="{padj} cost, no plan"><span class="figv">{nosub_fig}{'' if r['free_records'] else '<span class="note">no recordings</span>' if r['rec']=='no' else '<span class="note">3 hrs history</span>'}</span></td>
<td class="c-sub num{scls}" data-label="{padj} cost, with plan" data-region="{r['plan_region']}"><span class="figv">{sub_fig}{knote}{f'<span class="vh">{EU_NOTE}</span>' if r['plan_region'] == 'EU' else ''}</span></td>
<td class="c-catch" data-label="Main catch"><span class="catch-t">{e(r['catch'])}</span><div class="more-w"><button type="button" class="more" aria-expanded="false" aria-controls="d-{r['id']}"><span class="more-t">Costs &amp; sources</span></button></div></td>
</tr>
<tr class="detail" id="d-{r['id']}"><td colspan="8"><div class="dgrid">
<figure class="dimg">{zoom(r,"lg")}
<p class="srcs">Sources: {srclinks(r['src'])}</p></figure>
<dl class="dspec">
<div class="pair"><dt>Power</dt><dd>{e(r['plain'][0])}{pnote}</dd></div>
<div class="pair"><dt>Wi-Fi</dt><dd>{e(r['wifi'])}</dd></div>
<div class="pair"><dt>Storage</dt><dd>{e(r['plain'][1])}</dd></div>
<div class="pair"><dt>Live view</dt><dd>{e(r['live'])}</dd></div>
<div class="pair"><dt>Motion alerts</dt><dd>{e(r['alerts'])}</dd></div>
<div class="pair"><dt>Smart detection</dt><dd>{e(r['ai'])}</dd></div>
<div class="pair"><dt>History without a plan</dt><dd>{hist_fig} {fn([r['history_src']])}</dd></div>
<div class="pair"><dt>Behind the paywall</dt><dd>{e(r['paywalled'])}</dd></div>
<div class="pair"><dt>Plans</dt><dd>{plan_fig}</dd></div>
<div class="pair"><dt>Home Assistant</dt><dd>{ha_fig} {fn([r['ha_src']])}</dd></div>
<div class="pair"><dt>{period}, no plan</dt><dd class="maths">{e(r['maths_free'])}</dd></div>
<div class="pair"><dt>{period}, with plan</dt><dd class="maths">{e(r['maths_sub'])}</dd></div>
<div class="pair"><dt>Score breakdown</dt><dd>{"; ".join(f"{lbl} {r['score'][k]}/{mx}" for k, lbl, mx in SCORE_PARTS)}</dd></div>
</dl></div>
{unv}
</td></tr>
</tbody>''')

    data_js = json.dumps({r["id"]: {
        "name": f"{r['brand']} {r['model']}", "rec": REC_LABEL[r["rec"]], "recCls": r["rec"],
        "price": money(r["price"], None), "score": f"{r['score_total']}/{score_max}",
        "tone": cat["verdicts"][r["verdict"]][1] if r["verdict"] else "",
        "vtag": cat["verdicts"][r["verdict"]][0] if r["verdict"] else "",
        "nosub3": money(r["nosub3"], None),
        "sub3": money(r["sub3"], None) if r["sub3"] is not None else "No plan",
        "keep3": r["keep3"], "keepNote": r["keep_note"], "region": r["plan_region"],
        "best": r["best"], "catch": r["catch"], "power": " / ".join(POWER_LABEL[p] for p in r["power"]),
        "storage": r["storage"], "live": r["live"], "alerts": r["alerts"], "ai": r["ai"],
        "history": r["history"], "paywalled": r["paywalled"],
        "plan": r["sub_text"], "ha": r["ha_text"], "wifi": r["wifi"],
        "claims": {k: {f: v for f, v in c.items() if f != "keys"} for k, c in claims_by_id[r["id"]].items()},
        "img": "" if not has_photo(r) else f'img/{r["id"]}-sm.webp',
        "imgLg": "" if not has_photo(r) else f'img/{r["id"]}-lg.webp',
    } for r in rows}, ensure_ascii=False)

    # What the script needs to speak the category's words and read the record's
    # tables. A page carries only its own category, so a second page cannot
    # borrow the first one's vocabulary.
    js_cat = {
        "noun": cat["noun"], "nouns": cat["nouns"],
        "period": period, "periodAdj": padj, "months": MONTHS,
        "cap": cat["cap"], "scoreMax": score_max,
        "compare": [[label, key] for label, key in cat["compare"]],
        "pin": cat["pin"],
        "sortNotes": {key: note for key, _, note in cat["sort"]},
        "defaultSort": cat["sort"][0][0],
        "claims": {k: v.format(period=period, period_adj=padj) for k, v in cat["claims"].items()},
        "shown": cat["shown"], "noMatch": cat["no_match"], "empty": cat["empty_line"],
        "cmpCaption": cat["cmp_caption"],
    }

    page_js = (open(os.path.join(HERE, "page.js"), encoding="utf-8").read()
               .replace("/*@@DATA@@*/{}", data_js)
               .replace("/*@@CAT@@*/{}", json.dumps(js_cat, ensure_ascii=False))
               .replace("@@CHECKED@@", CHECKED))
    page_css_text = page_css()
    css_url = f"{prefix}{CSS_FILE}?v={content_version(page_css_text)}"
    js_url = f"{prefix}{JS_FILE}?v={content_version(page_js)}"

    # 52 numbered lines are hard to scan, so the list is grouped by the host the
    # link points at. Real <li value> keeps every footnote number stable.
    HOST_PREFIX = {"www", "en", "en-uk", "uk", "eu", "us", "store", "cloud", "support", "blog"}

    def src_host(url):
        parts = urlparse(url).netloc.lower().split(".")
        while len(parts) > 2 and parts[0] in HOST_PREFIX:
            parts = parts[1:]
        return ".".join(parts)

    groups = {}
    for k in order:
        groups.setdefault(src_host(S[k][1]), []).append(k)
    fn_list = "".join(
        f'<section class="fns-g"><h3>{e(host)}</h3><ol class="fns">'
        + "".join(f'<li id="fn{FN[k]}" value="{FN[k]}"><a href="{e(S[k][1])}" rel="nofollow noopener noreferrer">{e(S[k][0])}</a></li>' for k in keys)
        + '</ol></section>'
        for host, keys in sorted(groups.items(), key=lambda kv: FN[kv[1][0]]))

    photo_credits = ", ".join(f'<a href="{e(IMG[r["id"]]["page"])}" rel="nofollow noopener noreferrer">{e(r["brand"])} {e(r["model"])}</a>' for r in rows if has_photo(r))
    no_photo = ", ".join(f'{e(r["brand"])} {e(r["model"])}' for r in rows if not has_photo(r))
    missing = f" No reliable official photo for: {no_photo}." if no_photo else ""

    def method(key, **extra):
        return cat["method"][key].format(
            period=period, period_adj=padj, months=MONTHS, score_max=score_max,
            card=money(CARD), stick=money(STICK), **extra,
        )

    sort_options = "".join(
        f'<option value="{key}"{" selected" if i == 0 else ""}>{e(label)}</option>'
        for i, (key, label, _) in enumerate(cat["sort"])
    )
    default_note = cat["sort"][0][2]

    # The short answer is the category's own: three linked sentences, each
    # naming the row it is about.
    short_html = (
        f'<p class="vshort"><b class="vlab">{e(cat["short_head"])}</b>\n'
        + "".join(
            f'<span class="v-{tone}">{with_links(sentence)}</span>\n'
            for tone, sentence in zip(cat["short_tones"], cat["short"])
        )
        + "</p>"
    )
    aside_html = (
        f'<aside class="verdict">\n<h2>{e(cat["short_head"])}</h2>\n'
        + "".join(
            f'<p class="v-{tone}"><b>{e(head)}</b> {with_links(link + rest)}</p>\n'
            for tone, head, link, rest in cat["aside"]
        )
        + "</aside>"
    )

    canonical = f"{ORIGIN}{SITE}{cat['route']}"
    preview = hero(rows, cat)
    preview_img = f"{ORIGIN}{SITE}img/{preview['id']}-lg.webp" if has_photo(preview) else f"{ORIGIN}{SITE}favicon.svg"
    preview_alt = f"{preview['brand']} {preview['model']}" if has_photo(preview) else cat["title"]

    nav = ""
    if len(CATEGORIES) > 1:
        nav = '<nav class="cats" aria-label="Categories">' + "".join(
            f'<a href="{prefix}{other["route"]}"{" aria-current=\"page\"" if other["slug"] == cat["slug"] else ""}>{e(other["nouns"].capitalize())}</a>'
            for other in CATEGORIES
        ) + "</nav>"

    kit = kit_phrase(rows)
    page = f'''<!doctype html>
<html lang="en-GB" class="no-js"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="light dark">
<meta http-equiv="Content-Security-Policy" content="{policy()}">
<title>{cat["title"]} | SubFree UK</title>
<meta name="description" content="{cat["description"].format(n=n)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{cat["title"]}">
<meta property="og:description" content="{cat["description"].format(n=n)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{preview_img}">
<meta property="og:image:alt" content="{e(preview_alt)}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<script>{THEME_JS}</script>
<link rel="stylesheet" href="{css_url}">
</head><body>
<a class="skip" href="#tbl">{cat["skip"]}</a>
<div class="wrap">
<header class="mast-head">
<div class="mast" id="top"><div>SubFree UK <span class="mast-long">{cat["mast_long"]}</span><span class="mast-short">{cat["mast"]}</span></div>{nav}<button type="button" id="theme"><i aria-hidden="true"></i><span class="t-dark">Dark mode</span><span class="t-light">Light mode</span></button></div>
<div class="intro">
<div>
<h1>{cat["h1"]}</h1>
<p class="dek">{cat["dek"].format(n=n, period=padj)}</p>
<p class="meta"><b>Last checked {CHECKED}.</b> No affiliate links, no tracking, no cookies. Spotted a mistake? <a href="{GITHUB}/issues/new">Open an issue</a>.</p>
{short_html}</div>
{aside_html}</div>
</header>

<main>
<p class="vh" id="live" role="status"></p>
<form class="controls" id="controls">
<details class="filters" id="filters" open>
<summary>Filters</summary>
<div class="fbody">
<fieldset><legend>Show only</legend><div class="opts">
{chr(10).join(f'<label><input type="checkbox" id="{id_}"> {e(label)}</label>' for id_, label in cat["filters"])}
</div></fieldset>
<fieldset><legend>Power</legend><div class="opts">
{chr(10).join(f'<label><input type="checkbox" class="f-pw" value="{key}"> {e(label)}</label>' for key, label in cat["powers"])}
</div><p class="hint">{e(cat["power_hint"])}</p></fieldset>
<fieldset class="range"><legend>Price</legend>
<div class="dual">
<div class="dual-track" aria-hidden="true"><i id="f-fill"></i></div>
<input type="range" id="f-min" min="{MINP}" max="{MAXP}" step="5" value="{MINP}" aria-label="Lowest price" aria-valuetext="£{MINP}" aria-describedby="f-min-out f-max-out">
<input type="range" id="f-max" min="{MINP}" max="{MAXP}" step="5" value="{MAXP}" aria-label="Highest price" aria-valuetext="£{MAXP}" aria-describedby="f-min-out f-max-out">
</div>
<div class="dual-vals"><output id="f-min-out" for="f-min">£{MINP}</output><output id="f-max-out" for="f-max">£{MAXP}</output></div>
</fieldset>
</div>
</details>
<div class="sortby"><label class="lab" for="sort">Sort by</label><select id="sort">{sort_options}</select><p class="sortnote" id="sortnote">{e(default_note)}</p></div>
<p class="count">{cat["count_line"].format(cap=cat["cap"], nouns=cat["nouns"])} <span id="count">{n}</span> of {n} shown · <button type="button" class="link" id="reset">Reset</button><span id="cmp-sep" hidden> · </span><button type="button" class="link" id="cmp-inline" hidden>Compare</button><span id="cmp-cap" class="cap" hidden></span></p>
</form>
<noscript><p class="nojs">Filters, sorting and compare need JavaScript. All {n} {cat["nouns"]} are listed below, with each model's costs and sources open.</p></noscript>
<script>{NARROW_JS}</script>

<section id="compare" hidden>
<div class="cmp-head"><h2 id="cmp-h" tabindex="-1">Side by side</h2><div class="cmp-actions"><label class="cmpo" id="cmp-diff-w" hidden><input type="checkbox" id="cmp-diff"> Differences only <span id="cmp-dupes"></span></label><span class="cmp-links"><button type="button" class="link" id="cmp-copy">Copy shortlist</button><button type="button" class="link" id="cmp-clear">Clear</button><button type="button" class="link" id="cmp-close">Close</button></span></div></div>
<p class="cmp-note" id="cmp-note" role="status" hidden></p>
<p class="cmp-cue" id="cmp-cue" hidden></p>
<div class="cmp-wrap"><div class="cmp-scroll" tabindex="0" role="region" aria-label="Comparison table, scrolls sideways"><table class="cmp-t" id="cmp-table"></table></div></div>
</section>

<div id="totop-s" aria-hidden="true"></div>
<div class="tbl-w"><div class="prog" aria-hidden="true"><i></i></div>
<table class="main-t" id="tbl" tabindex="-1">
<caption class="vh">{cat["table_caption"].format(table_name=cat["table_name"], n=n)}</caption>
<thead><tr>
<th scope="col" class="c-cmp"><span class="vh">Compare</span><svg class="cmp-i" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><rect x="1.75" y="1.75" width="16.5" height="16.5" rx="2"/><path d="M5.5 10.4l3.1 3.1 5.9-6.3"/></svg></th>
<th scope="col" data-sort="model" aria-sort="none"><button type="button">Model{SI}</button></th><th scope="col" data-sort="recv" aria-sort="none"><button type="button">Records free?{SI}</button></th><th scope="col" class="num" data-sort="price" aria-sort="none"><button type="button">Price{SI}</button></th><th scope="col" data-sort="score" aria-sort="none"><button type="button">Free features{SI}</button></th>
<th scope="col" class="num" data-sort="nosub3" aria-sort="none"><button type="button" aria-label="{padj} cost, no plan, footnote a">{padj} cost, no plan{SI}</button><a class="mk" href="#m-a" aria-label="How the {padj} cost without a plan is worked out">a</a></th><th scope="col" class="num" data-sort="sub3" aria-sort="none"><button type="button" aria-label="{padj} cost, with plan, footnote b">{padj} cost, with plan{SI}</button><a class="mk" href="#m-b" aria-label="How the {padj} cost with a plan is worked out">b</a></th><th scope="col">Main catch</th>
</tr></thead>
{''.join(rows_html)}
</table></div>
<p class="empty" id="empty" hidden><span id="empty-txt">{cat["empty_line"]}</span> <span class="empty-acts"><button type="button" class="link" id="near" hidden></button> <button type="button" class="link" id="empty-reset">Reset filters</button></span></p>

<section class="method" id="method">
<div class="method-copy">
<h2>How we worked it out</h2>
<p id="m-a">{method("no_plan", kit=kit+"a 64 GB SanDisk microSD card at " + money(CARD) + " or SanDisk USB stick at " + money(STICK))}</p>
<p id="m-b">{method("with_plan")}</p>
<p>{method("score")}</p>
<p>{method("terms")}</p>
<p>{method("left_out")}</p>
<p>{method("photos", credits=photo_credits, missing=missing)}</p>
</div>
<details class="srcs" id="sources" open><summary><h2 class="srcs-t">Sources <span class="srcs-n">{len(order)} links</span></h2></summary><div class="fns-wrap">{fn_list}</div></details>
</section>
<footer class="foot">
<p>Last checked {CHECKED}. {n} UK {cat["nouns"]}, no affiliate links, no tracking. <a href="{GITHUB}/issues/new">Open an issue</a> · <a href="#tbl">Back to the table</a> · <a href="#top">Back to top</a>.</p>
<p>SubFree UK is a personal comparison of UK {cat["nouns"]}, put together by <a href="{GITHUB}">lydenyardley</a> to show which ones record without a subscription. Every price links to the page it came from, so you can check it yourself. Spotted a mistake? <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
</footer>
</main>
</div>
<div class="tray" id="tray" hidden role="region" aria-label="Compare selection"><span id="tray-txt"></span><button type="button" id="tray-go">Compare</button><button type="button" class="ghost" id="tray-clear">Clear</button></div>
<div class="totop-w" role="region" aria-label="Page tools"><button type="button" class="totop" id="totop" hidden aria-label="Back to top"><span aria-hidden="true">↑</span></button></div>
<dialog id="lightbox" aria-labelledby="lb-name">
<button type="button" class="lb-x" id="lb-x" aria-label="Close photo">✕</button>
<div id="lb-img"></div>
<div class="lb-bar"><span id="lb-name"></span><button type="button" class="link" id="lb-close">Close</button></div>
</dialog>
<dialog id="card" aria-labelledby="card-h">
<button type="button" class="lb-x" id="card-x" aria-label="Close source card">✕</button>
<h2 id="card-h"></h2>
<p class="card-say"></p>
<p class="card-arc"></p>
<p class="card-srcs"></p>
<p class="card-note"></p>
<p class="card-date">Prices and plans checked {CHECKED}.</p>
</dialog>
<script src="{js_url}"></script>
</body></html>'''
    # One page, one name. The second filename used to be a byte-identical copy;
    # it is now a redirect so an old link still lands on the canonical URL.
    alias = f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>Moved: the {cat["table_name"].lower()}</title>
<link rel="canonical" href="{canonical}">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=./">
</head><body><p>This page has moved to the <a href="./">UK {cat["noun"]} comparison</a>.</p></body></html>'''

    md = [cat['md_head'][0] + "\n",
          cat["md_head"][1].format(checked=CHECKED, n=n) + "\n",
          cat["md_head"][2].format(score_max=score_max, period_short=cat["period_short"]),
          "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: r["keep3"]):
        md.append(
            f"| {md_cell(r['brand'])} {md_cell(r['model'])} | {md_cell(REC_LABEL[r['rec']])} | "
            f"[{money(r['price'])}]({S[r['price_src']][1]}) | {r['score_total']} | "
            f"{money(r['nosub3'])} | {money(r['sub3']) if r['sub3'] else '—'} | "
            f"{md_cell(r['best'])} | {md_cell(r['catch'])} |"
        )
    md.append("\n## Detail\n")
    for r in rows:
        md += [f"### {r['brand']} {r['model']}", f"- **Best for:** {r['best']}", f"- **Main catch:** {r['catch']}",
               f"- **Price:** {money(r['price'])} ({r['price_note']})",
               f"- **{padj} cost, no plan:** {r['maths_free']}", f"- **{padj} cost, with plan:** {r['maths_sub']}",
               f"- **Storage:** {r['storage']}", f"- **Free:** live view {r['live'].lower()}; alerts {r['alerts'].lower()}; smart detection: {r['ai']}",
               f"- **History without plan:** {r['history']}", f"- **Paywalled:** {r['paywalled']}", f"- **Plans:** {r['sub_text']}",
               f"- **Home Assistant:** {r['ha_text']}", *([f"- **Unverified:** {r['unverified']}"] if r["unverified"] else []),
               "- **Sources:** " + " · ".join(f"[{S[k][0]}]({S[k][1]})" for k in r["src"]), ""]
    md += ["## How the " + padj + " costs are worked out"] + [
        "- " + line.format(card=money(CARD), stick=money(STICK), months=MONTHS)
        for line in cat["method"]["md"]
    ]

    return {
        cat["page"]: page,
        cat["alias"]: alias,
        cat["csv"]: csv_text(rows, cat),
        cat["md"]: "\n".join(md),
        CSS_FILE: page_css_text,
        JS_FILE: page_js,
    }, page_js, page_css_text


def csv_text(rows, cat):
    """The CSV a reader can open, one row per product, every figure with its page."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([head.format(score_max=SCORE_MAX) for head in cat["csv_head"]])
    for r in rows:
        w.writerow([r["brand"], r["model"], REC_LABEL[r["rec"]], "/".join(POWER_LABEL[p] for p in r["power"]), f"{r['price']:.2f}", r["price_note"], S[r["price_src"]][1],
                    r["best"], r["catch"], r["score_total"], f"{r['nosub3']:.2f}", "" if r["sub3"] is None else f"{r['sub3']:.2f}", f"{r['keep3']:.2f}", r["maths_free"], r["maths_sub"],
                    r["storage"], r["live"], r["alerts"], r["ai"], r["history"], r["paywalled"], r["sub_text"], r["plan_region"], r["ha_text"], r["wifi"],
                    " ; ".join(S[k][1] for k in r["src"]), r["unverified"], CHECKED])
    return out.getvalue()


def not_found(cats):
    """A mistyped link should land on the site's own page, not on a hosting
    company's. GitHub Pages serves this file for any path it cannot find, so
    the links in it are root-relative and work at any depth."""
    copy = cats[0]["not_found"]
    links = "".join(f'<a class="nf-btn" href="{SITE}{cat["route"]}">{e(cat["h1"])}</a>' for cat in cats)
    return f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<title>{copy["title"]}</title>
<meta name="description" content="{e(copy["description"])}">
<link rel="stylesheet" href="{SITE}assets/page.css?v={content_version(page_css())}">
</head><body>
<div class="wrap">
<header class="mast-head"><div class="mast"><div>SubFree UK <span class="mast-long">{e(cats[0]["mast_long"])}</span><span class="mast-short">{e(cats[0]["mast"])}</span></div></div></header>
<main class="nf">
<h1>{copy["h1"]}</h1>
<p>{e(copy["say"].format(what=copy["what"]))}</p>
{links}
</main>
</div>
</body></html>'''


def write():
    problems = []
    for cat in CATEGORIES:
        if not cat.get("rows"):
            problems.append(f"{cat['slug']}: the category has no rows attached")
            continue
        problems.extend(row_problems(cat))
    if problems:
        raise SystemExit("Row problems:\n  " + "\n  ".join(problems))
    if _CHECKED_DATE > date.today():
        raise SystemExit(
            f"CHECKED_ISO is {CHECKED_ISO}, which is in the future; fix the date before building"
        )
    for cat in CATEGORIES:
        files, _, _ = build(cat)
        for name, text in files.items():
            path = os.path.join(ROOT, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", newline="", encoding="utf-8") as handle:
                handle.write(text)
    not_found_path = os.path.join(ROOT, "404.html")
    with open(not_found_path, "w", encoding="utf-8") as handle:
        handle.write(not_found([words(c) for c in CATEGORIES]))
    # The one-off content-hashed names from the first version of this change.
    assets = os.path.join(ROOT, "assets")
    for name in os.listdir(assets):
        if name.startswith("page-") and name.endswith((".css", ".js")):
            os.remove(os.path.join(assets, name))

    print(len(ROWS), "rows written")
    for r in sorted(ROWS, key=lambda r: r["keep3"]): print(f"{r['brand']:14} {r['model']:38} score {r['score_total']}  nosub {r['nosub3']:8.2f}  sub {r['sub3'] if r['sub3'] else '-':>8}  keep {r['keep3']:.2f}")
    open_rows = [r for r in ROWS if r["unverified"]]
    print(f"\nUnverified ({len(open_rows)} of {len(ROWS)} rows):" + (" none" if not open_rows else ""))
    for r in open_rows: print(f"  {r['brand']} {r['model']}: {r['unverified'].replace('£','GBP ')}")


if __name__ == "__main__":
    write()
