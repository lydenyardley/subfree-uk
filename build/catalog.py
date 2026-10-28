"""What a category is: its address, its words, its facets and its files.

One record per category, and the build renders a record. Nothing outside this
module names a category in prose, so a second category is a second record here
plus its rows, not an edit to every page of the build.

A record holds:

- `slug`, `route` (the directory the page is written to, "" for the site root),
  `alias` (the old filename that redirects to it) and the output filenames;
- the nouns: what one row is called and what the many are called;
- the page's title, description, heading, dek, masthead and skip link;
- `months` with the period's written forms, which every 3-year figure uses;
- the row schema: the required keys beyond the universal ones, the fields that
  make a decision (`facets`), the filters, the power vocabulary, the record
  vocabulary and the score parts with their maxima;
- the words for the claims a figure carries, the comparison's rows, the sort
  options and the method paragraphs.

`row_problems()` in `rows.py` validates every row against the record, so an
unknown facet or an invalid value fails by name rather than printing nothing.
"""

# The words a figure's source card prints as its title. A figure with no claim
# key behind it cannot carry its own source, so a new figure starts here.
CLAIM_WHAT = {
    "rec": "Records free without a plan",
    "price": "The price",
    "nosub": "The {period} cost with no plan",
    "plan": "The {period} cost with a plan",
    "history": "The recorded history without a plan",
    "ha": "The Home Assistant line",
}
PLAIN_PART = {
    "power": "Power",
    "storage": "Storage",
}

# The sort control. The first is the default order, and its note names the bold
# figure the order follows.
SORT = [
    ("keep3", "{period_adj} cost to keep recordings",
     "Order: {period_adj} cost to keep recordings (the bold figure)."),
    ("price", "Price, low to high", "Order: price, low to high."),
    ("score", "Free-feature score, high to low", "Order: free-feature score, high to low."),
    ("recv", "Records free first", "Order: records free first."),
    ("nosub3", "{period_adj} cost, no plan",
     "Order: {period_adj} cost with no plan (the bold figure)."),
    ("sub3", "{period_adj} cost, with plan",
     "Order: {period_adj} cost with a plan (the bold figure)."),
    ("model", "Model, A to Z", "Order: model name, A to Z."),
]

# The method paragraphs. `{card}`, `{stick}`, `{months}`, `{period}` and the
# kit figures are filled from the data at build time.
METHOD = {
    "no_plan": (
        "<sup>a</sup> <b>{period}, no plan</b> = price + anything you must add "
        "to record for free ({kit}, each the cheapest UK price we found, on a "
        "page that publishes it). Ring and Nest can't keep recordings this way, "
        "which is shown next to the figure."
    ),
    "with_plan": (
        "<sup>b</sup> <b>{period}, with plan</b> = price + {months} × the "
        "cheapest UK monthly plan that adds cloud recording for one device. "
        "Paying yearly is usually cheaper. The EZVIZ plan figure is the EU "
        "price because EZVIZ shows UK pricing only inside its app. Every "
        "model's sums are under <i>Details</i>."
    ),
    "score": (
        "<b>Free-feature score (out of {score_max}):</b> records for free "
        "(2 = out of the box, 1 = with extra kit or only briefly), free live "
        "view (1), free motion alerts (1), free smart detection (1), storage "
        "included in the box (1), local Home Assistant support (2 = official "
        "and local, 1 = unofficial or generic)."
    ),
    "terms": (
        "<b>Plain terms.</b> <i>PoE</i> (Power over Ethernet) sends power and "
        "video down one network cable. An <i>NVR</i> is a recorder box that "
        "stores footage from several cameras. A <i>microSD</i> card is the "
        "small memory card that sits inside many doorbells or their indoor "
        "chime. <i>2.4 GHz only</i> means the doorbell cannot join a 5 GHz "
        "network, so it will not show up on a phone that is on 5 GHz. "
        "<i>Home Assistant</i> is free software that keeps your smart home on "
        "your own network instead of a manufacturer's cloud."
    ),
    "left_out": (
        "Batteries, electricity, installation (except Hikvision, where the "
        "price includes fitting) and future price rises are left out. Anything "
        "not yet confirmed is listed under <i>Not yet verified</i> in each "
        "model's details."
    ),
    "photos": (
        "Photos are the manufacturers' own, from their product pages: "
        "{credits}.{missing}"
    ),
    "md": [
        "Without a plan: hardware price + anything extra you need to record "
        "for free (a 64 GB SanDisk microSD card at {card} or SanDisk USB stick "
        "at {stick}, each the cheapest UK price we found, at Amazon UK).",
        "With a plan: hardware price + {months} × the cheapest UK monthly plan "
        "that adds recording for one device. Paying yearly is usually cheaper.",
        "Batteries, electricity, installation (except Hikvision, where it's "
        "included) and price rises are left out.",
    ],
}

CSV_HEAD =    [
    "Brand", "Model", "Records free without subscription", "Power",
    "UK price (£)", "Price note", "Price source", "Best for", "Main catch",
    "Free-feature score (/{score_max})", "3-yr cost without subscription (£)",
    "3-yr cost with cheapest plan, monthly (£)",
    "Cheapest 3-yr cost to keep recordings (£)", "Maths: without",
    "Maths: with", "Local storage", "Live view free?", "Motion alerts free?",
    "Smart detection", "Recorded history without subscription",
    "What's paywalled", "Subscription & UK price", "Plan price region",
    "Home Assistant / local-only", "Wi-Fi", "Sources",
    "Unverified / re-check", "Last checked",
]

MD_HEAD = (
    "# UK video doorbells without a subscription",
    "Last checked {checked}. {n} doorbells. No affiliate links.",
    "| Doorbell | Records free? | Price | Score /{score_max} | {period_short}, "
    "no plan | {period_short}, with plan | Best for | Main catch |",
)

NOT_FOUND = {
    "title": "Page not found | SubFree UK",
    "description": "That page does not exist. The UK video doorbell comparison is on the home page.",
    "h1": "Page not found",
    "say": "That link does not lead anywhere. The {what} is on the home page, and it is one page.",
    "what": "comparison of UK video doorbells that record without a subscription",
}


DOORBELLS = {
    "slug": "doorbells",
    "route": "",
    "alias": "doorbells.html",
    "csv": "data/doorbells.csv",
    "md": "data/doorbells.md",
    "page": "index.html",

    "noun": "doorbell",
    "nouns": "doorbells",

    "title": "Video doorbells that work without a subscription (UK)",
    "description": "{n} UK video doorbells compared: what is free, what is paywalled, and what each costs over three years.",
    "h1": "Video doorbells that work without a subscription",
    "dek": "{n} UK doorbells, checked against manufacturer pages and independent reviews: free features, paywalls and {period} costs.",
    "mast": "No subscriptions",
    "mast_long": "Gadgets that work without a subscription",
    "skip": "Skip to the doorbell table",
    "table_name": "Doorbell comparison",
    "table_caption": "{table_name}: {n} models, 8 columns",
    "cmp_caption": "Side-by-side comparison of {count} {nouns}",
    "count_line": "Tick up to {cap} {nouns} to compare.",
    "empty_line": "Nothing matches those filters.",
    "no_match": "No {nouns} match those filters",
    "shown": "{shown} of {total} {nouns} shown",

    "months": 36,
    "period": "3 years",
    "period_adj": "3-year",
    "period_short": "3 yrs",
    "cap": 3,

    # The editorial lead, which is a judgement about this category's rows rather
    # than a figure: `{v:ID:Words}` becomes a link to that row.
    "short": (
        '{v:reo-poe:Reolink PoE} is the best overall without fees.',
        '{v:tapo-d230:Tapo D230S1} is the easiest battery one.',
        '{v:ring:Ring} needs a plan. {v:blink:Blink} and {v:arlo:Arlo} need extra kit.',
    ),
    "short_tones": ("best", "batt", "avoid"),
    "aside": (
        ("best", "Best overall without fees:", "{v:reo-poe:Reolink Video Doorbell PoE}",
         ". It records to a card or NVR, nothing is paywalled, and Reolink is the only "
         "brand here with an official local Home Assistant integration. The WiFi and "
         "battery versions follow the same rules if you can't run an Ethernet cable."),
        ("batt", "Easiest battery pick:", "{v:tapo-d230:Tapo D230S1}",
         ", which keeps footage on a hub inside the house."),
        ("avoid", "Avoid if you won't pay monthly:", "{v:ring:Ring}",
         " records nothing without a plan, and {v:blink:Blink} and {v:arlo:Arlo} need "
         "extra hardware."),
    ),

    "score_max": 8,
    "score_parts": [
        ("rec", "Records free", 2),
        ("live", "Live view free", 1),
        ("alerts", "Motion alerts free", 1),
        ("ai", "Smart detection free", 1),
        ("storage", "Storage in the box", 1),
        ("ha", "Local / Home Assistant", 2),
    ],

    "rec": [
        ("yes", "Yes", 2),
        ("kit", "Only with extra kit", 1),
        ("brief", "Only briefly (3 hrs)", 1),
        ("no", "No", 0),
    ],
    # The keys a row needs beyond the universal ones. The plain-language
    # sentences are attached to the row as `plain` and checked there.
    "required_keys": (
        "power", "wifi", "live", "alerts", "ai", "history", "storage",
        "paywalled",
    ),

    "facets": [
        ("power", "Power"),
        ("storage", "Storage"),
        ("live", "Live view"),
        ("alerts", "Motion alerts"),
        ("ai", "Smart detection"),
        ("history", "History, no plan"),
        ("paywalled", "Behind the paywall"),
        ("ha", "Home Assistant"),
        ("wifi", "Wi-Fi"),
    ],
    "powers": [
        ("battery", "Battery"),
        ("wired", "Wired"),
        ("poe", "PoE"),
    ],
    "power_hint": "PoE: one cable carries both power and data.",
    "filters": [
        ("f-rec", "Records free, no extra kit"),
        ("f-ha", "Local / Home Assistant"),
    ],

    "verdicts": {
        "best": ("Best overall", "best"),
        "wired": ("Best with doorbell wiring", "best"),
        "batt": ("Best battery, no fees", "batt"),
        "easy": ("Easiest battery setup", "batt"),
        "avoid": ("Avoid without a plan", "avoid"),
    },
    # The verdict that heads the page: its row carries the social preview.
    "headline": "best",

    "claims": CLAIM_WHAT,
    "compare": [
        ("Records free?", "rec"),
        ("Price", "price"),
        ("Free features", "score"),
        ("{period_adj} cost, no plan", "nosub3"),
        ("{period_adj} cost, with plan", "sub3"),
        ("Best for", "best"),
        ("Main catch", "catch"),
        ("Power", "power"),
        ("Storage", "storage"),
        ("Live view", "live"),
        ("Motion alerts", "alerts"),
        ("Smart detection", "ai"),
        ("History, no plan", "history"),
        ("Behind the paywall", "paywalled"),
        ("Plans", "plan"),
        ("Home Assistant", "ha"),
        ("Wi-Fi", "wifi"),
    ],
    # The decision rows the comparison pins above its scroller, by key: the two
    # cost rows and the two that decide between them. Listed rather than counted,
    # so re-ordering the rows above cannot silently pin a different four.
    "pin": ("rec", "price", "nosub3", "sub3"),

    "sort": SORT,
    "method": METHOD,
    "plain_part": PLAIN_PART,
    "csv_head": CSV_HEAD,
    "md_head": MD_HEAD,
    "not_found": NOT_FOUND,
}

CATEGORIES = [DOORBELLS]
BY_SLUG = {cat["slug"]: cat for cat in CATEGORIES}


def words(cat):
    """The record's prose with its period written out, once, for every page."""
    out = dict(cat)
    out["sort"] = [
        (key, label.format(period=cat["period"], period_adj=cat["period_adj"]),
         note.format(period=cat["period"], period_adj=cat["period_adj"]))
        for key, label, note in cat["sort"]
    ]
    out["compare"] = [
        (label.format(period=cat["period"], period_adj=cat["period_adj"]), key)
        for label, key in cat["compare"]
    ]
    return out


def rec_by_key(cat):
    return {key: (label, rank) for key, label, rank in cat["rec"]}


def power_labels(cat):
    return dict(cat["powers"])


def facet_keys(cat):
    """Every row field the category makes a decision on, in page order."""
    return {key for key, _ in cat["facets"]}


def score_max(cat):
    return sum(maximum for _, _, maximum in cat["score_parts"])
