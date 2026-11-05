"""Sweep every external citation on the generated category pages.

Usage: python build/links.py

A 404 or 410 is dead. A 401, 403, 407 or 429 is treated as bot blocking,
because the page may still open in a browser. A 2xx page whose title says
something went wrong or page not found is dead too. Unreachable requests are
kept separate from both. The exit status is 1 for a dead page or a server
error, so a scheduled run fails on a missing citation without failing on a bot
wall.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from pathlib import Path
import re
import urllib.error
import urllib.request

from catalog import CATEGORIES

ROOT = Path(__file__).resolve().parent.parent
PAGES = [cat["page"] for cat in CATEGORIES] + [
    cat["alias"] for cat in CATEGORIES if cat.get("alias")
]
OWN = (
    "lydenyardley.github.io",
    "subfreeuk.goatcounter.com",
    "gc.zgo.at",
    "github.com/lydenyardley/subfree-uk",
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; subfree-uk-link-check/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}
SOFT_ERROR = re.compile(
    r"<title[^>]*>[^<]*(?:something went wrong|page not found)[^<]*</title>",
    re.IGNORECASE,
)


def citations():
    links = set()
    for page in PAGES:
        text = (ROOT / page).read_text(encoding="utf-8")
        for raw in re.findall(r'href="([^"]+)"', text):
            url = unescape(raw)
            if not url.startswith(("http://", "https://")):
                continue
            if any(host in url for host in OWN):
                continue
            links.add(url)
    return sorted(links)


def fetch(url):
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            body = response.read(16384).decode("utf-8", "replace")
            return url, response.status, body
    except urllib.error.HTTPError as error:
        return url, error.code, ""
    except Exception as error:
        return url, None, f"{type(error).__name__}: {error}"


def main():
    links = citations()
    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch, url) for url in links]
        for future in as_completed(futures):
            results.append(future.result())

    groups = {
        "dead": [], "blocked": [], "server": [],
        "unreachable": [], "other": [], "ok": [],
    }
    for url, status, detail in results:
        if status is None:
            groups["unreachable"].append((url, detail))
        elif 200 <= status < 300 and SOFT_ERROR.search(detail):
            groups["dead"].append((url, f"{status} soft 404"))
        elif 200 <= status < 300:
            groups["ok"].append((url, status))
        elif status in (404, 410):
            groups["dead"].append((url, status))
        elif status in (401, 403, 407, 429):
            groups["blocked"].append((url, status))
        elif 500 <= status < 600:
            groups["server"].append((url, status))
        else:
            groups["other"].append((url, status))

    print(f"External citations: {len(links)}")
    for name in ("dead", "blocked", "server", "unreachable", "other"):
        print(f"{name.upper()} {len(groups[name])}")
        for url, value in sorted(groups[name]):
            print(f"  {value} {url}")
    print(f"OK {len(groups['ok'])}")
    return 1 if groups["dead"] or groups["server"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
