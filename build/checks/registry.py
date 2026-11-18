"""Every check the audit runs, gathered from the family modules in this package.

A family module exposes `CHECKS`, a list of `Check`. A check names itself, the
page state it needs (its phase), where it runs inside that phase (its order) and
what it proves. `registry()` returns them all in run order and refuses a
duplicate name, a duplicate order or an unknown phase, so a new check cannot
quietly take the place of an old one.

Phases, in the order the runner prepares them:

- `static`  files only, before the page is served.
- `phone`   a fresh 390px page, before any row or the comparison is opened.
- `desktop` a fresh 1280px page.
- `compare` the 1280px page with every row open and three models selected.
- `post`    the page is gone, and the browser is still open for its own passes.
- `report`  nothing is running; results already collected are reported.

A report-phase check cannot read the page, and `registry()` refuses one that
tries: naming `snapshot` or `page` there reads a closed browser, which only
looks harmless when a cache an earlier phase filled stands in for it.
"""
from dataclasses import dataclass
from types import CodeType

PHASES = ("static", "phone", "desktop", "compare", "post", "report")

# What only a live page can answer.
PAGE_BACKED = frozenset(
    {"page", "snapshot", "phone", "lightbox", "browser", "playwright", "ensure_compare"}
)


@dataclass(frozen=True)
class Check:
    """One named, timed result. `proves` is a sentence, or a call built from the run."""

    name: str
    phase: str
    order: int
    proves: object
    run: object

    def describe(self, ctx):
        return self.proves(ctx) if callable(self.proves) else self.proves


class Skip(Exception):
    """A check that cannot run here. The reason takes its place in the report."""


def page_reads(target, seen=None):
    """The page-backed names a callable reaches, through the helpers it calls.

    `co_names` holds the attributes and globals a body mentions, so a local
    variable is not mistaken for the context's `page`. Lambdas and
    comprehensions inside the body are code constants, and a helper it names is
    walked the same way, so a check cannot hide a page read one call away.
    """
    code = target if isinstance(target, CodeType) else getattr(target, "__code__", None)
    seen = set() if seen is None else seen
    if code is None or code in seen:
        return set()
    seen.add(code)
    names = set(code.co_names)
    if not isinstance(target, CodeType):
        globals_ = getattr(target, "__globals__", {})
        for name in names & globals_.keys():
            names |= page_reads(globals_[name], seen)
    for const in code.co_consts:
        if isinstance(const, CodeType):
            names |= page_reads(const, seen)
    return names


def registry():
    """Every check, in the order it runs."""
    from . import (
        accessibility, behaviour, browsers, category, compare, data, performance, structure,
    )

    modules = (
        data, category, structure, behaviour, compare, accessibility, performance, browsers,
    )
    checks = [check for module in modules for check in module.CHECKS]
    checks.sort(key=lambda check: check.order)

    names = [check.name for check in checks]
    repeated = sorted({name for name in names if names.count(name) > 1})
    if repeated:
        raise ValueError("two checks share a name: " + ", ".join(repeated))
    orders = [check.order for check in checks]
    repeated = sorted({order for order in orders if orders.count(order) > 1})
    if repeated:
        raise ValueError("two checks share an order: " + ", ".join(map(str, repeated)))
    unknown = sorted({check.phase for check in checks} - set(PHASES))
    if unknown:
        raise ValueError("unknown phase: " + ", ".join(unknown))
    for check in checks:
        if check.phase != "report":
            continue
        names = page_reads(check.run)
        if callable(check.proves):
            names |= page_reads(check.proves)
        read = sorted(names & PAGE_BACKED)
        if read:
            raise ValueError(
                f"{check.name!r} runs in the report phase, after the browser has "
                f"closed, so it cannot read {', '.join(read)}; move it to the "
                "phase that owns the page"
            )
    return checks
