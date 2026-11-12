#!/usr/bin/env python3
"""The Monday lineup report: products a brand's feed carries that the page does not.

This reads the two Shopify product feeds the audit found, keeps the products
whose titles name the category, drops accessories and bundles, and prints the
remainder as links for a person to triage. It never edits the dataset or a
price. A product already named by a row or a lineup entry is not repeated; a
product a person has dismissed is named in `lineup_ignore.json` with the reason
recorded beside it.

The feed is a report, not a gate: a model the page should carry is an editorial
call, and a product's title is not enough to make it. A feed that cannot be read
is printed as unavailable and does not stop the price issue.

    python build/lineup_feed.py
"""

import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from catalog import CATEGORIES

import rows

HERE = os.path.dirname(os.path.abspath(__file__))
IGNORE = os.path.join(HERE, "lineup_ignore.json")

# Accessories and bundles carry the category noun in their titles but are not
# models a reader chooses between. A base model sold with a chime or an adapter
# appears again as the base product, so the bundle is not the lineup signal.
NOT_A_MODEL = (
    "spare", "kit", "mount", "faceplate", "charger", "adapter", "adaptor",
    "cable", "transformer", "resistor", "wedge", "corner", "retrofit", "solar",
    "battery pack", "quick release", "no drill", "no-drill", "intercom",
    "chime", "hub", "bundle", "+",
)

FEEDS = {
    "Ring": (
        "doorbells",
        "https://en-uk.ring.com/products.json?limit=250",
        "https://en-uk.ring.com/products/",
    ),
    "Tapo": (
        "doorbells",
        "https://uk.store.tapo.com/products.json?limit=250",
        "https://uk.store.tapo.com/products/",
    ),
}


def normal(text):
    """A title reduced to the words that identify the model."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def known_models(cat):
    """Every model the rows and the lineup maps already name, normalised."""
    cat_rows = [row for row in rows.ROWS if row["cat"] == cat["slug"]]
    by_id = {row["id"]: row["model"] for row in cat_rows}
    found = {normal(row["model"]) for row in cat_rows}
    handles = set()
    for row in cat_rows:
        # A row id with a model number is a second, precise match for a feed
        # handle: Tapo's D260 row is "Doorbell Pro (D260)" but its handle is
        # "tapo-d260-4k-video-doorbell". A prefix such as D235 must not swallow
        # the newer D235L, so the id has to end at a hyphen or the handle's end.
        if re.search(r"[0-9]", row["id"]):
            handles.add(row["id"])
    for key in ("current", "previous"):
        for named in (cat.get(key) or {}).values():
            if isinstance(named, str):
                found.add(normal(by_id.get(named, "")))
            elif isinstance(named, tuple) and named and named[0]:
                found.add(normal(str(named[0])))
    return found, handles


def ignored(brand):
    if not os.path.exists(IGNORE):
        return set()
    with open(IGNORE, encoding="utf-8") as handle:
        data = json.load(handle)
    return {normal(title) for title in data.get(brand, ())}


def feed(url):
    request = urllib.request.Request(url, headers={"User-Agent": "SubFree-UK lineup check"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response).get("products", ())


def candidates(cat, brand, products):
    known, handles = known_models(cat)
    skip = ignored(brand)
    noun = cat["noun"].lower()
    out = []
    for product in products:
        title = str(product.get("title", "")).strip()
        lower = title.lower()
        if noun not in lower or any(word in lower for word in NOT_A_MODEL):
            continue
        key = normal(title)
        handle = str(product.get("handle", ""))
        claimed = any(
            re.search(rf"(^|-){re.escape(row_id)}(-|$)", handle)
            for row_id in handles
        )
        if key in known or key in skip or claimed:
            continue
        out.append((title, handle))
    return out


def main():
    by_slug = {cat["slug"]: cat for cat in CATEGORIES}
    print("### Lineup feed\n")
    print("Products on a brand's feed that are neither a row nor a lineup entry. "
          "Accessories and bundles are omitted; a person decides whether a model "
          "belongs on the page.\n")
    for brand, (slug, url, base) in FEEDS.items():
        cat = by_slug.get(slug)
        if not cat:
            continue
        try:
            products = feed(url)
        except Exception as error:
            print(f"**{brand}:** feed unavailable ({type(error).__name__}: {error})\n")
            continue
        found = candidates(cat, brand, products)
        if not found:
            print(f"**{brand}:** no unclaimed products.\n")
            continue
        print(f"**{brand}:**")
        for title, handle in found:
            print(f"- [{title}]({base}{handle})")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
