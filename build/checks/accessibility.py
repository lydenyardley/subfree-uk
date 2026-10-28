"""Names, contrast, targets, the document outline and axe-core."""
from .context import AXE_WIDTHS, BEST_PRACTICE_TAG, WCAG_TAGS
from .js import INK_JS
from .registry import Check
from .structure import tiny


def axe_violations(axe, page):
    """Every axe rule, on every card laid out.

    A phone card below the fold is contained and not painted, so a control in
    one overflows a box that is only the 330px estimate. No reader can see
    that, but axe reads the box and calls the control partially obscured. The
    style tag lays every card out for the measurement, which is the page a
    reader gets, and no rule is switched off to get there.
    """
    style = page.add_style_tag(
        content=".main-t tbody.item{content-visibility:visible!important}"
    )
    try:
        results = axe.run(
            page,
            options={
                "resultTypes": ["violations"],
                "runOnly": {"type": "tag", "values": WCAG_TAGS + [BEST_PRACTICE_TAG]},
            },
        )
    finally:
        style.evaluate("el => el.remove()")
    return results.response["violations"]

def ink_check(page):
    """Muted text clears 4.5:1 on the page and on a tinted row, in both themes.

    The cards tint their row on hover, so a note has to pass on the tint, not
    only on paper.
    """
    problems = []
    start = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
    for want in ("light", "dark"):
        page.evaluate("(t) => document.documentElement.setAttribute('data-theme', t)", want)
        page.wait_for_timeout(60)
        got = page.evaluate(INK_JS)
        if got.get("theme") == "unparsed":
            problems.append(f"{want}: --ink3/--paper/--tint are not hex: {got['raw']!r}")
            continue
        for surface in ("paper", "tint"):
            if got[surface] < 4.5:
                problems.append(
                    f"{want}: --ink3 {got['raw']} on --{surface} is {got[surface]}:1, needs 4.5"
                )
    page.evaluate(
        """(t) => {
            if (t) document.documentElement.setAttribute('data-theme', t);
            else document.documentElement.removeAttribute('data-theme');
        }""",
        start,
    )
    return problems

def link_names(data):
    return (
        ["links without an accessible name: " + ", ".join(data["emptyLinks"][:5])]
        if data["emptyLinks"]
        else []
    )

def alt_text(data):
    missing = [img["src"] for img in data["images"] if img["alt"] is None]
    repeated = [img["src"] for img in data["images"] if img["inRowHeader"] and img["alt"]]
    if missing:
        return ["images without an alt attribute: " + ", ".join(missing[:5])]
    if repeated:
        return ["thumbnails repeat the row heading in alt text: " + ", ".join(repeated[:5])]
    return []

def control_labels(data):
    unnamed = [
        f"{control['tag']}[{control['type']}]"
        for control in data["controls"]
        if control["visible"] and not control["name"]
    ]
    return ["form controls without a label: " + ", ".join(unnamed)] if unnamed else []

def button_names(data):
    unnamed = [button["name"] or "(empty)" for button in data["buttons"] if button["visible"] and not button["name"]]
    return [f"buttons without a name: {len(unnamed)}"] if unnamed else []

def target_sizes(data):
    small_buttons = [
        f"{button['name']} ({button['width']}x{button['height']})"
        for button in data["buttons"]
        if button["visible"] and (button["width"] < 24 or button["height"] < 24)
    ]
    small_controls = [
        f"{control['tag']}[{control['type']}] ({control['width']}x{control['height']})"
        for control in data["controls"]
        if control["visible"] and control["type"] != "checkbox"
        and (control["width"] < 24 or control["height"] < 24)
    ]
    return ["targets under 24px: " + ", ".join(small_buttons + small_controls)] if (
        small_buttons or small_controls
    ) else []

def header_scope(data):
    return [f"{data['thNoScope']} table headers missing scope"] if data["thNoScope"] else []

def heading_outline(data):
    problems = []
    if data["headings"].count(1) != 1:
        problems.append(f"{data['headings'].count(1)} h1 elements")
    for previous, current in zip(data["headings"], data["headings"][1:]):
        if current > previous + 1:
            problems.append(f"h{previous} jumps to h{current}")
    return problems

def footnote_set(data):
    if set(data["footRefs"]) == set(data["footTargets"]):
        return []
    orphaned = sorted(set(data["footTargets"]) - set(data["footRefs"]))
    broken = sorted(set(data["footRefs"]) - set(data["footTargets"]))
    return [f"footnote mismatch, unreferenced: {orphaned}, missing: {broken}"]

def axe_where(key):
    """The name of one pass: a theme at a width, or a named page state."""
    theme, where = key
    return f"{theme} at {where}px" if isinstance(where, int) else f"{theme} {where}"


def axe_problems(axe_results):
    problems = []
    best_practice = {}
    for key, violations in axe_results.items():
        where = axe_where(key)
        wcag = [v for v in violations if set(v["tags"]) & set(WCAG_TAGS)]
        wcag_ids = {v["id"] for v in wcag}
        for violation in violations:
            if violation["id"] in wcag_ids:
                continue
            entry = best_practice.setdefault(
                violation["id"],
                {"impact": violation["impact"], "help": violation["help"],
                 "targets": set(), "where": set()},
            )
            entry["targets"].update(node["target"][0] for node in violation["nodes"])
            entry["where"].add(where)
        if not wcag:
            continue
        for violation in wcag:
            nodes = violation["nodes"]
            problems.append(
                f"axe {where}: {violation['id']} ({violation['impact']}), "
                f"{len(nodes)} node(s). {violation['help']}"
            )
            for node in nodes[:4]:
                summary = node.get("failureSummary", "").replace("\n", " ").strip()
                print(f"        {', '.join(node['target'])}  {summary[:150]}")
    # The masthead sat outside every landmark, so the one finding axe called a
    # best practice was the only content a landmark user could not jump to.
    # It fails now rather than only printing, which is what the audit's R15
    # asks for: the region rule reports zero nodes.
    if "region" in best_practice:
        entry = best_practice["region"]
        problems.append(
            f"axe region: {len(entry['targets'])} element(s) outside every landmark: "
            + ", ".join(sorted(entry["targets"])[:4])
        )
    for rule, entry in sorted(best_practice.items()):
        if rule == "region":
            continue
        print(
            f"  note  axe best-practice {rule} ({entry['impact']}): {entry['help']} On "
            f"{', '.join(sorted(entry['targets'])[:3])}, in {len(entry['where'])} of "
            f"{len(axe_results)} theme, width and state passes"
        )
    return problems

def axe_audit(page):
    from axe_playwright_python.sync_playwright import Axe

    axe = Axe()
    results = {}
    for mode in ("dark", "light"):
        for width in AXE_WIDTHS:
            page.set_viewport_size({"width": width, "height": 900})
            page.wait_for_timeout(120)
            results[(mode, width)] = axe_violations(axe, page)
        page.click("#theme")
        page.wait_for_timeout(120)
    # The tray and the back-to-top button are only on screen once the reader has
    # ticked a model and scrolled, so a pass at the top of the page never sees
    # them. This one does: one model ticked, the page scrolled past its
    # sentinel, at the width where the tray is the only Compare affordance.
    page.set_viewport_size({"width": 390, "height": 844})
    page.evaluate(
        """() => {
            const box = document.querySelector('input.cmp');
            box.checked = true;
            box.dispatchEvent(new Event('change', { bubbles: true }));
            const s = document.getElementById('totop-s');
            window.scrollTo(0, s.getBoundingClientRect().top + window.scrollY + 600);
        }"""
    )
    page.wait_for_timeout(250)
    theme = page.evaluate(
        "() => document.documentElement.getAttribute('data-theme')"
        " || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')"
    )
    results[(theme, "with the tray and back-to-top on screen")] = axe_violations(axe, page)
    # Put the page back the way the checks after this one expect it: one row
    # unticked through its own change event, so the tray closes with it.
    page.evaluate(
        """() => {
            window.scrollTo(0, 0);
            const box = document.querySelector('input.cmp');
            box.checked = false;
            box.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(120)
    return results

COLUMN_KEYS_JS = """() => ({
    order: Array.from(document.querySelectorAll('#cmp-table thead th[data-id]')).map((th) => th.dataset.id),
    labels: Array.from(document.querySelectorAll('#cmp-table thead th[data-id]')).map((th) => {
        const move = th.querySelector('.cmp-move');
        return move ? move.getAttribute('aria-label') : null;
    }),
    target: (() => {
        const move = document.querySelector('#cmp-table .cmp-move');
        if (!move) return [0, 0];
        const box = move.getBoundingClientRect();
        return [Math.round(box.width), Math.round(box.height)];
    })(),
    focus: document.activeElement && document.activeElement.dataset
        ? document.activeElement.dataset.move : null,
    live: document.getElementById('live').textContent
})"""

def column_keys_check(page):
    """The column handle is a button, and the arrow keys arrange the columns.

    A drag is not the only way to move a column: each handle is a tab stop that
    moves its column one place with the arrow keys and to either end with Home
    and End. The name says where the column is, and the move is announced, so a
    reader who cannot see the slide still knows where the column landed.
    """
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(120)
    page.locator("#cmp-table").scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    before = page.evaluate(COLUMN_KEYS_JS)
    if len(before["order"]) != 3:
        return [f"expected three columns to arrange, found {len(before['order'])}"]
    missing = [before["order"][i] for i, label in enumerate(before["labels"]) if label is None]
    if missing:
        return [f"no column handle on {', '.join(missing)}"]
    problems = []
    if before["target"] != [44, 44]:
        problems.append(f"the handle's target is {before['target']}, not 44x44")

    first = before["order"][0]
    name = before["labels"][0].split(" left or right")[0].removeprefix("Move ")
    page.locator(f'.cmp-move[data-move="{first}"]').focus()
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(500)
    moved = page.evaluate(COLUMN_KEYS_JS)
    expect = [before["order"][1], first, before["order"][2]]
    if moved["order"] != expect:
        problems.append(
            f"ArrowRight on {first} gave {moved['order']}, expected {expect}"
        )
    if moved["focus"] != first:
        problems.append(f"focus went to {moved['focus']!r} after the key, not {first!r}")
    if moved["labels"][1] != f"Move {name} left or right. Column 2 of 3.":
        problems.append(f"the moved handle is named {moved['labels'][1]!r} at column 2")
    if moved["live"] != f"{name} moved to column 2 of 3":
        problems.append(f"the key move was announced as {moved['live']!r}")

    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(300)
    if page.evaluate(COLUMN_KEYS_JS)["order"] != before["order"]:
        problems.append(
            f"ArrowLeft did not put the columns back: {page.evaluate(COLUMN_KEYS_JS)['order']}"
        )

    page.keyboard.press("End")
    page.wait_for_timeout(300)
    end = page.evaluate(COLUMN_KEYS_JS)
    if end["order"][-1] != first:
        problems.append(f"End put {first} at {end['order']}, not the last column")
    page.keyboard.press("Home")
    page.wait_for_timeout(300)
    home = page.evaluate(COLUMN_KEYS_JS)
    if home["order"] != before["order"]:
        problems.append(f"Home left the columns as {home['order']}, not {before['order']}")

    # The name counts the columns the reader has. Two models used to be named
    # "of 3", because the count was written into the name instead of read from
    # the table.
    page.evaluate(
        """(ids) => document.querySelectorAll('input.cmp').forEach((c) => {
            c.checked = ids.indexOf(c.value) > -1;
            c.dispatchEvent(new Event('change', { bubbles: true }));
        })""",
        before["order"][:2],
    )
    page.wait_for_timeout(250)
    two = page.evaluate(COLUMN_KEYS_JS)
    if len(two["labels"]) != 2 or any(not (label or "").endswith(" of 2.") for label in two["labels"]):
        problems.append(f"a two-model comparison names its handles {two['labels']}")
    page.evaluate(
        """(ids) => document.querySelectorAll('input.cmp').forEach((c) => {
            c.checked = ids.indexOf(c.value) > -1;
            c.dispatchEvent(new Event('change', { bubbles: true }));
        })""",
        before["order"],
    )
    page.wait_for_timeout(250)
    back = page.evaluate(COLUMN_KEYS_JS)
    if back["order"] != before["order"]:
        problems.append(f"the third model came back at {back['order']}, not {before['order']}")
    return problems

CHECKS = [
    Check(
        "muted contrast", "desktop", 33,
        "muted text clears 4.5:1 on paper and on a tinted row, in both themes",
        lambda ctx: ink_check(ctx.page),
    ),
    Check(
        "link names", "compare", 63, "every link has an accessible name",
        lambda ctx: link_names(ctx.snapshot),
    ),
    Check(
        "alt text", "compare", 64, "images carry usable alt text",
        lambda ctx: alt_text(ctx.snapshot),
    ),
    Check(
        "form labels", "compare", 65, "every form control is labelled",
        lambda ctx: control_labels(ctx.snapshot),
    ),
    Check(
        "button names", "compare", 66, "every button has a name",
        lambda ctx: button_names(ctx.snapshot),
    ),
    Check(
        "target sizes", "compare", 67, "buttons and inputs meet 24px targets",
        lambda ctx: target_sizes(ctx.snapshot),
    ),
    Check(
        "table header scope", "compare", 68, "every table header declares scope",
        lambda ctx: header_scope(ctx.snapshot),
    ),
    Check(
        "heading outline", "compare", 69, "the heading outline is intact",
        lambda ctx: heading_outline(ctx.snapshot),
    ),
    Check(
        "footnote set", "compare", 70, "footnotes are referenced and present",
        lambda ctx: footnote_set(ctx.snapshot),
    ),
    Check(
        "type floor at 1280", "compare", 73, "no rendered text is below 11px at 1280",
        lambda ctx: tiny(ctx.snapshot, 1280),
    ),
    Check(
        "compare column keys", "compare", 29,
        "each column handle is a 44px button that moves its column with the arrow keys and Home/End, keeps focus, and announces where it landed",
        lambda ctx: column_keys_check(ctx.page),
    ),
    Check(
        "axe WCAG", "compare", 77,
        "axe-core finds no WCAG 2.2 A/AA violation in either theme at 390, 820 and 1280, or with the tray and back-to-top on screen, and every element sits inside a landmark",
        lambda ctx: axe_problems(axe_audit(ctx.page)),
    ),
]

