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

def axe_problems(axe_results):
    problems = []
    best_practice = {}
    for theme in ("dark", "light"):
        for width in AXE_WIDTHS:
            violations = axe_results[(theme, width)]
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
                entry["where"].add(f"{theme} {width}px")
            if not wcag:
                continue
            for violation in wcag:
                nodes = violation["nodes"]
                problems.append(
                    f"axe {theme} at {width}px: {violation['id']} ({violation['impact']}), "
                    f"{len(nodes)} node(s). {violation['help']}"
                )
                for node in nodes[:4]:
                    summary = node.get("failureSummary", "").replace("\n", " ").strip()
                    print(f"        {', '.join(node['target'])}  {summary[:150]}")
    for rule, entry in sorted(best_practice.items()):
        print(
            f"  note  axe best-practice {rule} ({entry['impact']}): {entry['help']} On "
            f"{', '.join(sorted(entry['targets'])[:3])}, in {len(entry['where'])} of "
            f"{len(AXE_WIDTHS) * 2} theme and width passes"
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
    return results

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
        "axe WCAG", "compare", 77,
        "axe-core finds no WCAG 2.2 A/AA violation in either theme at 390, 820 and 1280",
        lambda ctx: axe_problems(axe_audit(ctx.page)),
    ),
]

