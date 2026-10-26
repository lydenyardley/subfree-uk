"""The page: `index.html`, its alias, `404.html`, the CSS and the script.

The dataset, its sources and every derived figure are in `rows.py`, which this
module imports. Everything here turns that data into files. Nothing is written
at import time, so an agent can read the page assembly without touching the
working tree; `write()` does all the writing.
"""

import csv, hashlib, html, json
import os
from datetime import date
from urllib.parse import urlparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
HERE = os.path.dirname(os.path.abspath(__file__))

GITHUB = "https://github.com/lydenyardley/subfree-uk"
SITE = "/subfree-uk/"   # where the site is published; the 404 page needs root-relative links
EMAIL = "lydenyardley+subfreeuk@posteo.net"

from rows import (
    CARD, CHECKED, CHECKED_ISO, FN, MINP, MONTHS, POWER_LABEL, REC_LABEL,
    REC_RANK, ROWS, S, SCORE_PARTS, _CHECKED_DATE, money, order, row_problems,
)

# ---------- HTML ----------
e=html.escape
def fn(keys): return ", ".join(f'<a class="fn" href="#fn{FN[k]}" title="{e(S[k][0])}">{FN[k]}</a>' for k in keys)
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

# Each figure on the page carries its claim. The card opens from the figure and
# gives the page behind it, the day the prices were checked and the sentence in
# the dataset that supports it, and a 3-year total gets the sum it is made of.
# `CLAIM_WHAT` names the claim; the rest is the row's own words.
CLAIM_WHAT = {
    "rec": "Records free without a plan",
    "price": "The price",
    "nosub": "The 3-year cost with no plan",
    "plan": "The 3-year cost with a plan",
    "history": "The recorded history without a plan",
    "ha": "The Home Assistant line",
}
EU_NOTE = "EU price, not a UK quote"
UNSOURCED_CARD = (
    f"The card or USB stick in that sum is an assumption at {money(CARD)}, "
    "not a figure from a cited source."
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
    # every page it is built from. The card or USB stick is the one figure on
    # the page that is an assumption, and the card says so where it shows.
    # What the no-plan sum buys is the kit it adds, where it adds one, and the
    # recording it needs no plan for, where it does not: the storage line names
    # the SmartHub that £115 of Arlo's sum is for, and the history line is what
    # a doorbell spending nothing extra gives instead.
    add("nosub", r["price_src"], r["rec_src"] if r["extra"] else r["history_src"],
        say=r["storage"] if r["extra"] else r["history"], arc=r["maths_free"],
        note=UNSOURCED_CARD if r["extra"] else "")
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
    hears rather than its entities."""
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
IMG = json.load(open(os.path.join(HERE,"images.json"), encoding="utf-8"))
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

# Short-answer verdicts, colour-coded and repeated on the matching rows.
# One row owns "Best overall"; the other variants name the case they win.
VERDICT = {"reo-poe":"best","reo-wifi":"wired","reo-batt":"batt","tapo-d230":"easy","ring":"avoid","blink":"avoid","arlo":"avoid"}
V_LABEL = {"best":"Best overall","wired":"Best with doorbell wiring","batt":"Best battery, no fees","easy":"Easiest battery setup","avoid":"Avoid without a plan"}
V_TONE = {"best":"best","wired":"best","batt":"batt","easy":"batt","avoid":"avoid"}
def vlink(ids, text): return f'<a class="jump" href="#m-{ids[0]}" data-ids="{" ".join(ids)}">{text}</a>'

# The details panel in plain sentences. The table and the comparison keep the
# terse values, which are for someone who already knows the words; this is the
# version for someone who has never fitted a doorbell. No new facts: each
# sentence says the same thing as the row it stands in for.
PLAIN = {
 "ring": ("Runs on the battery, or you can wire it to your existing chime.",
          "None. The doorbell has no storage of its own and no hub to hold the footage."),
 "nest": ("Runs on the battery, or you can wire it to your existing chime.",
          "None. The doorbell has no storage of its own and no hub to hold the footage."),
 "eufy-e340": ("Runs on the battery, or you can wire it to your existing chime.",
          "8 GB is built into the doorbell, so it records on its own. The optional HomeBase S380 (16 GB, expandable) holds more."),
 "reo-wifi": ("Wired to your existing doorbell chime.",
          "A microSD card in the doorbell (up to 256 GB), or a Reolink NVR. It also streams over RTSP and ONVIF, so other apps can pull the video."),
 "reo-poe": ("Powered by an Ethernet cable (PoE): one cable carries both the power and the video, so there is no separate power supply to run.",
          "A microSD card in the doorbell, or a Reolink NVR. It also streams over RTSP and ONVIF, so other apps can pull the video."),
 "reo-batt": ("Runs on the battery, or you can wire it to your existing chime.",
          "A microSD card in the doorbell, or a Reolink Home Hub indoors (up to 1 TB)."),
 "tapo-d230": ("Battery only.",
          "A microSD card (up to 512 GB) in the indoor H200 hub, so the footage stays in the house."),
 "tapo-td21": ("Battery only.",
          "A microSD card (up to 512 GB) in the doorbell itself, so the card comes out with the doorbell if it is stolen."),
 "arlo": ("Battery only, though you can wire it to an existing chime for trickle charging.",
          "Recording needs an Arlo SmartHub (VMB4540, with a USB stick) or a Base Station."),
 "aqara-g4": ("Runs on AA batteries, or you can wire it to your existing chime.",
          "A microSD card (up to 512 GB) in the indoor chime."),
 "blink": ("Battery only.",
          "Recording needs a Sync Module 2 and a USB stick (1–256 GB). The clips are not encrypted."),
 "ezviz-ep3x": ("Battery only.",
          "32 GB is built in, so no card is needed."),
 "ezviz-db2": ("Battery only.",
          "A microSD card (up to 256 GB) in the indoor chime that comes with it."),
 "hik": ("Wired to your existing doorbell chime.",
          "A microSD card (up to 128 GB), and it can stream to an NVR over RTSP."),
}
def plain_problems():
    """Every row has a plain sentence, and no sentence is left for a gone row."""
    missing = [r["id"] for r in ROWS if r["id"] not in PLAIN]
    stale = [k for k in PLAIN if k not in {r["id"] for r in ROWS}]
    if missing:
        raise SystemExit(f"PLAIN has no entry for: {missing}")
    if stale:
        raise SystemExit(f"PLAIN has an entry for a row that does not exist: {stale}")

# Per row, once: the markup builds the cards from this, and the script rebuilds
# the comparison's own figures from the same sentences.
CLAIMS={r["id"]: claims(r) for r in ROWS}

rows_html=[]
for i,r in enumerate(ROWS):
    pw=" ".join(r["power"])
    sc=r["score_total"]
    v=VERDICT.get(r["id"])
    tone=V_TONE[v] if v else ""
    vattr=f' data-v="{tone}"' if tone else ""
    vtag=f'<span class="vtag v-{tone}">{V_LABEL[v]}</span>' if v else ""
    unv=f'<p class="unverified"><b>Not yet verified:</b> {e(r["unverified"])}</p>' if r["unverified"] else ""
    pnote='. ' + e(r["power_note"]) if r.get("power_note") else ""
    cl=CLAIMS[r["id"]]
    # The price is the link to the page the price came from, so the promise in
    # the intro ("each one links to its source") is kept in the row itself; with
    # a script that click opens the price's card, which prints the same address.
    pm=money(r["price"], None);psrc=S[r["price_src"]]
    price=fig(r, cl, "price", pm, f'{pm} at {psrc[0]}', cls="buy",
              attrs=f' title="Check the price at {e(psrc[0])}"')
    # Each figure a reader might doubt carries its own card. The words are the
    # same ones the cell shows, so the card cannot drift from the figure.
    rec_lbl=REC_LABEL[r["rec"]]
    rec_fig=fig(r, cl, "rec", f'<span class="rec-t">{rec_lbl}</span>', src_label(cl, "rec", rec_lbl))
    nosub_words=money(r["nosub3"], None)
    nosub_fig=fig(r, cl, "nosub", nosub_words, src_label(cl, "nosub", nosub_words))
    sub_words=money(r["sub3"], None) if r["sub3"] is not None else "No plan"
    sub_fig=fig(r, cl, "plan", sub_words if r["sub3"] is not None else f'<span class="noplan">{sub_words}</span>',
                src_label(cl, "plan", sub_words))
    hist_fig=fig(r, cl, "history", e(r["history"]), src_label(cl, "history", r["history"]))
    ha_fig=fig(r, cl, "ha", e(r["ha_text"]), src_label(cl, "ha", r["ha_text"]))
    plan_fig=fig(r, cl, "plan", e(r["sub_text"]), src_label(cl, "plan", r["sub_text"]))
    ncls=" keep" if r["keep_basis"]=="nosub" else ""
    scls=" keep" if r["keep_basis"]=="sub" else ""
    # The bold figure follows the sort. The default sort is the 3-year cost to
    # keep recordings, so the cell that figure comes from starts bold, and the
    # sort note says so. Where the plan is the cheapest way to record, the
    # cell says so too, or the bold number reads as the wrong figure.
    knote='<span class="note">cheapest for this model: with plan</span>' if r["keep_basis"]=="sub" else ""
    rows_html.append(f'''<tbody class="item" id="m-{r['id']}" data-id="{r['id']}" data-keep="{r['keep_basis']}"{vattr} data-rec="{r['rec']}" data-recv="{REC_RANK[r['rec']]}" data-ha="{r['ha']}" data-power="{pw}" data-price="{r['price']}" data-keep3="{r['keep3']}" data-nosub3="{r['nosub3']}" data-sub3="{r['sub3'] if r['sub3'] is not None else 0}" data-score="{sc}" data-model="{e((r['brand']+' '+r['model']).lower())}" data-idx="{i}">
<tr class="main">
<td class="c-cmp"><label class="cmp-w"><input type="checkbox" class="cmp" value="{r['id']}" aria-label="Compare {e(r['brand'])} {e(r['model'])}"><span class="cmp-cap" aria-hidden="true">Compare</span></label></td>
<th scope="row" class="c-model"><div class="mcell">{zoom(r,"sm")}<div><span class="brand">{e(r['brand'])}</span> <span class="mname">{e(r['model'])}</span>{vtag}<span class="best">Best for: {e(r['best'])}</span></div></div></th>
<td class="c-rec" data-label="Records free?"><span class="rec rec-{r['rec']}">{rec_fig}{fn([r['rec_src']])}</span></td>
<td class="c-price num" data-label="Price">{price}</td>
<td class="c-score" data-label="Free features"><span class="score"><b>{sc}</b>/8</span><span class="bar" aria-hidden="true"><i style="transform:scaleX({sc/8:.3f})"></i></span></td>
<td class="c-nosub num{ncls}" data-label="3 years, no plan"><span class="figv">{nosub_fig}{'' if r['free_records'] else '<span class="note">no recordings</span>' if r['rec']=='no' else '<span class="note">3 hrs history</span>'}</span></td>
<td class="c-sub num{scls}" data-label="3 years, with plan" data-region="{r['plan_region']}"><span class="figv">{sub_fig}{knote}{f'<span class="vh">{EU_NOTE}</span>' if r['plan_region'] == 'EU' else ''}</span></td>
<td class="c-catch" data-label="Main catch"><span class="catch-t">{e(r['catch'])}</span><div class="more-w"><button type="button" class="more" aria-expanded="false" aria-controls="d-{r['id']}"><span class="more-t">Costs &amp; sources</span></button></div></td>
</tr>
<tr class="detail" id="d-{r['id']}"><td colspan="8"><div class="dgrid">
<figure class="dimg">{zoom(r,"lg")}
<p class="srcs">Sources: {srclinks(r['src'])}</p></figure>
<dl class="dspec">
<div class="pair"><dt>Power</dt><dd>{e(PLAIN[r['id']][0])}{pnote}</dd></div>
<div class="pair"><dt>Wi-Fi</dt><dd>{e(r['wifi'])}</dd></div>
<div class="pair"><dt>Storage</dt><dd>{e(PLAIN[r['id']][1])}</dd></div>
<div class="pair"><dt>Live view</dt><dd>{e(r['live'])}</dd></div>
<div class="pair"><dt>Motion alerts</dt><dd>{e(r['alerts'])}</dd></div>
<div class="pair"><dt>Smart detection</dt><dd>{e(r['ai'])}</dd></div>
<div class="pair"><dt>History without a plan</dt><dd>{hist_fig} {fn([r['history_src']])}</dd></div>
<div class="pair"><dt>Behind the paywall</dt><dd>{e(r['paywalled'])}</dd></div>
<div class="pair"><dt>Plans</dt><dd>{plan_fig}</dd></div>
<div class="pair"><dt>Home Assistant</dt><dd>{ha_fig} {fn([r['ha_src']])}</dd></div>
<div class="pair"><dt>3 years, no plan</dt><dd class="maths">{e(r['maths_free'])}</dd></div>
<div class="pair"><dt>3 years, with plan</dt><dd class="maths">{e(r['maths_sub'])}</dd></div>
<div class="pair"><dt>Score breakdown</dt><dd>{"; ".join(f"{lbl} {r['score'][k]}/{mx}" for k,lbl,mx in SCORE_PARTS)}</dd></div>
</dl></div>
{unv}
</td></tr>
</tbody>''')

data_js = json.dumps({r["id"]:{
 "name":f"{r['brand']} {r['model']}","rec":REC_LABEL[r["rec"]],"recCls":r["rec"],"price":money(r["price"], None),"score":f"{r['score_total']}/8",
 "tone":V_TONE[VERDICT[r["id"]]] if VERDICT.get(r["id"]) else "","vtag":V_LABEL[VERDICT[r["id"]]] if VERDICT.get(r["id"]) else "",
 "nosub3":money(r["nosub3"], None),"sub3":money(r["sub3"], None) if r["sub3"] is not None else "No plan","keep3":r["keep3"],"keepNote":r["keep_note"],"region":r["plan_region"],"best":r["best"],"catch":r["catch"],"power":" / ".join(POWER_LABEL[p] for p in r["power"]),
 "storage":r["storage"],"live":r["live"],"alerts":r["alerts"],"ai":r["ai"],"history":r["history"],"paywalled":r["paywalled"],
 "plan":r["sub_text"],"ha":r["ha_text"],"wifi":r["wifi"],
 "claims":{k:{f:v for f,v in c.items() if f!="keys"} for k,c in CLAIMS[r["id"]].items()},
 "img":"" if IMG.get(r["id"],{}).get("placeholder") else f'img/{r["id"]}-sm.webp',
 "imgLg":"" if IMG.get(r["id"],{}).get("placeholder") else f'img/{r["id"]}-lg.webp'} for r in ROWS}, ensure_ascii=False)

# 52 numbered lines are hard to scan, so the list is grouped by the host the
# link points at. Real <li value> keeps every footnote number stable.
HOST_PREFIX = {"www", "en", "en-uk", "uk", "eu", "us", "store", "cloud", "support", "blog"}
def src_host(url):
    parts = urlparse(url).netloc.lower().split(".")
    while len(parts) > 2 and parts[0] in HOST_PREFIX: parts = parts[1:]
    return ".".join(parts)
groups={}
for k in order: groups.setdefault(src_host(S[k][1]), []).append(k)
fn_list="".join(
    f'<section class="fns-g"><h3>{e(host)}</h3><ol class="fns">'
    + "".join(f'<li id="fn{FN[k]}" value="{FN[k]}"><a href="{e(S[k][1])}" rel="nofollow noopener noreferrer">{e(S[k][0])}</a></li>' for k in keys)
    + '</ol></section>'
    for host, keys in sorted(groups.items(), key=lambda kv: FN[kv[1][0]]))
maxp=int(max(r["price"] for r in ROWS)+5)
byid={r["id"]:r for r in ROWS}
photo_credits=", ".join(f'<a href="{e(IMG[r["id"]]["page"])}" rel="nofollow noopener noreferrer">{e(r["brand"])} {e(r["model"])}</a>' for r in ROWS if not IMG.get(r["id"],{}).get("placeholder"))
no_photo=", ".join(f'{e(r["brand"])} {e(r["model"])}' for r in ROWS if IMG.get(r["id"],{}).get("placeholder"))

# The page's static parts live in their own files so an editor, a linter and
# `node --check` can see them. They ship as separate asset files, not inline:
# with gzip on, that is 26.2KB on a first visit against 29.0KB inlined, and
# 13.5KB on a repeat visit. The version in the URL is a content hash, so a
# change busts the cache, while the path stays stable: GitHub Pages caches HTML
# for ten minutes, and a hashed filename that a deploy deletes would leave that
# cached copy asking for a file that no longer exists.
PAGE_CSS = open(os.path.join(HERE, "page.css"), encoding="utf-8").read()
PAGE_JS = (open(os.path.join(HERE, "page.js"), encoding="utf-8").read()
           .replace("/*@@DATA@@*/{}", data_js)
           .replace("/*@@CLAIMS@@*/{}", json.dumps(CLAIM_WHAT))
           .replace("@@CHECKED@@", CHECKED))

def content_version(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:10]


# The sort indicator is drawn by the stylesheet, so the button keeps its word
# as its name and the mark carries no text of its own.
SI = '<span class="si" aria-hidden="true"></span>'

CSS_FILE, JS_FILE = "assets/page.css", "assets/page.js"
CSS_URL = f"{CSS_FILE}?v={content_version(PAGE_CSS)}"
JS_URL = f"{JS_FILE}?v={content_version(PAGE_JS)}"

page=f'''<!doctype html>
<html lang="en-GB" class="no-js"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="light dark">
<title>Video doorbells that work without a subscription (UK) | SubFree UK</title>
<meta name="description" content="{len(ROWS)} UK video doorbells compared: what is free, what is paywalled, and what each costs over three years.">
<link rel="canonical" href="https://lydenyardley.github.io/subfree-uk/">
<meta property="og:type" content="website">
<meta property="og:title" content="Video doorbells that work without a subscription (UK)">
<meta property="og:description" content="{len(ROWS)} UK video doorbells compared: what is free, what is paywalled, and what each costs over three years.">
<meta property="og:url" content="https://lydenyardley.github.io/subfree-uk/">
<meta property="og:image" content="https://lydenyardley.github.io/subfree-uk/img/reo-poe-lg.webp">
<meta property="og:image:alt" content="Reolink Video Doorbell PoE">
<meta name="twitter:card" content="summary">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<script>document.documentElement.className="js";try{{var t=localStorage.getItem("theme");if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>
<link rel="stylesheet" href="{CSS_URL}">
</head><body>
<a class="skip" href="#tbl">Skip to the doorbell table</a>
<div class="wrap">
<header class="mast-head">
<div class="mast" id="top"><div>SubFree UK <span class="mast-long">Gadgets that work without a subscription</span><span class="mast-short">No subscriptions</span></div><button type="button" id="theme"><i aria-hidden="true"></i><span>Dark mode</span></button></div>
<div class="intro">
<div>
<h1>Video doorbells that work without a subscription</h1>
<p class="dek">{len(ROWS)} UK doorbells, checked against manufacturer pages and independent reviews: free features, paywalls and 3-year costs.</p>
<p class="meta"><b>Last checked {CHECKED}.</b> No affiliate links, no tracking, no cookies. Spotted a mistake? <a href="{GITHUB}/issues/new">Open an issue</a>.</p>
<p class="vshort"><b class="vlab">Short answer</b>
<span class="v-best">{vlink(["reo-poe"],"Reolink PoE")} is the best overall without fees.</span>
<span class="v-batt">{vlink(["tapo-d230"],"Tapo D230S1")} is the easiest battery one.</span>
<span class="v-avoid">{vlink(["ring"],"Ring")} needs a plan. {vlink(["blink"],"Blink")} and {vlink(["arlo"],"Arlo")} need extra kit.</span>
</p>
</div>
<aside class="verdict">
<h2>The short answer</h2>
<p class="v-best"><b>Best overall without fees:</b> {vlink(["reo-poe"],"Reolink Video Doorbell PoE")}. It records to a card or NVR, nothing is paywalled, and Reolink is the only brand here with an official local Home Assistant integration. The WiFi and battery versions follow the same rules if you can't run an Ethernet cable.</p>
<p class="v-batt"><b>Easiest battery pick:</b> {vlink(["tapo-d230"],"Tapo D230S1")}, which keeps footage on a hub inside the house.</p>
<p class="v-avoid"><b>Avoid if you won't pay monthly:</b> {vlink(["ring"],"Ring")} records nothing without a plan, and {vlink(["blink"],"Blink")} and {vlink(["arlo"],"Arlo")} need extra hardware.</p>
</aside>
</div>
</header>

<main>
<p class="vh" id="live" role="status"></p>
<form class="controls" id="controls" onsubmit="return false">
<details class="filters" id="filters" open>
<summary>Filters</summary>
<div class="fbody">
<fieldset><legend>Show only</legend><div class="opts">
<label><input type="checkbox" id="f-rec"> Records free, no extra kit</label>
<label><input type="checkbox" id="f-ha"> Local / Home Assistant</label>
</div></fieldset>
<fieldset><legend>Power</legend><div class="opts">
<label><input type="checkbox" class="f-pw" value="battery"> Battery</label>
<label><input type="checkbox" class="f-pw" value="wired"> Wired</label>
<label><input type="checkbox" class="f-pw" value="poe"> PoE</label>
</div><p class="hint">PoE: one cable carries both power and data.</p></fieldset>
<div class="range">
<span class="lab">Price</span>
<div class="dual">
<div class="dual-track" aria-hidden="true"><i id="f-fill"></i></div>
<input type="range" id="f-min" min="{MINP}" max="{maxp}" step="5" value="{MINP}" aria-label="Lowest price">
<input type="range" id="f-max" min="{MINP}" max="{maxp}" step="5" value="{maxp}" aria-label="Highest price">
</div>
<div class="dual-vals"><output id="f-min-out" for="f-min">£{MINP}</output><output id="f-max-out" for="f-max">£{maxp}</output></div>
</div>
</div>
</details>
<div class="sortby"><label class="lab" for="sort">Sort by</label><select id="sort">
<option value="keep3">3-year cost to keep recordings</option>
<option value="price">Price, low to high</option>
<option value="score">Free-feature score, high to low</option>
<option value="recv">Records free first</option>
<option value="nosub3">3-year cost, no plan</option>
<option value="sub3">3-year cost, with plan</option>
<option value="model">Model, A to Z</option>
</select><p class="sortnote" id="sortnote">Order: 3-year cost to keep recordings (the bold figure).</p></div>
<p class="count">Tick up to 3 doorbells to compare. <span id="count">{len(ROWS)}</span> of {len(ROWS)} shown · <button type="button" class="link" id="reset">Reset</button><span id="cmp-sep" hidden> · </span><button type="button" class="link" id="cmp-inline" hidden>Compare</button><span id="cmp-cap" class="cap" hidden></span></p>
</form>
<noscript><p class="nojs">Filters, sorting and compare need JavaScript. All {len(ROWS)} doorbells are listed below, with each model's costs and sources open.</p></noscript>
<script>if(window.matchMedia('(max-width:520px)').matches)document.getElementById('filters').open=false;</script>

<section id="compare" hidden>
<div class="cmp-head"><h2 id="cmp-h" tabindex="-1">Side by side</h2><div class="cmp-actions"><label class="cmpo" id="cmp-diff-w" hidden><input type="checkbox" id="cmp-diff"> Differences only <span id="cmp-dupes"></span></label><span class="cmp-links"><button type="button" class="link" id="cmp-copy">Copy shortlist</button><button type="button" class="link" id="cmp-clear">Clear</button><button type="button" class="link" id="cmp-close">Close</button></span></div></div>
<p class="cmp-note" id="cmp-note" role="status" hidden></p>
<p class="cmp-cue" id="cmp-cue" hidden></p>
<div class="cmp-wrap"><div class="cmp-scroll" tabindex="0" role="region" aria-label="Comparison table, scrolls sideways"><table class="cmp-t" id="cmp-table"></table></div></div>
</section>

<div id="totop-s" aria-hidden="true"></div>
<div class="tbl-w"><div class="prog" aria-hidden="true"><i></i></div>
<table class="main-t" id="tbl" tabindex="-1">
<caption class="vh">Doorbell comparison: {len(ROWS)} models, 8 columns</caption>
<thead><tr>
<th scope="col" class="c-cmp"><span class="vh">Compare</span><svg class="cmp-i" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><rect x="1.75" y="1.75" width="16.5" height="16.5" rx="2"/><path d="M5.5 10.4l3.1 3.1 5.9-6.3"/></svg></th>
<th scope="col" data-sort="model" aria-sort="none"><button type="button">Model{SI}</button></th><th scope="col" data-sort="recv" aria-sort="none"><button type="button">Records free?{SI}</button></th><th scope="col" class="num" data-sort="price" aria-sort="none"><button type="button">Price{SI}</button></th><th scope="col" data-sort="score" aria-sort="none"><button type="button">Free features{SI}</button></th>
<th scope="col" class="num" data-sort="nosub3" aria-sort="none"><button type="button" aria-label="3-year cost, no plan, footnote a">3-year cost, no plan{SI}</button><a class="mk" href="#m-a" aria-label="How the 3-year cost without a plan is worked out">a</a></th><th scope="col" class="num" data-sort="sub3" aria-sort="none"><button type="button" aria-label="3-year cost, with plan, footnote b">3-year cost, with plan{SI}</button><a class="mk" href="#m-b" aria-label="How the 3-year cost with a plan is worked out">b</a></th><th scope="col">Main catch</th>
</tr></thead>
{''.join(rows_html)}
</table></div>
<p class="empty" id="empty" hidden><span id="empty-txt">Nothing matches those filters.</span> <span class="empty-acts"><button type="button" class="link" id="near" hidden></button> <button type="button" class="link" id="empty-reset">Reset filters</button></span></p>

<section class="method" id="method">
<div class="method-copy">
<h2>How we worked it out</h2>
<p id="m-a"><sup>a</sup> <b>3 years, no plan</b> = price + anything you must add to record for free (Blink's Sync Module 2 at £39.99, Arlo's SmartHub at £105.07, and a microSD card or USB stick, assumed at {money(CARD)}; that last figure isn't from a cited source). Ring and Nest can't keep recordings this way, which is shown next to the figure.</p>
<p id="m-b"><sup>b</sup> <b>3 years, with plan</b> = price + 36 × the cheapest UK monthly plan that adds cloud recording for one device. Paying yearly is usually cheaper. The EZVIZ plan figure is the EU price because EZVIZ shows UK pricing only inside its app. Every model's sums are under <i>Details</i>.</p>
<p><b>Free-feature score (out of 8):</b> records for free (2 = out of the box, 1 = with extra kit or only briefly), free live view (1), free motion alerts (1), free smart detection (1), storage included in the box (1), local Home Assistant support (2 = official and local, 1 = unofficial or generic).</p>
<p><b>Plain terms.</b> <i>PoE</i> (Power over Ethernet) sends power and video down one network cable. An <i>NVR</i> is a recorder box that stores footage from several cameras. A <i>microSD</i> card is the small memory card that sits inside many doorbells or their indoor chime. <i>2.4 GHz only</i> means the doorbell cannot join a 5 GHz network, so it will not show up on a phone that is on 5 GHz. <i>Home Assistant</i> is free software that keeps your smart home on your own network instead of a manufacturer's cloud.</p>
<p>Batteries, electricity, installation (except Hikvision, where the price includes fitting) and future price rises are left out. Anything not yet confirmed is listed under <i>Not yet verified</i> in each model's details.</p>
<p>Photos are the manufacturers' own, from their product pages: {photo_credits}.{f" No reliable official photo for: {no_photo}." if no_photo else ""}</p>
</div>
<details class="srcs" id="sources" open><summary><h2 class="srcs-t">Sources <span class="srcs-n">{len(order)} links</span></h2></summary><div class="fns-wrap">{fn_list}</div></details>
</section>
<footer class="foot">
<p>Last checked {CHECKED}. {len(ROWS)} UK doorbells, no affiliate links, no tracking. <a href="{GITHUB}/issues/new">Open an issue</a> · <a href="#tbl">Back to the table</a> · <a href="#top">Back to top</a>.</p>
<p>SubFree UK is a personal comparison of UK video doorbells, put together by <a href="{GITHUB}">lydenyardley</a> to show which ones record without a subscription. Every price links to the page it came from, so you can check it yourself. Spotted a mistake? <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
</footer>
</main>
</div>
<div class="tray" id="tray" hidden><span id="tray-txt"></span><button type="button" id="tray-go">Compare</button><button type="button" class="ghost" id="tray-clear">Clear</button></div>
<button type="button" class="totop" id="totop" hidden aria-label="Back to top"><span aria-hidden="true">↑</span></button>
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
<script src="{JS_URL}"></script>
</body></html>'''
# One page, one name. The second filename used to be a byte-identical copy;
# it is now a redirect so an old link still lands on the canonical URL.
ALIAS = '''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>Moved: the doorbell comparison</title>
<link rel="canonical" href="https://lydenyardley.github.io/subfree-uk/">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=./">
</head><body><p>This page has moved to the <a href="./">UK doorbell comparison</a>.</p></body></html>'''

# A mistyped link should land on the site's own page, not on a hosting
# company's. GitHub Pages serves this file for any path it cannot find, so
# the links in it are root-relative and work at any depth.
NOT_FOUND = f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<title>Page not found | SubFree UK</title>
<meta name="description" content="That page does not exist. The UK video doorbell comparison is on the home page.">
<link rel="stylesheet" href="{SITE}{CSS_FILE}?v={content_version(PAGE_CSS)}">
</head><body>
<div class="wrap">
<header class="mast-head"><div class="mast"><div>SubFree UK <span class="mast-long">Gadgets that work without a subscription</span><span class="mast-short">No subscriptions</span></div></div></header>
<main class="nf">
<h1>Page not found</h1>
<p>That link does not lead anywhere. The comparison of UK video doorbells that record without a subscription is on the home page, and it is one page.</p>
<a class="nf-btn" href="{SITE}">See the doorbell comparison</a>
</main>
</div>
</body></html>'''


def write():
    problems = row_problems()
    if problems:
        raise SystemExit("Row problems:\n  " + "\n  ".join(problems))
    plain_problems()
    if _CHECKED_DATE > date.today():
        raise SystemExit(
            f"CHECKED_ISO is {CHECKED_ISO}, which is in the future; fix the date before building"
        )
    # ---------- CSV ----------
    with open(os.path.join(ROOT,"data","doorbells.csv"),"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(["Brand","Model","Records free without subscription","Power","UK price (£)","Price note","Price source",
            "Best for","Main catch","Free-feature score (/8)","3-yr cost without subscription (£)","3-yr cost with cheapest plan, monthly (£)",
            "Cheapest 3-yr cost to keep recordings (£)","Maths: without","Maths: with","Local storage","Live view free?","Motion alerts free?",
            "Smart detection","Recorded history without subscription","What's paywalled","Subscription & UK price","Plan price region","Home Assistant / local-only",
            "Wi-Fi","Sources","Unverified / re-check","Last checked"])
        for r in ROWS:
            w.writerow([r["brand"],r["model"],REC_LABEL[r["rec"]],"/".join(POWER_LABEL[p] for p in r["power"]),f"{r['price']:.2f}",r["price_note"],S[r["price_src"]][1],
                r["best"],r["catch"],r["score_total"],f"{r['nosub3']:.2f}","" if r["sub3"] is None else f"{r['sub3']:.2f}",f"{r['keep3']:.2f}",r["maths_free"],r["maths_sub"],
                r["storage"],r["live"],r["alerts"],r["ai"],r["history"],r["paywalled"],r["sub_text"],r["plan_region"],r["ha_text"],r["wifi"],
                " ; ".join(S[k][1] for k in r["src"]),r["unverified"],CHECKED])

    # ---------- Markdown ----------
    md=[f"# UK video doorbells without a subscription\n", f"Last checked {CHECKED}. {len(ROWS)} doorbells. No affiliate links.\n",
        "| Doorbell | Records free? | Price | Score /8 | 3 yrs, no plan | 3 yrs, with plan | Best for | Main catch |","|---|---|---|---|---|---|---|---|"]
    for r in sorted(ROWS,key=lambda r:r["keep3"]):
        md.append(f"| {r['brand']} {r['model']} | {REC_LABEL[r['rec']]} | [{money(r['price'])}]({S[r['price_src']][1]}) | {r['score_total']} | {money(r['nosub3'])} | {money(r['sub3']) if r['sub3'] else '—'} | {r['best']} | {r['catch']} |")
    md.append("\n## Detail\n")
    for r in ROWS:
        md += [f"### {r['brand']} {r['model']}", f"- **Best for:** {r['best']}", f"- **Main catch:** {r['catch']}",
          f"- **Price:** {money(r['price'])} ({r['price_note']})", f"- **3-year cost, no plan:** {r['maths_free']}", f"- **3-year cost, with plan:** {r['maths_sub']}",
          f"- **Storage:** {r['storage']}", f"- **Free:** live view {r['live'].lower()}; alerts {r['alerts'].lower()}; smart detection: {r['ai']}",
          f"- **History without plan:** {r['history']}", f"- **Paywalled:** {r['paywalled']}", f"- **Plans:** {r['sub_text']}",
          f"- **Home Assistant:** {r['ha_text']}", *([f"- **Unverified:** {r['unverified']}"] if r["unverified"] else []),
          "- **Sources:** " + " · ".join(f"[{S[k][0]}]({S[k][1]})" for k in r["src"]), ""]
    md += ["## How the 3-year costs are worked out",
     f"- Without a plan: hardware price + anything extra you need to record for free (a microSD card or USB stick is assumed at {money(CARD)}; that figure isn't from a cited source).",
     f"- With a plan: hardware price + {MONTHS} × the cheapest UK monthly plan that adds recording for one device. Paying yearly is usually cheaper.",
     "- Batteries, electricity, installation (except Hikvision, where it's included) and price rises are left out."]
    open(os.path.join(ROOT,"data","doorbells.md"),"w",encoding="utf-8").write("\n".join(md))

    open(os.path.join(ROOT,"index.html"),"w",encoding="utf-8").write(page)
    open(os.path.join(ROOT,"doorbells.html"),"w",encoding="utf-8").write(ALIAS)
    open(os.path.join(ROOT,"404.html"),"w",encoding="utf-8").write(NOT_FOUND)
    assets = os.path.join(ROOT, "assets")
    os.makedirs(assets, exist_ok=True)
    for name, text in ((CSS_FILE, PAGE_CSS), (JS_FILE, PAGE_JS)):
        open(os.path.join(ROOT, name), "w", encoding="utf-8").write(text)
    # The one-off content-hashed names from the first version of this change.
    for name in os.listdir(assets):
        if name.startswith("page-") and name.endswith((".css", ".js")):
            os.remove(os.path.join(assets, name))
    print(len(ROWS),"rows written")
    for r in sorted(ROWS,key=lambda r:r["keep3"]): print(f"{r['brand']:14} {r['model']:38} score {r['score_total']}  nosub {r['nosub3']:8.2f}  sub {r['sub3'] if r['sub3'] else '-':>8}  keep {r['keep3']:.2f}")
    open_rows=[r for r in ROWS if r["unverified"]]
    print(f"\nUnverified ({len(open_rows)} of {len(ROWS)} rows):" + (" none" if not open_rows else ""))
    for r in open_rows: print(f"  {r['brand']} {r['model']}: {r['unverified'].replace('£','GBP ')}")

if __name__ == "__main__":
    write()
