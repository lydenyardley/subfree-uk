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
"""
from dataclasses import dataclass

PHASES = ("static", "phone", "desktop", "compare", "post", "report")


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


def registry():
    """Every check, in the order it runs."""
    from . import accessibility, behaviour, browsers, compare, data, performance, structure

    modules = (data, structure, behaviour, compare, accessibility, performance, browsers)
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
    return checks
