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

from catalog import CATEGORIES, CSV_KEYS, words
from rows import (
    CARD, DATASETS, ROWS, S, SPONSORED, STICK, authored_problems, money,
    row_problems,
)

# ---------- HTML ----------
e = html.escape


def rel(url):
    """A paid link says so to search engines; every other link keeps no referrer.

    Which pages are paid is the data's answer, not a pattern over the address:
    `rows.py` builds the set where it tags the links, so an Awin click and an
    Amazon tag are both marked and a new network is one entry there.
    """
    return "sponsored nofollow noopener" if url in SPONSORED else "nofollow noopener noreferrer"
EU_NOTE = "EU price, not a UK quote"


def fn(ds, keys):
    return ", ".join(
        f'<a class="fn" href="#fn{ds.FN[k]}" title="{e(ds.S[k][0])}">{ds.FN[k]}</a>'
        for k in keys
    )


def srclinks(ds, keys):
    """The row's own list of sources, as links to the pages themselves.

    A row names every page its record comes from, so that list leaves for those
    pages rather than for a numbered entry: it works with or without a script,
    and whether or not the register is on screen. `data-fn` still ties each link
    to its entry, which is what the audit counts.
    """
    return ", ".join(
        f'<a class="sref" href="{e(ds.S[k][1])}" data-fn="{ds.FN[k]}" title="{e(ds.S[k][0])}" '
        f'rel="{rel(ds.S[k][1])}">{e(ds.S[k][0])}</a>'
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
        say=r.get("nosub_say") or (r["storage"] if r["extra"] else r["history"]),
        arc=r["maths_free"])
    add("plan", r["plan_src"], r["price_src"] if r["sub"] is not None else "",
        say=r.get("plan_say") or (
            r["sub_text"] if r["sub"] is not None else r["storage"]
        ),
        arc=r["maths_sub"], note=EU_NOTE if r["plan_region"] == "EU" else "")
    add("history", r["history_src"], say=r["history"])
    add("ha", r["ha_src"], say=r["ha_text"])
    return {k: {f: v for f, v in c.items() if f == "keys" or v} for k, c in out.items()}


def src_label(ds, cl, key, words):
    """The figure's words and the page its card opens, so a screen reader hears
    where the click leads without going there first.

    `words` are the row's own and unescaped: a label is escaped once, in `fig`,
    which is what keeps an apostrophe an apostrophe in the words the reader
    hears rather than its entities.
    """
    return f"{words}, source: {', '.join(ds.S[k][0] for k in cl[key]['keys'])}"


def fig(ds, r, cl, key, text, label, cls="", attrs=""):
    """One figure with its source card on it.

    The anchor is a real link to the page the figure came from, so on paper and
    without a script it still goes where it says it goes; with a script the
    click opens the card instead, and the address is the one the card prints.
    `data-fn` is the register entry the card reads the name and URL from, so a
    URL is in the page once; `data-more` names the second page a total is built
    from. `label` is what the click says it does.
    """
    keys = cl[key]["keys"]
    more = "".join(f" data-more=\"{' '.join(str(ds.FN[k]) for k in keys[1:])}\"" if len(keys) > 1 else "")
    return (f'<a class="src{" " + cls if cls else ""}" href="{e(ds.S[keys[0]][1])}"{more}{attrs}'
            f' data-claim="{key}" data-id="{r["id"]}" data-fn="{ds.FN[keys[0]]}" '
            f'rel="{rel(ds.S[keys[0]][1])}" aria-haspopup="dialog" '
            f'aria-label="{e(label)}">{text}</a>')


# Product photos: manufacturers' own images, processed by make_images.py into img/*.webp; sources in images.json
IMG = json.load(open(os.path.join(HERE, "images.json"), encoding="utf-8"))


def has_photo(r):
    return bool(IMG.get(r["id"], {})) and not IMG.get(r["id"], {}).get("placeholder")


def photo(r, size, prefix=""):
    name = f"{r['brand']} {r['model']}"
    w, h = (45, 60) if size == "sm" else (180, 240)
    m = IMG.get(r["id"], {})
    # The thumbnail sits beside the model name, so it is decorative and must not
    # repeat that name. The large photo is the only name in the details panel.
    if m.get("placeholder") or not m:
        attrs = 'aria-hidden="true"' if size == "sm" else f'role="img" aria-label="No photo available for {e(name)}"'
        return f'<span class="ph ph-{size}" {attrs} style="width:{w}px;height:{h}px"><span>No photo</span></span>'
    alt = "" if size == "sm" else e(name)
    return f'<img class="ph ph-{size}" src="{prefix}img/{r["id"]}-{size}.webp" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{alt}">'


def zoom(r, size, prefix=""):
    # Both sizes are 2x files, so the lightbox shows the large one at its own
    # width. Placeholders stay plain: there is nothing bigger to open.
    m = IMG.get(r["id"], {})
    if m.get("placeholder") or not m:
        return photo(r, size, prefix)
    name = e(f"{r['brand']} {r['model']}")
    # Two photos on one row, so the two names say which one opens: the row's
    # thumbnail sits beside the name, the large one only inside the details.
    # Both open the full-size photo, so neither name claims to open a thumbnail.
    which = "photo" if size == "sm" else "photo full size"
    return (f'<button type="button" class="zoom" data-full="{prefix}img/{r["id"]}-lg.webp" data-name="{name}" '
            f'aria-label="View {name} {which}">{photo(r, size, prefix)}<span class="zi" aria-hidden="true"></span></button>')


def vlink(ids, text):
    return f'<a class="jump" href="#m-{ids[0]}" data-ids="{" ".join(ids)}">{text}</a>'


ROW_FIG = re.compile(r"\{([pc]):([a-z0-9-]+)\}")
ROW_LINK = re.compile(r"\{v:([a-z0-9-]+):([^}]+)\}")


def with_links(text, by_id):
    """`{v:ID:Words}` becomes a link to that row, so the editorial lead can
    name a product without the record holding markup for a specific id.
    `{p:ID}` and `{c:ID}` print its price and its no-plan 3-year cost, to the
    pound, so the answer near the top cannot drift from the table."""
    text = ROW_FIG.sub(
        lambda m: f"£{round(by_id[m.group(2)]['price' if m.group(1) == 'p' else 'nosub3']):,}",
        text,
    )
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


# A claim whose card sentence is already one of the row's own fields is not
# shipped twice: the data names the field, and the script reads it. `nosub`
# and `plan` each have two possible fields because a row with a plan and one
# without answer the same question with different rows of their own.
SAY_FIELDS = {
    "price": ("priceNote",),
    "rec": ("history",),
    "history": ("history",),
    "ha": ("ha",),
    "plan": ("plan", "storage"),
    "nosub": ("storage", "history"),
}


def data_map(ds, cat):
    """The row record the script reads, keyed by product id."""
    score_max = ds.SCORE_MAX
    claims_by_id = {r["id"]: claims(r) for r in ds.ROWS}
    out = {}
    for r in ds.ROWS:
        d = {
            "name": f"{r['brand']} {r['model']}",
            "rec": ds.REC_LABEL[r["rec"]], "recCls": r["rec"],
            "price": "Check price" if r.get("price_check") else money(r["price"], None),
            "priceNote": r["price_note"],
            "score": f"{r['score_total']}/{score_max}",
            "tone": cat["verdicts"][r["verdict"]][1] if r["verdict"] else "",
            "vtag": cat["verdicts"][r["verdict"]][0] if r["verdict"] else "",
            "nosub3": money(r["nosub3"], None),
            "sub3": money(r["sub3"], None) if r["sub3"] is not None else cat["labels"]["no_plan_cell"],
            "keep3": r["keep3"], "keepNote": r["keep_note"], "region": r["plan_region"],
            "best": r["best"], "catch": r["catch"],
            "power": " / ".join(ds.POWER_LABEL[p] for p in r["power"]),
            "storage": r["storage"], "live": r["live"], "alerts": r["alerts"],
            "ai": r["ai"], "history": r["history"], "paywalled": r["paywalled"],
            "plan": r["sub_text"], "ha": r["ha_text"], "wifi": r["wifi"],
            "img": bool(has_photo(r)),
        }
        d["claims"] = {}
        for key, claim in claims_by_id[r["id"]].items():
            item = {f: v for f, v in claim.items() if f != "keys"}
            for field in SAY_FIELDS.get(key, ()):
                if item.get("say") == d[field]:
                    item.pop("say")
                    item["f"] = field
                    break
            d["claims"][key] = item
        out[r["id"]] = d
    return out


def category_js(ds, cat):
    """The words the script speaks for one category, keyed by slug."""
    period, padj = cat["period"], cat["period_adj"]
    return {
        "noun": cat["noun"], "nouns": cat["nouns"], "imgp": "../" * cat["route"].count("/") + "img/",
        "periodAdj": padj, "checked": ds.CHECKED,
        "compare": [[label, key] for label, key in cat["compare"]],
        "pin": cat["pin"],
        "sortNotes": {key: note for key, _, note in cat["sort"]},
        "defaultSort": cat["sort"][0][0],
        "claims": {k: v.format(period=period, period_adj=padj) for k, v in cat["claims"].items()},
        "shown": cat["shown"], "noMatch": cat["no_match"], "empty": cat["empty_line"],
        "cmpCaption": cat["cmp_caption"],
        "keepLabel": cat["labels"]["keep_label"],
        "recFilterWhy": cat["labels"]["rec_filter_why"],
        "haFilterWhy": cat["labels"]["ha_filter_why"],
    }


SHARED = None


def shared_assets():
    """The one stylesheet and script every page loads.

    The script carries all categories, keyed by slug, because it lives at one
    address shared by every route; each page names its category on `<body>`
    and the script reads its own record. Building it once keeps the content
    hash the same on every page, so a nested route and the root cannot point at
    different scripts.
    """
    global SHARED
    if SHARED is None:
        data, cats = {}, {}
        for c in CATEGORIES:
            ds = DATASETS[c["slug"]]
            written = words(c)
            data[c["slug"]] = data_map(ds, written)
            cats[c["slug"]] = category_js(ds, written)
        js = (open(os.path.join(HERE, "page.js"), encoding="utf-8").read()
              .replace("/*@@DATA@@*/{}", json.dumps(data, ensure_ascii=False))
              .replace("/*@@CAT@@*/{}", json.dumps(cats, ensure_ascii=False)))
        SHARED = js, page_css()
    return SHARED


def build(cat):
    """Every file one category owns, as `{filename: text}`, plus its data rows."""
    ds = DATASETS[cat["slug"]]
    cat = words(cat)
    L = cat["labels"]
    rows = ds.ROWS
    n = len(rows)
    period, padj = cat["period"], cat["period_adj"]
    # A nested route needs the assets one level up; the root needs them plain.
    prefix = "../" * cat["route"].count("/")
    # The vocabulary, dates and numbering are this category's own, so a second
    # page cannot borrow the first one's words or its footnote numbers.
    S, FN, order = ds.S, ds.FN, cat["order"]
    CHECKED, CHECKED_ISO, MONTHS = ds.CHECKED, ds.CHECKED_ISO, ds.MONTHS
    MINP, MAXP = cat["minp"], cat["maxp"]
    REC_LABEL, REC_RANK = ds.REC_LABEL, ds.REC_RANK
    POWER_LABEL, SCORE_PARTS, SCORE_MAX = ds.POWER_LABEL, ds.SCORE_PARTS, ds.SCORE_MAX
    score_max = SCORE_MAX
    claims_by_id = {r["id"]: claims(r) for r in rows}

    # A category may band its power vocabulary, because seven exact battery
    # buckets are too many to tick. A band's words join the row's tokens, so the
    # script's one exact-token test still finds the row without a second map.
    power_bands = cat.get("power_filters") or []
    power_opts = (
        [(label, label, members) for label, members in power_bands]
        if power_bands
        else [(key, label, (key,)) for key, label in cat["powers"]]
    )

    rows_html = []
    for i, r in enumerate(rows):
        pw_parts = list(r["power"]) + [
            band for band, members in power_bands if set(members) & set(r["power"])
        ]
        pw = "|".join(pw_parts)
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
        # No figure is ever Amazon's price: the price comes from another UK
        # shop, and the Amazon link under it is only where to buy. A row with
        # no other UK seller says "Check price"; its totals use a cited RRP.
        shown = "Check price" if r.get("price_check") else pm
        price = fig(ds, r, cl, "price", shown, f'{pm} at {psrc[0]}',
                    cls="buy chk" if r.get("price_check") else "buy",
                    attrs=f' title="Price source: {e(psrc[0])}"')
        if r.get("buy"):
            bu = S[r["buy"]][1]
            price += (f'<a class="amz" href="{e(bu)}" rel="{rel(bu)}">'
                      f'{e(r.get("buy_label", "Amazon"))}</a>')
        # Each figure a reader might doubt carries its own card. The words are
        # the same ones the cell shows, so the card cannot drift from the figure.
        rec_lbl = REC_LABEL[r["rec"]]
        rec_fig = fig(ds, r, cl, "rec", f'<span class="rec-t">{rec_lbl}</span>', src_label(ds, cl, "rec", rec_lbl))
        nosub_words = money(r["nosub3"], None)
        nosub_fig = fig(ds, r, cl, "nosub", nosub_words, src_label(ds, cl, "nosub", nosub_words))
        sub_words = money(r["sub3"], None) if r["sub3"] is not None else L["no_plan_cell"]
        sub_fig = fig(ds, r, cl, "plan", sub_words if r["sub3"] is not None else f'<span class="noplan">{sub_words}</span>',
                      src_label(ds, cl, "plan", sub_words))
        hist_fig = fig(ds, r, cl, "history", e(r["history"]), src_label(ds, cl, "history", r["history"]))
        ha_fig = fig(ds, r, cl, "ha", e(r["ha_text"]), src_label(ds, cl, "ha", r["ha_text"]))
        plan_fig = fig(ds, r, cl, "plan", e(r["sub_text"]), src_label(ds, cl, "plan", r["sub_text"]))
        ncls = " keep" if r["keep_basis"] == "nosub" else ""
        scls = " keep" if r["keep_basis"] == "sub" else ""
        rec_note = L["rec_note"].get(r["rec"], "")
        rec_note_html = f'<span class="note">{e(rec_note)}</span>' if rec_note else ""
        # The bold figure follows the sort. The default sort is the 3-year cost
        # to keep recordings, so the cell that figure comes from starts bold, and
        # the sort note says so. Where the plan is the cheapest way to record,
        # the cell says so too, or the bold number reads as the wrong figure.
        knote = f'<span class="note">{e(L["keep_sub_note"])}</span>' if r["keep_basis"] == "sub" else ""
        rows_html.append(f'''<tbody class="item" id="m-{r['id']}" data-id="{r['id']}" data-keep="{r['keep_basis']}"{vattr} data-rec="{r['rec']}" data-recv="{REC_RANK[r['rec']]}" data-ha="{r['ha']}" data-power="{pw}" data-price="{r['price']}" data-keep3="{r['keep3']}" data-nosub3="{r['nosub3']}" data-sub3="{r['sub3'] if r['sub3'] is not None else r['nosub3']}" data-noplan="{'1' if r['sub'] is None else '0'}" data-score="{sc}" data-region="{r['plan_region']}" data-model="{e((r['brand']+' '+r['model']).lower())}" data-idx="{i}">
<tr class="main">
<td class="c-cmp"><label class="cmp-w"><input type="checkbox" class="cmp" value="{r['id']}" aria-label="Compare {e(r['brand'])} {e(r['model'])}"><span class="cmp-cap" aria-hidden="true">Compare</span></label></td>
<th scope="row" class="c-model"><div class="mcell">{zoom(r,"sm",prefix)}<div><span class="brand">{e(r['brand'])}</span> <span class="mname">{e(r['model'])}</span>{vtag}<span class="best">Best for: {e(r['best'])}</span></div></div></th>
<td class="c-rec" data-label="{e(L['rec_col'])}"><span class="rec rec-{r['rec']}">{rec_fig}{fn(ds, [r['rec_src']])}</span></td>
<td class="c-price num" data-label="Price">{price}</td>
<td class="c-score" data-label="{e(L['score_col'])}"><span class="score"><b>{sc}</b>/{score_max}</span><span class="bar" aria-hidden="true"><i style="transform:scaleX({sc/score_max:.3f})"></i></span></td>
<td class="c-nosub num{ncls}" data-label="{e(L['nosub_col'])}"><span class="figv">{nosub_fig}{'' if r['free_records'] else rec_note_html}</span></td>
<td class="c-sub num{scls}" data-label="{e(L['sub_col'])}" data-region="{r['plan_region']}"><span class="figv">{sub_fig}{knote}{f'<span class="vh">{EU_NOTE}</span>' if r['plan_region'] == 'EU' else ''}</span></td>
<td class="c-catch" data-label="{e(L['catch_col'])}"><span class="catch-t">{e(r['catch'])}</span><div class="more-w"><button type="button" class="more" aria-expanded="false" aria-controls="d-{r['id']}"><span class="more-t">Costs &amp; sources</span></button></div></td>
</tr>
<tr class="detail" id="d-{r['id']}"><td colspan="8"><div class="dgrid">
<figure class="dimg">{zoom(r,"lg",prefix)}
<p class="srcs">Sources: {srclinks(ds, r['src'])}</p></figure>
<dl class="dspec">
<div class="pair"><dt>{e(L['detail']['power'])}</dt><dd>{e(r['plain'][0])}{pnote}</dd></div>
<div class="pair"><dt>{e(L['detail']['wifi'])}</dt><dd>{e(r['wifi'])}</dd></div>
<div class="pair"><dt>{e(L['detail']['storage'])}</dt><dd>{e(r['plain'][1])}</dd></div>
<div class="pair"><dt>{e(L['detail']['live'])}</dt><dd>{e(r['live'])}</dd></div>
<div class="pair"><dt>{e(L['detail']['alerts'])}</dt><dd>{e(r['alerts'])}</dd></div>
<div class="pair"><dt>{e(L['detail']['ai'])}</dt><dd>{e(r['ai'])}</dd></div>
<div class="pair"><dt>{e(L['detail']['history'])}</dt><dd>{hist_fig} {fn(ds, [r['history_src']])}</dd></div>
<div class="pair"><dt>{e(L['detail']['paywalled'])}</dt><dd>{e(r['paywalled'])}</dd></div>
<div class="pair"><dt>{e(L['detail']['plans'])}</dt><dd>{plan_fig}</dd></div>
<div class="pair"><dt>{e(L['detail']['ha'])}</dt><dd>{ha_fig} {fn(ds, [r['ha_src']])}</dd></div>
<div class="pair"><dt>{e(L['detail']['nosub'])}</dt><dd class="maths">{e(r['maths_free'])}</dd></div>
<div class="pair"><dt>{e(L['detail']['sub'])}</dt><dd class="maths">{e(r['maths_sub'])}</dd></div>
<div class="pair"><dt>{e(L['detail']['score'])}</dt><dd>{"; ".join(f"{lbl} {r['score'][k]}/{mx}" for k, lbl, mx in SCORE_PARTS)}</dd></div>
</dl></div>
{unv}
</td></tr>
</tbody>''')

    page_js, page_css_text = shared_assets()
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
        + "".join(f'<li id="fn{FN[k]}" value="{FN[k]}"><a href="{e(S[k][1])}" rel="{rel(S[k][1])}">{e(S[k][0])}</a></li>' for k in keys)
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

    # The short answer is the category's own: linked sentences, each naming
    # the row it is about.
    by_id = {r["id"]: r for r in rows}
    short_html = (
        f'<p class="vshort"><b class="vlab">{e(cat.get("short_head", "Short answer"))}</b>\n'
        + "".join(
            f'<span class="v-{tone}">{with_links(sentence, by_id)}</span>\n'
            for tone, sentence in zip(cat["short_tones"], cat["short"])
        )
        + "</p>"
    )
    aside_html = (
        f'<aside class="verdict">\n<h2>{e(cat.get("short_head", "Short answer"))}</h2>\n'
        + "".join(
            f'<p class="v-{tone}"><b>{e(head)}</b> {with_links(link + rest, by_id)}</p>\n'
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
        # Three categories no longer fit beside the brand as links, so the
        # masthead holds one disclosure. It is a native details, so every
        # keyboard and screen reader already knows how to open it.
        nav = ('<nav class="cats" aria-label="Categories"><details class="catmenu">'
               '<summary>Categories</summary><ul>' + "".join(
            f'<li><a href="{prefix}{other["route"]}"{" aria-current=\"page\"" if other["slug"] == cat["slug"] else ""}>{e(other.get("nav") or other["nouns"].capitalize())}</a></li>'
            for other in CATEGORIES
        ) + "</ul></details></nav>")

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
</head><body data-cat="{cat['slug']}">
<a class="skip" href="#tbl">{cat["skip"]}</a>
<div class="wrap">
<header class="mast-head">
<div class="mast" id="top"><div>SubFree UK <span class="mast-long">{cat["mast_long"]}</span><span class="mast-short">{cat["mast"]}</span></div>{nav}<button type="button" id="theme"><i aria-hidden="true"></i><span class="t-dark">Dark mode</span><span class="t-light">Light mode</span></button></div>
<div class="intro">
<div>
<h1>{cat["h1"]}</h1>
<p class="dek">{cat["dek"].format(n=n, period=padj)}</p>
<p class="meta"><b>Last checked {CHECKED}.</b> Some links are paid links. No cookies. Spotted a mistake? <a href="{GITHUB}/issues/new">Open an issue</a>.</p>
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
{chr(10).join(f'<label><input type="checkbox" class="f-pw" value="{e(value)}"> {e(label)}</label>' for value, label, _ in power_opts)}
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
<th scope="col" data-sort="model" aria-sort="none"><button type="button">Model{SI}</button></th><th scope="col" data-sort="recv" aria-sort="none"><button type="button">{e(L['rec_col'])}{SI}</button></th><th scope="col" class="num" data-sort="price" aria-sort="none"><button type="button">Price{SI}</button></th><th scope="col" data-sort="score" aria-sort="none"><button type="button">{e(L['score_col'])}{SI}</button></th>
<th scope="col" class="num" data-sort="nosub3" aria-sort="none"><button type="button" aria-label="{e(L['nosub_col'])}, footnote a">{e(L['nosub_col'])}{SI}</button><a class="mk" href="#m-a" aria-label="How the {e(L['nosub_how'])} is worked out">a</a></th><th scope="col" class="num" data-sort="sub3" aria-sort="none"><button type="button" aria-label="{e(L['sub_col'])}, footnote b">{e(L['sub_col'])}{SI}</button><a class="mk" href="#m-b" aria-label="How the {e(L['sub_how'])} is worked out">b</a></th><th scope="col">{e(L['catch_col'])}</th>
</tr></thead>
{''.join(rows_html)}
</table></div>
<p class="empty" id="empty" hidden><span id="empty-txt">{cat["empty_line"]}</span> <span class="empty-acts"><button type="button" class="link" id="near" hidden></button> <button type="button" class="link" id="empty-reset">Reset filters</button></span></p>

<section class="method" id="method">
<div class="method-copy">
<h2>How we worked it out</h2>
<p id="m-a">{method("no_plan", kit=kit+"a 64 GB SanDisk microSD card at " + money(CARD) + " or SanDisk USB stick at " + money(STICK))}</p>
<p id="m-b">{method("with_plan")}</p>
{f'<p>{method("offers")}</p>' if cat["method"].get("offers") else ''}
<p>{method("score")}</p>
<p>{method("terms")}</p>
<p>{method("left_out")}</p>
<p>{method("photos", credits=photo_credits, missing=missing)}</p>
</div>
<details class="srcs" id="sources" open><summary><h2 class="srcs-t">Sources <span class="srcs-n">{len(order)} links</span></h2></summary><div class="fns-wrap">{fn_list}</div></details>
</section>
<footer class="foot">
<p>Last checked {CHECKED}. {n} UK {cat["nouns"]}. <span class="aff">As an Amazon Associate I earn from qualifying purchases.</span> <a href="{GITHUB}/issues/new">Open an issue</a> · <a href="#tbl">Back to the table</a> · <a href="#top">Back to top</a>.</p>
<p>SubFree UK is a personal comparison of UK {cat["nouns"]}, put together by <a href="{GITHUB}">lydenyardley</a> {L['footer']}. Every price links to the page it came from, so you can check it yourself. Spotted a mistake? <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
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
    M = L["md"]
    for r in rows:
        md += [f"### {r['brand']} {r['model']}", f"- **Best for:** {r['best']}", f"- **Main catch:** {r['catch']}",
               f"- **Price:** {money(r['price'])} ({r['price_note']})",
               f"- **{L['nosub_col']}:** {r['maths_free']}", f"- **{L['sub_col']}:** {r['maths_sub']}",
               f"- **{M['storage']}:** {r['storage']}",
               f"- **{M['free']}:** " + M["free_line"].format(
                   live=r["live"].lower() if M.get("free_lower", True) else r["live"],
                   alerts=r["alerts"].lower() if M.get("free_lower", True) else r["alerts"],
                   ai=r["ai"],
               ),
               f"- **{M['history']}:** {r['history']}", f"- **{M['paywalled']}:** {r['paywalled']}",
               f"- **{M['plans']}:** {r['sub_text']}",
               f"- **{M['ha']}:** {r['ha_text']}", *([f"- **{M['unverified']}:** {r['unverified']}"] if r["unverified"] else []),
               "- **Sources:** " + " · ".join(f"[{S[k][0]}]({S[k][1]})" for k in r["src"]), ""]
    md += ["## How the " + padj + " costs are worked out"] + [
        "- " + line.format(card=money(CARD), stick=money(STICK), months=MONTHS)
        for line in cat["method"]["md"]
    ]

    files = {
        cat["page"]: page,
        cat["csv"]: csv_text(ds, rows, cat),
        cat["md"]: "\n".join(md),
        CSS_FILE: page_css_text,
        JS_FILE: page_js,
    }
    # A category that never had an old filename has no redirect to write.
    if cat.get("alias"):
        files[cat["alias"]] = alias
    return files, page_js, page_css_text


def csv_text(ds, rows, cat):
    """The CSV a reader can open, one row per product, every figure with its page."""
    # `csv` writes CRLF by default, which made the file's bytes depend on who
    # committed it: the repo stores CSV with LF, so a Linux checkout disagreed
    # with the generator and `rebuild` failed on a tree that was correct. One
    # terminator everywhere, and the bytes stop depending on the platform.
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow([head.format(score_max=ds.SCORE_MAX) for head in cat["csv_head"]])
    for r in rows:
        values = {
            "brand": r["brand"], "model": r["model"],
            "rec": ds.REC_LABEL[r["rec"]],
            "power": "/".join(ds.POWER_LABEL[p] for p in r["power"]),
            "price": f"{r['price']:.2f}", "price_note": r["price_note"],
            "price_src": ds.S[r["price_src"]][1], "best": r["best"],
            "catch": r["catch"], "score_total": r["score_total"],
            "nosub3": f"{r['nosub3']:.2f}",
            "sub3": "" if r["sub3"] is None else f"{r['sub3']:.2f}",
            "keep3": f"{r['keep3']:.2f}", "maths_free": r["maths_free"],
            "maths_sub": r["maths_sub"], "storage": r["storage"],
            "live": r["live"], "alerts": r["alerts"], "ai": r["ai"],
            "history": r["history"], "paywalled": r["paywalled"],
            "sub_text": r["sub_text"], "plan_region": r["plan_region"],
            "ha_text": r["ha_text"], "wifi": r["wifi"],
            "sources": " ; ".join(ds.S[k][1] for k in r["src"]),
            "unverified": r["unverified"], "checked": ds.CHECKED,
        }
        w.writerow([values[key] for key in CSV_KEYS])
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
    problems = authored_problems()
    for cat in CATEGORIES:
        if not cat.get("rows"):
            problems.append(f"{cat['slug']}: the category has no rows attached")
            continue
        problems.extend(row_problems(cat))
        if len(cat["csv_head"]) != len(CSV_KEYS):
            problems.append(
                f"{cat['slug']}: the CSV has {len(cat['csv_head'])} columns, "
                f"but its rows carry {len(CSV_KEYS)}"
            )
        checked = date.fromisoformat(cat["checked_iso"])
        if checked > date.today():
            problems.append(
                f"{cat['slug']}: checked_iso is {cat['checked_iso']}, which is in the future; "
                "fix the date before building"
            )
    if problems:
        raise SystemExit("Row problems:\n  " + "\n  ".join(problems))
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
    for r in sorted(ROWS, key=lambda r: (r["keep3"] is None, r["keep3"] or 0)):
        print(f"{r['brand']:14} {r['model']:38} score {r['score_total']}  "
              f"nosub {r['nosub3']:8.2f}  sub {r['sub3'] if r['sub3'] else '-':>8}  "
              f"keep {r['keep3']:.2f}")
    open_rows = [r for r in ROWS if r["unverified"]]
    print(f"\nUnverified ({len(open_rows)} of {len(ROWS)} rows):" + (" none" if not open_rows else ""))
    for r in open_rows: print(f"  {r['brand']} {r['model']}: {r['unverified'].replace('£','GBP ')}")


if __name__ == "__main__":
    write()
