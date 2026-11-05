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
    "nosub": "The {period_adj} cost with no plan",
    "plan": "The {period_adj} cost with a plan",
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
# kit figures are filled from the data at build time. Each category writes its
# own, so a camera page cannot inherit a doorbell's warning.
DOORBELL_METHOD = {
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
        "at {stick}, both from Argos).",
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

DOORBELL_MD_HEAD = (
    "# UK video doorbells without a subscription",
    "Last checked {checked}. {n} doorbells. As an Amazon Associate I earn from qualifying purchases.",
    "| Doorbell | Records free? | Price | Score /{score_max} | {period_short}, "
    "no plan | {period_short}, with plan | Best for | Main catch |",
)

CAMERA_METHOD = {
    "no_plan": (
        "<sup>a</sup> <b>{period}, no plan</b> = price + anything you must add "
        "to record for free ({kit}, each the cheapest UK price we found, on a "
        "page that publishes it). Cameras with no free recording are shown next "
        "to the figure."
    ),
    "with_plan": (
        "<sup>b</sup> <b>{period}, with plan</b> = price + {months} × the "
        "cheapest UK monthly plan that adds cloud recording for one camera. "
        "Paying yearly is usually cheaper. A camera that records free without a "
        "plan is still priced against its optional one, so the two columns "
        "compare like with like. Every model's sums are under <i>Details</i>."
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
        "small memory card that sits inside many cameras or their hub. "
        "<i>2.4 GHz only</i> means the camera cannot join a 5 GHz network, so "
        "it will not show up on a phone that is on 5 GHz. <i>Home Assistant</i> "
        "is free software that keeps your smart home on your own network "
        "instead of a manufacturer's cloud."
    ),
    "left_out": (
        "Batteries, electricity, installation and future price rises are left "
        "out. Anything not yet confirmed is listed under <i>Not yet verified</i> "
        "in each model's details."
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
        "that adds recording for one camera. Paying yearly is usually cheaper.",
        "Batteries, electricity, installation and price rises are left out.",
    ],
}

CAMERA_MD_HEAD = (
    "# UK security cameras without a subscription",
    "Last checked {checked}. {n} cameras. As an Amazon Associate I earn from qualifying purchases.",
    "| Camera | Records free? | Price | Score /{score_max} | {period_short}, "
    "no plan | {period_short}, with plan | Best for | Main catch |",
)

# A ring's 3-year figure is the price plus a membership, not a recorder and a
# card, so its score asks different questions and its table has different
# columns. The keys are the same ones the build reads; only the words change.
RING_CLAIMS = {
    "rec": "Works without a subscription",
    "price": "The price",
    "nosub": "The {period_adj} cost with no subscription",
    "plan": "The {period_adj} cost with the membership",
    "history": "The data you keep without a plan",
    "ha": "The Home Assistant line",
}
RING_SORT = [
    ("keep3", "{period_adj} cost to keep the data",
     "Order: {period_adj} cost to keep the data (the bold figure)."),
    ("price", "Price, low to high", "Order: price, low to high."),
    ("score", "Free-data score, high to low", "Order: free-data score, high to low."),
    ("recv", "No subscription first", "Order: no subscription first."),
    ("nosub3", "{period_adj} cost, no subscription",
     "Order: {period_adj} cost with no subscription."),
    ("sub3", "{period_adj} cost, with membership",
     "Order: {period_adj} cost with a membership (the bold figure)."),
    ("model", "Model, A to Z", "Order: model name, A to Z."),
]

RING_METHOD = {
    "no_plan": (
        "<sup>a</sup> <b>{period}, no subscription</b> = the ring's price, "
        "because no maker charges for the app itself. What the free tier "
        "keeps differs: Oura keeps three daily scores, and the other rings "
        "keep their full data. Each row says which."
    ),
    "with_plan": (
        "<sup>b</sup> <b>{period}, with membership</b> = the price + {months} × "
        "the cheapest monthly membership. Only Oura charges one: £5.99 a "
        "month, or £69.99 a year, which works out cheaper. A ring with no "
        "membership says so in that column, so the two totals compare like "
        "with like. Every ring's sums are under <i>Details</i>."
    ),
    "offers": (
        "<b>Where to buy.</b> Each ring is sold by more than one UK shop, and "
        "its price moves with size and finish, so every offer names the one it "
        "is for. The price shown is the cheapest we found, unless a second shop "
        "is within £5 of it and pays us more — then that shop is shown, and the "
        "link on the price goes to it. A shop paying us never adds more than "
        "£5 to the price of a ring."
    ),
    "score": (
        "<b>Free-data score (out of {score_max}):</b> works without a "
        "subscription (2 = every core metric free, 1 = scores only or a free "
        "trial, 0 = a membership is required), sleep detail free (1), heart "
        "rate free (1), SpO2 and temperature free (1), advanced "
        "insights free (1), local Home Assistant support (2 = official and "
        "local, 1 = unofficial or cloud)."
    ),
    "terms": (
        "<b>Plain terms.</b> A <i>smart ring</i> is a finger-worn tracker with "
        "no screen: it sends what it measures to a phone app. <i>HRV</i> "
        "(heart-rate variability) is the variation between heartbeats, used as "
        "a recovery signal. <i>SpO2</i> is blood-oxygen saturation. A "
        "<i>membership</i> is the subscription some brands charge before the app "
        "shows its detailed data. <i>Home Assistant</i> is free software that "
        "keeps your smart home on your own network instead of a manufacturer's "
        "cloud."
    ),
    "left_out": (
        "A phone, electricity, sizing kits and future price rises are left out. "
        "Anything not yet confirmed is listed under <i>Not yet verified</i> in "
        "each ring's details."
    ),
    "photos": (
        "Photos are the manufacturers' own, from their product pages: "
        "{credits}.{missing}"
    ),
    "md": [
        "With no subscription: the ring's price, because no maker charges for "
        "the app itself. Oura's free tier keeps three daily scores; the other "
        "rings keep their full data.",
        "With a membership: price + {months} × the cheapest monthly membership "
        "(Oura's £5.99). Paying yearly is cheaper.",
        "A phone, electricity, sizing kits and price rises are left out.",
        "Where to buy: the cheapest offer checked, or a second shop within £5 "
        "of it that pays us more (never more than £5 dearer).",
    ],
}

RING_MD_HEAD = (
    "# UK smart rings that work without a subscription",
    "Last checked {checked}. {n} smart rings. As an Amazon Associate I earn from qualifying purchases.",
    "| Smart ring | Subscription? | Price | Score /{score_max} | {period_short}, "
    "no subscription | {period_short}, with membership | Best for | Main catch |",
)

RING_CSV_HEAD = [
    "Brand", "Model", "Subscription needed?", "Battery",
    "UK price (£)", "Price note", "Price source", "Best for", "Main catch",
    "Free-data score (/{score_max})", "3-yr cost without subscription (£)",
    "3-yr cost with membership, monthly (£)",
    "Cheapest 3-yr cost to keep the data (£)", "Maths: without",
    "Maths: with", "Where the data lives", "Live heart rate free?",
    "Wellness alerts free?", "Sleep & recovery insights",
    "Data history without a subscription", "What's paywalled",
    "Membership & UK price", "Membership price region",
    "Home Assistant / local-only", "Works with", "Sources",
    "Unverified / re-check", "Last checked",
]

RING_LABELS = {
    "rec_col": "Subscription?",
    "score_col": "Free data",
    "nosub_col": "{period_adj} cost, no subscription",
    "sub_col": "{period_adj} cost, with membership",
    "nosub_how": "{period_adj} cost without a subscription",
    "sub_how": "{period_adj} cost with the membership",
    "detail": {
        "power": "Battery", "wifi": "Works with",
        "storage": "Where the data lives", "live": "Live heart rate",
        "alerts": "Wellness alerts", "ai": "Sleep & recovery insights",
        "history": "Data without a plan", "paywalled": "Behind the membership",
        "plans": "Membership", "nosub": "{period}, no subscription",
        "sub": "{period}, with membership",
    },
    "rec_note": {
        "yes": "", "brief": "scores only", "no": "membership only",
    },
    "keep_sub_note": "cheapest for this ring: with membership",
    "keep_free": "no subscription, nothing more to pay",
    "maths_no_route": " (but no data without a membership)",
    "maths_brief": " (three daily scores only)",
    "no_plan_cell": "No membership",
    "footer": "to show which ones work without a subscription",
    "rec_filter_why": "none works without a subscription",
    "ha_filter_why": "none works with Home Assistant",
    "keep_label": "Cheapest way to keep the data for {period}",
    "md": {
        "storage": "Where the data lives",
        "free": "Free",
        "free_line": "live heart rate: {live}; wellness alerts: {alerts}; "
                     "sleep and recovery insights: {ai}",
        "free_lower": False,
        "history": "Data without a plan",
        "paywalled": "Behind the membership",
        "plans": "Membership",
        "ha": "Home Assistant",
        "unverified": "Not yet verified",
    },
}

# The labels the shared table and details panel print. A category carries its
# own words where they differ; the doorbells' are the default, because that was
# the page before there were categories. `labels()` merges a record's overrides
# one level into the nested maps, so a ring record can change `detail.power` to
# "Battery" without restating the other eleven rows.
DEFAULT_LABELS = {
    "rec_col": "Records free?",
    "score_col": "Free features",
    "nosub_col": "{period_adj} cost, no plan",
    "sub_col": "{period_adj} cost, with plan",
    "nosub_how": "{period_adj} cost without a plan",
    "sub_how": "{period_adj} cost with a plan",
    "catch_col": "Main catch",
    "detail": {
        "power": "Power", "wifi": "Wi-Fi", "storage": "Storage",
        "live": "Live view", "alerts": "Motion alerts",
        "ai": "Smart detection", "history": "History without a plan",
        "paywalled": "Behind the paywall", "plans": "Plans",
        "ha": "Home Assistant", "score": "Score breakdown",
        "nosub": "{period}, no plan", "sub": "{period}, with plan",
    },
    "rec_note": {
        "yes": "", "kit": "extra kit needed", "brief": "3 hrs history",
        "no": "no recordings",
    },
    "keep_sub_note": "cheapest for this model: with plan",
    "keep_free": "records free, no plan",
    "maths_no_route": " (but no recordings)",
    "maths_brief": " (3 hours of history only)",
    "no_plan_cell": "No plan",
    "no_plan_note": "No subscription offered or needed",
    "footer": "to show which ones record without a subscription",
    "rec_filter_why": "none records free with no extra kit",
    "ha_filter_why": "none works locally with Home Assistant",
    "keep_label": "Cheapest way to record for {period}",
    "md": {
        "storage": "Storage",
        "free": "Free",
        "free_line": "live view {live}; alerts {alerts}; smart detection: {ai}",
        "history": "History without plan",
        "paywalled": "Paywalled",
        "plans": "Plans",
        "ha": "Home Assistant",
        "unverified": "Unverified",
    },
}


def labels(cat):
    """A category's labels: the default words with the record's overrides."""
    out = {}
    for source in (DEFAULT_LABELS, cat.get("labels") or {}):
        for key, value in source.items():
            if isinstance(value, dict):
                out.setdefault(key, {})
                out[key].update(value)
            else:
                out[key] = value
    return out


# The CSV's columns, in order, named by the meaning each one carries. The
# header words are the category's; the check reads a figure back by this key
# rather than by an English label that a second category may word differently.
CSV_KEYS = (
    "brand", "model", "rec", "power", "price", "price_note", "price_src",
    "best", "catch", "score_total", "nosub3", "sub3", "keep3", "maths_free",
    "maths_sub", "storage", "live", "alerts", "ai", "history", "paywalled",
    "sub_text", "plan_region", "ha_text", "wifi", "sources", "unverified",
    "checked",
)

NOT_FOUND = {
    "title": "Page not found | SubFree UK",
    "description": "That page does not exist. The UK comparisons are on the home page, the cameras page, the smart rings page and the printers page.",
    "h1": "Page not found",
    "say": "That link does not lead anywhere. The {what} are on the home page, the cameras page, the smart rings page and the printers page.",
    "what": "comparisons of UK video doorbells, security cameras, smart rings and printers that work without a subscription",
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
    "nav": "Doorbells",
    "checked_iso": "2026-11-02",

    # Each brand's newest model in this category, read from the vendor's own UK
    # store. Where a brand sells more than one newest model — a battery and a
    # wired version, say — the entry names the one this table covers. The table
    # carries the newest model, not merely a model still on sale: a page that
    # names last year's doorbell is the gap this map exists to catch. A pair
    # records a brand whose current product is not a consumer doorbell at all,
    # with the reason.
    "current": {
        "Ring": "ring-4kpro",
        "Google Nest": "nest",
        "eufy": "eufy-s4",
        "Reolink": "reo-wifi",
        "TP-Link Tapo": "tapo-d260",
        "Arlo": "arlo",
        "Aqara": "aqara-g410",
        "Blink": "blink",
        "EZVIZ": "ezviz-ep3x",
        "Hikvision": (
            "DS-KB6003-WIP",
            "discontinued: Hikvision's UK catalogue lists wired video-intercom "
            "door stations, and both of its Wi-Fi doorbells are end of life",
        ),
    },

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
    # What the plan column says when the row has no plan to price.
    "no_plan_note": "No subscription offered or needed",

    # The editorial lead, which is a judgement about this category's rows rather
    # than a figure: `{v:ID:Words}` becomes a link to that row.
    # `{p:ID}`, `{c:ID}` and `{k:ID}` print a row's price, its no-plan 3-year
    # cost and its cheaper 3-year cost, rounded to the pound, so the short answer
    # never drifts from the table.
    "short": (
        'Wired doorbell: {v:reo-wifi:Reolink WiFi}, {p:reo-wifi}',
        'Renting or no wires: {v:tapo-d235:Tapo D235}, {p:tapo-d235}',
        'Cheapest that records free: {v:tapo-td21:Tapo TD21}, {p:tapo-td21}',
        '{v:ring:Ring} needs a plan. {v:blink:Blink} and {v:arlo:Arlo} need extra kit.',
    ),
    "short_tones": ("pick", "pick", "pick", "avoid"),
    "short_head": "Short answer: which to buy",
    "aside": (
        ("pick", "Already have a wired doorbell:", "{v:reo-wifi:Reolink WiFi}",
         ", {p:reo-wifi} ({c:reo-wifi} over 3 yrs). Same wires, records to a card (or the {v:reo-poe:PoE}, {p:reo-poe}, if you can run a cable)."),
        ("pick", "Renting or no wires:", "{v:tapo-d235:Tapo D235}",
         ", {p:tapo-d235} ({c:tapo-d235}). Battery, or hardwired for 24/7."),
        ("pick", "Cheapest that records free:", "{v:tapo-td21:Tapo TD21}",
         ", {p:tapo-td21} ({c:tapo-td21}). Basic, card sits in the doorbell."),
        ("avoid", "Avoid if you won't pay monthly:", "{v:ring:Ring}",
         " records nothing without a plan; {v:blink:Blink} and {v:arlo:Arlo} need extra kit."),
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
    "method": DOORBELL_METHOD,
    "plain_part": PLAIN_PART,
    "csv_head": CSV_HEAD,
    "md_head": DOORBELL_MD_HEAD,
    "not_found": NOT_FOUND,
}

CAMERAS = {
    "slug": "cameras",
    "route": "cameras/",
    "alias": None,
    "csv": "data/cameras.csv",
    "md": "data/cameras.md",
    "page": "cameras/index.html",

    "noun": "security camera",
    "nouns": "security cameras",
    "nav": "Cameras",
    "checked_iso": "2026-11-05",

    # Each brand's newest model in this category, read from the vendor's own UK
    # store. Where a brand sells more than one newest model, the entry names the
    # one this table covers.
    "current": {
        "Reolink": "reo-argus4",
        "TP-Link Tapo": "tapo-c660",
        "eufy": "eufy-s340",
        "Aqara": "aqara-g100",
        "Ring": "ring-outpro",
        "Blink": "blink-out2k",
    },

    "title": "Security cameras that work without a subscription (UK)",
    "description": "{n} UK security cameras compared: what is free, what is paywalled, and what each costs over three years.",
    "h1": "Security cameras that work without a subscription",
    "dek": "{n} UK security cameras, checked against manufacturer pages: free features, paywalls and {period} costs.",
    "mast": "No subscriptions",
    "mast_long": "Gadgets that work without a subscription",
    "skip": "Skip to the camera table",
    "table_name": "Security camera comparison",
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
    "no_plan_note": "No plan needed: the free route keeps the recording",

    # The editorial lead, which is a judgement about this category's rows rather
    # than a figure: `{v:ID:Words}` becomes a link to that row.
    "short": (
        '{v:reo-rlc820a:Reolink RLC-820A} is the best overall without fees.',
        '{v:reo-argus4:Reolink Argus 4 Pro} is the best wire-free one.',
        '{v:ring-outpro:Ring} records nothing without a plan, and {v:blink-out2k:Blink} needs extra kit.',
    ),
    "short_tones": ("best", "batt", "avoid"),
    "short_head": "The short answer",
    "aside": (
        ("best", "Best overall without fees:", "{v:reo-rlc820a:Reolink RLC-820A}",
         ". It records 4K to a card or NVR, detection is free and Reolink's Home "
         "Assistant integration is fully local. It needs a PoE switch or injector "
         "and an Ethernet run to the camera."),
        ("batt", "Best wire-free pick:", "{v:reo-argus4:Reolink Argus 4 Pro}",
         ", which covers 180° from one battery camera and still records to a card "
         "without a plan."),
        ("avoid", "Avoid if you won't pay monthly:", "{v:ring-outpro:Ring}",
         " records nothing without a plan, and {v:blink-out2k:Blink} needs a Sync "
         "Module 2 and a USB stick before it saves a clip."),
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
        "ptz": ("Best for a wide garden", "batt"),
        "solar": ("Best solar", "batt"),
        "batt": ("Best wire-free", "batt"),
        "indoor": ("Best indoor", "batt"),
        "value": ("Best value", "batt"),
        "avoid": ("Avoid without a plan", "avoid"),
    },
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
    "pin": ("rec", "price", "nosub3", "sub3"),

    "sort": SORT,
    "method": CAMERA_METHOD,
    "plain_part": PLAIN_PART,
    "csv_head": CSV_HEAD,
    "md_head": CAMERA_MD_HEAD,
    "not_found": NOT_FOUND,
}

RINGS = {
    "slug": "rings",
    "route": "rings/",
    "alias": None,
    "csv": "data/rings.csv",
    "md": "data/rings.md",
    "page": "rings/index.html",

    "noun": "smart ring",
    "nouns": "smart rings",
    "nav": "Smart rings",
    "checked_iso": "2026-11-05",

    # The model each brand is selling now, as of the date above. A brand in the
    # table with no entry here fails `category records`, so a lineup cannot be
    # left un-asked: the gap that shipped a page of Ring 4 with Ring 5 already
    # on sale was nobody being made to answer this question per brand.
    "current": {
        "Oura": "oura-5",
        "RingConn": "rc-3",
        "Ultrahuman": "ultra-air",
        "Samsung": "samsung-ring",
        "Amazfit": "amazfit-helio",
    },

    "title": "Smart rings that work without a subscription (UK)",
    "description": "{n} UK smart rings compared: what each tracks without a membership, what is paywalled, and what it costs over three years.",
    "h1": "Smart rings that work without a subscription",
    "dek": "{n} UK smart rings, checked against manufacturer pages and UK prices: free data, memberships and {period} costs.",
    "mast": "No subscriptions",
    "mast_long": "Gadgets that work without a subscription",
    "skip": "Skip to the smart ring table",
    "table_name": "Smart ring comparison",
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
    "no_plan_note": "No membership offered or needed",

    "short": (
        '{v:rc-3:RingConn Gen 3} is the best overall without a subscription.',
        '{v:rc-2:RingConn Gen 2} is the best value.',
        '{v:oura-5:Oura Ring 5} needs a £5.99 monthly membership for its detail.',
    ),
    "short_tones": ("best", "batt", "avoid"),
    "short_head": "The short answer",
    "aside": (
        ("best", "Best overall without a subscription:", "{v:rc-3:RingConn Gen 3}",
         ". It tracks sleep, HRV, SpO2, temperature and overnight vascular trends, "
         "lasts up to 14 days and adds nothing to the price. It has no Home "
         "Assistant integration."),
        ("batt", "Best value:", "{v:rc-2:RingConn Gen 2}",
         ", which keeps its data free for {p:rc-2}, adds the sleep-apnea "
         "insights the Air leaves out, and lasts up to 12 days on a charge."),
        ("avoid", "Avoid if you won't pay monthly:", "{v:oura-5:Oura Ring 5}",
         " shows only three daily scores without its membership; the sleep "
         "stages, HRV, SpO2 and trends need £5.99 a month. The {v:oura-4:Ring 4}"
         " is the same ring a generation back, for {p:oura-4}."),
    ),

    "score_max": 8,
    "score_parts": [
        ("rec", "No subscription", 2),
        ("sleep", "Sleep detail free", 1),
        ("hr", "Heart rate free", 1),
        ("spo2", "SpO2 & temperature free", 1),
        ("extra", "Advanced insights free", 1),
        ("ha", "Local / Home Assistant", 2),
    ],

    "rec": [
        ("yes", "No subscription", 2),
        ("brief", "Scores only without a plan", 1),
        ("no", "Membership required", 0),
    ],
    "required_keys": (
        "power", "wifi", "live", "alerts", "ai", "history", "storage",
        "paywalled",
    ),

    "facets": [
        ("power", "Battery"),
        ("wifi", "Works with"),
        ("storage", "Where the data lives"),
        ("live", "Live heart rate"),
        ("alerts", "Wellness alerts"),
        ("ai", "Sleep & recovery insights"),
        ("history", "Data without a plan"),
        ("paywalled", "Behind the membership"),
        ("ha", "Home Assistant"),
    ],
    "powers": [
        ("four", "Up to 4 days"),
        ("six", "Up to 6 days"),
        ("seven", "Up to 7 days"),
        ("eight", "Up to 8 days"),
        ("nine", "Up to 9 days"),
        ("ten", "Up to 10 days"),
        ("twelve", "Up to 12 days"),
        ("fourteen", "Up to 14 days"),
    ],
    "power_hint": "Battery life is the maker's figure with the main features on, unless the row says otherwise.",
    # Seven exact battery buckets is too many to tick. The filter offers three
    # bands that cover every bucket once, while the table still prints the
    # maker's exact figure.
    "power_filters": [
        ("up to 6 days", ("four", "six")),
        ("7 to 10 days", ("seven", "eight", "nine", "ten")),
        ("over 10 days", ("twelve", "fourteen")),
    ],
    "filters": [
        ("f-rec", "Works without a subscription"),
        ("f-ha", "Home Assistant"),
    ],

    "verdicts": {
        "best": ("Best overall", "best"),
        "value": ("Best value", "batt"),
        "ha": ("Best for Home Assistant", "batt"),
        "galaxy": ("Best for Samsung phones", "batt"),
        "budget": ("Cheapest", "batt"),
        "avoid": ("Avoid without a membership", "avoid"),
    },
    "headline": "best",

    "claims": RING_CLAIMS,
    "compare": [
        ("Subscription?", "rec"),
        ("Price", "price"),
        ("Free data", "score"),
        ("{period_adj} cost, no subscription", "nosub3"),
        ("{period_adj} cost, with membership", "sub3"),
        ("Best for", "best"),
        ("Main catch", "catch"),
        ("Battery", "power"),
        ("Where the data lives", "storage"),
        ("Live heart rate", "live"),
        ("Wellness alerts", "alerts"),
        ("Sleep & recovery insights", "ai"),
        ("Data without a plan", "history"),
        ("Behind the membership", "paywalled"),
        ("Membership", "plan"),
        ("Home Assistant", "ha"),
        ("Works with", "wifi"),
    ],
    "pin": ("rec", "price", "nosub3", "sub3"),

    "sort": RING_SORT,
    "method": RING_METHOD,
    "plain_part": PLAIN_PART,
    "labels": RING_LABELS,
    "csv_head": RING_CSV_HEAD,
    "md_head": RING_MD_HEAD,
    "not_found": NOT_FOUND,
}

PRINTER_METHOD = {
    "no_plan": (
        "<sup>a</sup> <b>{period}, retail ink</b> = the printer's price + "
        "{months} months of original cartridges at 100 pages a month (50 mono, "
        "50 colour), priced from the maker's own UK cartridge pages and ISO "
        "yields. A tank printer is priced at its price alone, because the "
        "bottles in the box cover the whole period. Starter cartridges are "
        "left out of both routes, so a cartridge figure is an upper bound."
    ),
    "with_plan": (
        "<sup>b</sup> <b>{period}, with an ink plan</b> = the printer's price "
        "+ {months} × the cheapest UK monthly plan that covers 100 pages. A "
        "printer with no plan to price says <i>No plan needed</i>, because its "
        "bottles are the ink route. Every printer's sums are under "
        "<i>Details</i>."
    ),
    "score": (
        "<b>No-plan score (out of {score_max}):</b> prints on retail ink "
        "without an account (2 = standard cartridges or bottles, 1 = original "
        "ink only, 0 = a plan or account is required), print speed (1), "
        "automatic double-sided printing (1), scan and copy (1), ink included "
        "in the box (1), prints without an account (2 = no account at all, "
        "1 = an app is optional, 0 = an account is required)."
    ),
    "terms": (
        "<b>Plain terms.</b> An <i>ink plan</i> is a monthly payment that posts "
        "cartridges or tops up a tank before you run out. A <i>tank</i> printer "
        "has refillable reservoirs and comes with bottles instead of "
        "cartridges. <i>Yield</i> is the number of pages a cartridge or bottle "
        "prints to the ISO/IEC standard. <i>Duplex</i> means printing on both "
        "sides of the sheet."
    ),
    "left_out": (
        "Paper, electricity, delivery and future price rises are left out. "
        "Anything not yet confirmed is listed under <i>Not yet verified</i> in "
        "each printer's details."
    ),
    "photos": (
        "Photos are the manufacturers' own, from their product pages: "
        "{credits}.{missing}"
    ),
    "md": [
        "Retail ink: printer price + {months} months of original cartridges at "
        "100 pages a month (50 mono, 50 colour), from the maker's UK cartridge "
        "prices and ISO yields. A tank is priced at its price alone, because "
        "the bottles in the box cover the period.",
        "With an ink plan: printer price + {months} × the cheapest UK monthly "
        "plan that covers 100 pages. A printer with no plan to price says so.",
        "Starter cartridges are left out of both routes, so a cartridge figure "
        "is an upper bound. Paper, electricity, delivery and price rises are "
        "left out.",
    ],
}

PRINTER_MD_HEAD = (
    "# UK printers that work without an ink subscription",
    "Last checked {checked}. {n} printers. As an Amazon Associate I earn from qualifying purchases.",
    "| Printer | Retail ink? | Price | Score /{score_max} | {period_short}, "
    "retail ink | {period_short}, with plan | Best for | Main catch |",
)

PRINTER_CSV_HEAD = [
    "Brand", "Model", "Retail ink without a plan?", "Ink system",
    "UK price (£)", "Price note", "Price source", "Best for", "Main catch",
    "No-plan score (/{score_max})", "3-yr cost, retail ink (£)",
    "3-yr cost with ink plan, monthly (£)",
    "Cheaper 3-yr cost (£)", "Maths: retail ink", "Maths: with plan",
    "Ink in the box", "Print speed", "Double-sided", "Scan and copy",
    "Ink without a plan", "With an ink plan", "Ink plan & UK price",
    "Plan price region", "Account needed", "Connectivity", "Sources",
    "Unverified / re-check", "Last checked",
]

PRINTER_LABELS = {
    "rec_col": "Retail ink?",
    "score_col": "No-plan score",
    "nosub_col": "{period_adj} cost, retail ink",
    "sub_col": "{period_adj} cost, with plan",
    "nosub_how": "{period_adj} cost on retail ink",
    "sub_how": "{period_adj} cost with an ink plan",
    "detail": {
        "power": "Ink system", "wifi": "Connectivity",
        "storage": "Ink in the box", "live": "Print speed",
        "alerts": "Double-sided", "ai": "Scan and copy",
        "history": "Ink without a plan", "paywalled": "With an ink plan",
        "plans": "Ink plans", "ha": "Account needed",
        "nosub": "{period}, retail ink", "sub": "{period}, with plan",
    },
    "rec_note": {
        "yes": "", "kit": "extra kit needed", "brief": "original ink only",
        "no": "ink plan only",
    },
    "keep_sub_note": "cheaper for this printer: with an ink plan",
    "keep_free": "retail ink is cheaper, nothing more to pay",
    "maths_no_route": " (but no ink without a plan)",
    "maths_brief": " (original ink only)",
    "no_plan_cell": "No plan needed",
    "no_plan_note": "No ink plan offered or needed",
    "footer": "to show which printers run without an ink subscription",
    "rec_filter_why": "none takes standard retail ink without an account",
    "ha_filter_why": "none prints without an account",
    "keep_label": "Cheaper way to print for {period}",
    "md": {
        "storage": "Ink in the box",
        "free": "Included",
        "free_line": "{live}; double-sided: {alerts}; scan and copy: {ai}",
        "free_lower": False,
        "history": "Ink without a plan",
        "paywalled": "With an ink plan",
        "plans": "Ink plans",
        "ha": "Account needed",
        "unverified": "Not yet verified",
    },
}

PRINTER_SORT = [
    ("keep3", "{period_adj} cost to print",
     "Order: {period_adj} cost to print (the bold figure)."),
    ("price", "Price, low to high", "Order: price, low to high."),
    ("score", "No-plan score, high to low", "Order: no-plan score, high to low."),
    ("recv", "Takes retail ink first", "Order: takes retail ink first."),
    ("nosub3", "{period_adj} cost, retail ink",
     "Order: {period_adj} cost on retail ink."),
    ("sub3", "{period_adj} cost, with an ink plan",
     "Order: {period_adj} cost with an ink plan."),
    ("model", "Model, A to Z", "Order: model name, A to Z."),
]

PRINTERS = {
    "slug": "printers",
    "route": "printers/",
    "alias": None,
    "csv": "data/printers.csv",
    "md": "data/printers.md",
    "page": "printers/index.html",

    "noun": "printer",
    "nouns": "printers",
    "nav": "Printers",
    "checked_iso": "2026-11-05",

    # The model each brand sells now, as of the date above. HP's Envy is the
    # newest Envy all-in-one; Brother's J1310DW is the current small inkjet;
    # Epson's ET-2951 replaced the discontinued ET-2850; Canon's G3590 is the
    # current 3-in-1 MegaTank, with the cartridge TS6550i covered beside it.
    "current": {
        "HP": "hp-envy-6530e",
        "Brother": "brother-dcp-j1310dw",
        "Epson": "epson-et-2951",
        "Canon": "canon-pixma-g3590",
    },

    "title": "Printers that work without an ink subscription (UK)",
    "description": "{n} UK printers compared: what the ink costs without a plan, what a plan adds, and which is cheaper over three years.",
    "h1": "Printers that work without an ink subscription",
    "dek": "{n} UK printers, checked against manufacturer pages and UK prices: ink costs, plans and {period} totals.",
    "mast": "No subscriptions",
    "mast_long": "Gadgets that work without a subscription",
    "skip": "Skip to the printer table",
    "table_name": "Printer comparison",
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
    "no_plan_note": "No ink plan offered or needed",

    "short": (
        "{v:canon-pixma-g3590:Canon PIXMA G3590} is the best overall without an ink plan. It costs {p:canon-pixma-g3590} and its bottles cover three years.",
        "{v:canon-pixma-ts6550i:Canon PIXMA TS6550i} costs {p:canon-pixma-ts6550i}, and its £4.49 plan brings three years to {k:canon-pixma-ts6550i}.",
        "{v:epson-et-2951:Epson EcoTank ET-2951} is the fastest tank at {p:epson-et-2951}, printing 15 mono pages a minute.",
        "{v:brother-dcp-j1310dw:Brother DCP-J1310DW} is the cheapest cartridge printer on retail ink at {c:brother-dcp-j1310dw} over 3 years.",
        "{v:hp-envy-6530e:HP Envy 6530e} needs an HP account, and retail ink takes it to {c:hp-envy-6530e}.",
    ),
    "short_tones": ("best", "pick", "pick", "pick", "avoid"),
    "short_head": "The short answer",
    "aside": (
        ("best", "Best overall without an ink plan:", "{v:canon-pixma-g3590:Canon PIXMA G3590}",
         " costs {p:canon-pixma-g3590}. Its four bottles cover 3,600 pages, double-sided printing is automatic, and nothing needs an account."),
        ("batt", "Cheapest with an ink plan:", "{v:canon-pixma-ts6550i:Canon PIXMA TS6550i}",
         " costs {p:canon-pixma-ts6550i}, and £4.49 a month covers 100 pages; three years come to {k:canon-pixma-ts6550i}."),
        ("batt", "Fastest tank:", "{v:epson-et-2951:Epson EcoTank ET-2951}",
         " costs {p:epson-et-2951} and prints 15 mono and 8 colour pages a minute."),
        ("batt", "Cheapest cartridge ink:", "{v:brother-dcp-j1310dw:Brother DCP-J1310DW}",
         " costs {c:brother-dcp-j1310dw} over 3 years with EcoPro, and its cartridges print 500 pages each."),
        ("avoid", "Dearest to run:", "{v:hp-envy-6530e:HP Envy 6530e}",
         " costs {p:hp-envy-6530e}, but retail ink takes it to {c:hp-envy-6530e}, and HP+ requires an account."),
    ),

    "score_max": 8,
    "score_parts": [
        ("rec", "Takes retail ink", 2),
        ("storage", "Ink in the box", 1),
        ("live", "Print speed", 1),
        ("alerts", "Double-sided", 1),
        ("ai", "Scan and copy", 1),
        ("ha", "No account needed", 2),
    ],

    "rec": [
        ("yes", "Yes", 2),
        ("brief", "Original ink only", 1),
        ("no", "Plan only", 0),
    ],
    "required_keys": (
        "power", "wifi", "live", "alerts", "ai", "history", "storage",
        "paywalled",
    ),

    "facets": [
        ("power", "Ink system"),
        ("wifi", "Connectivity"),
        ("storage", "Ink in the box"),
        ("live", "Print speed"),
        ("alerts", "Double-sided"),
        ("ai", "Scan and copy"),
        ("history", "Ink without a plan"),
        ("paywalled", "With an ink plan"),
        ("ha", "Account needed"),
    ],
    "powers": [
        ("tank", "Refillable tanks"),
        ("cart", "Cartridges"),
    ],
    "power_hint": "A tank refills from bottles; a cartridge printer takes sealed cartridges.",
    "filters": [
        ("f-rec", "Retail ink, no account"),
        ("f-ha", "Prints without an account"),
    ],

    "verdicts": {
        "best": ("Best overall", "best"),
        "plan": ("Cheapest with a plan", "batt"),
        "fast": ("Fastest tank", "batt"),
        "retail": ("Cheapest cartridge ink", "batt"),
        "avoid": ("Dearest to run", "avoid"),
    },
    "headline": "best",

    "claims": CLAIM_WHAT,
    "compare": [
        ("Retail ink?", "rec"),
        ("Price", "price"),
        ("No-plan score", "score"),
        ("{period_adj} cost, retail ink", "nosub3"),
        ("{period_adj} cost, with plan", "sub3"),
        ("Best for", "best"),
        ("Main catch", "catch"),
        ("Ink system", "power"),
        ("Ink in the box", "storage"),
        ("Print speed", "live"),
        ("Double-sided", "alerts"),
        ("Scan and copy", "ai"),
        ("Ink without a plan", "history"),
        ("With an ink plan", "paywalled"),
        ("Ink plans", "plan"),
        ("Account needed", "ha"),
        ("Connectivity", "wifi"),
    ],
    "pin": ("rec", "price", "nosub3", "sub3"),

    "sort": PRINTER_SORT,
    "method": PRINTER_METHOD,
    "plain_part": PLAIN_PART,
    "labels": PRINTER_LABELS,
    "csv_head": PRINTER_CSV_HEAD,
    "md_head": PRINTER_MD_HEAD,
    "not_found": NOT_FOUND,
}

CATEGORIES = [DOORBELLS, CAMERAS, RINGS, PRINTERS]
BY_SLUG = {cat["slug"]: cat for cat in CATEGORIES}


def _written(value, cat):
    """A label's placeholders filled, recursively, so no page formats them."""
    if isinstance(value, str):
        # Only the period's two placeholders are the record's to fill. A label
        # that carries another field's placeholder, such as the markdown free
        # line, is left for the page that has that row.
        return (value.replace("{period_adj}", cat["period_adj"])
                .replace("{period}", cat["period"]))
    if isinstance(value, dict):
        return {key: _written(item, cat) for key, item in value.items()}
    return value


def words(cat):
    """The record's prose with its period written out, once, for every page."""
    out = dict(cat)
    out["labels"] = _written(labels(cat), cat)
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
