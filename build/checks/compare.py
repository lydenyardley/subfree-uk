"""The comparison view, from the tray it grows out of to the table it becomes."""
from .context import SHORTLIST_IDS, open_compare
from .registry import Check


def costrow_check(page, row_count, cells):
    """The compare table opens with a row that does the 3-year subtraction."""
    problems = []
    state = page.evaluate(
        """() => {
            const row = document.querySelector('#cmp-table tr.cmp-cost');
            return {
                label: row ? row.querySelector('th').textContent : '',
                cells: row ? Array.from(row.querySelectorAll('td')).map((td) => td.textContent) : [],
                rows: document.querySelectorAll('#cmp-table tbody tr').length
            };
        }"""
    )
    if state["label"] != "Cheapest way to record for 3 years":
        problems.append(f"the compare cost row is labelled {state['label']!r}")
    if state["cells"] != cells:
        problems.append(f"compare cost row reads {state['cells']}, expected {cells}")
    if state["rows"] != row_count:
        problems.append(
            f"the compare table has {state['rows']} body rows, expected {row_count}"
        )
    return problems

def marks_check(page):
    """The comparison marks what is missing, and leaves good news unmarked.

    A missing feature is worth a reader's attention, so it is coloured. The
    two rows where "None" is good news, the plan row and the paywall row, are
    left alone: a doorbell with no plan and nothing held back is the cheapest
    option on the page, and painting it red would warn the reader off it.
    The verdict a row carries comes with it, as a rule down its column and the
    verdict in the column's header.
    """
    problems = []
    page.evaluate(
        """() => {
            const ids = ['ring', 'reo-poe', 'aqara-g4'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(250)
    if page.evaluate("() => document.getElementById('compare').hidden"):
        page.click("#cmp-inline")
        page.wait_for_timeout(300)
    state = page.evaluate(
        """() => {
            const rows = Array.from(document.querySelectorAll('#cmp-table tbody tr'));
            const row = (label) => rows.find(
                (tr) => { const th = tr.querySelector('th'); return th && th.textContent === label; }
            );
            const cells = (label) => {
                const tr = row(label);
                if (!tr) return null;
                return Array.from(tr.querySelectorAll('td')).map((td) => {
                    const rec = td.querySelector('.rec');
                    return {
                        text: td.textContent.trim().slice(0, 30),
                        marked: !!td.querySelector('.cmp-no'),
                        rec: rec ? rec.className : ''
                    };
                });
            };
            return {
                rec: cells('Records free?'),
                storage: cells('Storage'),
                history: cells('History, no plan'),
                plan: cells('Plans'),
                paywall: cells('Behind the paywall')
            };
        }"""
    )
    for label in ("rec", "storage", "history", "plan", "paywall"):
        if state[label] is None:
            problems.append(f"the comparison has no {label} row to read")
    if problems:
        return problems
    # The columns are in the table's order, not the order they were ticked,
    # so the assertions read the cells rather than count them.
    # The record marker is the list's own, so a "No" reads the same in both
    # places and colour is not the only signal.
    no = [cell for cell in state["rec"] if cell["rec"] == "rec rec-no"]
    yes = [cell for cell in state["rec"] if cell["rec"] == "rec rec-yes"]
    if len(no) != 1 or len(yes) != 2:
        problems.append(f"the record markers are wrong: {state['rec']}")
    # One of the three has no storage and no free history, and both are
    # marked. The other two have both, and neither is marked.
    for label in ("storage", "history"):
        marked = [cell for cell in state[label] if cell["marked"]]
        if len(marked) != 1 or not marked[0]["text"].startswith("None"):
            problems.append(
                f"the {label} row does not mark the one that is missing: {state[label]}"
            )
    # "None" in the plan row and the paywall row is good news, and is not
    # marked. Reolink PoE and Aqara are both in this trio.
    if any(cell["marked"] for cell in state["plan"]):
        problems.append(f"a plan cell is marked: {state['plan']}")
    if any(cell["marked"] for cell in state["paywall"]):
        problems.append(f"a paywall cell is marked: {state['paywall']}")
    if not any(cell["text"].startswith("None") for cell in state["plan"]):
        problems.append(f"the plan row has no 'None' in it to read: {state['plan']}")
    # The verdict a row carries travels into the comparison as the badge under
    # its column's header and the rule under that header, both in the verdict's
    # colour at the 3px of every other verdict line on the page. The spec column
    # holds no model and keeps the page's ink. A rule down the side of every cell
    # read as the previous column's edge, so no cell carries one.
    tone = page.evaluate(
        """() => {
            const ids = Array.from(document.querySelectorAll('input.cmp:checked')).map((c) => c.value);
            const body = Array.from(document.querySelectorAll('#cmp-table tbody tr'));
            const heads = Array.from(document.querySelectorAll('#cmp-table thead th')).slice(1);
            const sides = (tr) => Array.from(tr.children).slice(1).map((c) => getComputedStyle(c).borderLeftWidth);
            const spec = getComputedStyle(document.querySelector('#cmp-table thead th'));
            return {
                columns: heads.map((th, i) => {
                    const id = ids[i];
                    const main = document.getElementById('m-' + id);
                    const rowTag = main ? main.querySelector('.vtag') : null;
                    const headTag = th.querySelector('.vtag');
                    const rule = getComputedStyle(th);
                    return {
                        id,
                        rowTone: main ? main.getAttribute('data-v') : null,
                        tone: th.getAttribute('data-v'),
                        tag: headTag ? headTag.textContent.trim() : '',
                        rowTag: rowTag ? rowTag.textContent.trim() : '',
                        ruleWidth: rule.borderBottomWidth,
                        rule: rule.borderBottomColor,
                        toneColor: headTag ? getComputedStyle(headTag).color : ''
                    };
                }),
                ink: getComputedStyle(document.body).color,
                specWidth: spec.borderBottomWidth,
                specRule: spec.borderBottomColor,
                cellBorders: Array.from(new Set(body.flatMap(sides)))
            };
        }"""
    )
    for column in tone["columns"]:
        if (column["rowTone"] or "") != (column["tone"] or ""):
            problems.append(
                f"{column['id']}'s column carries {column['tone']!r}, its row {column['rowTone']!r}"
            )
        if column["tone"] and column["tag"] != column["rowTag"]:
            problems.append(
                f"{column['id']}'s column badge reads {column['tag']!r}, its row {column['rowTag']!r}"
            )
        want = column["toneColor"] or tone["ink"]
        if column["ruleWidth"] != "3px" or column["rule"] != want:
            problems.append(
                f"{column['id']}'s header rule is {column['ruleWidth']} "
                f"{column['rule']}, expected a 3px {want} for its {column['tone'] or 'no'} verdict"
            )
    if tone["specWidth"] != "3px" or tone["specRule"] != tone["ink"]:
        problems.append(
            f"the spec column's header rule is {tone['specWidth']} {tone['specRule']}, "
            f"expected a 3px rule in the page's ink {tone['ink']}"
        )
    if tone["cellBorders"] != ["0px"]:
        problems.append(
            f"cells in the comparison carry a side rule: {tone['cellBorders']}"
        )

    # Put the shortlist back for the checks that follow.
    page.evaluate(
        """() => {
            const ids = ['tapo-td21', 'reo-poe', 'ezviz-ep3x'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(250)
    return problems

def chrome_check(page):
    """The sort control and compare table keep their declared metrics."""
    problems = []
    m = page.evaluate(
        """() => {
            const cs = (el) => el ? getComputedStyle(el) : null;
            const sel = cs(document.getElementById('sort'));
            const cell = cs(document.querySelector('#cmp-table tbody td'));
            const head = cs(document.querySelector('#cmp-table thead th'));
            const th = cs(document.querySelector('#cmp-table tbody th'));
            return {
                select: sel ? sel.minHeight : '',
                cellPad: cell ? cell.paddingTop + ' ' + cell.paddingRight : '',
                headPad: head ? head.paddingTop + ' ' + head.paddingRight : '',
                thLine: th ? th.lineHeight : '',
                thSize: th ? th.fontSize : ''
            };
        }"""
    )
    if m["select"] != "44px":
        problems.append(f"the sort select is {m['select']!r} tall, expected 44px")
    for name in ("cellPad", "headPad"):
        if m[name] != "8px 16px":
            problems.append(f"compare table {name} is {m[name]!r}, expected 8px 16px")
    if m["thSize"] != "11px" or m["thLine"] != "19.2px":
        problems.append(
            f"compare row labels are {m['thSize']}/{m['thLine']}, expected 11px/19.2px"
        )
    return problems

def shortlist_check(page, checked=None):
    """Copy shortlist puts the selected models and the URL on the clipboard."""
    problems = []
    before = page.inner_text("#cmp-copy")
    page.click("#cmp-copy")
    page.wait_for_timeout(350)
    after = page.evaluate(
        """() => {
            const n = document.getElementById('cmp-note');
            return { text: n.textContent.trim(), hidden: n.hidden, role: n.getAttribute('role') };
        }"""
    )
    try:
        text = page.evaluate("() => navigator.clipboard.readText()")
    except Exception as error:
        text = ""
        problems.append(f"could not read the clipboard: {error}")
    if before != "Copy shortlist":
        problems.append(f"the copy action reads {before!r}")
    confirm = (
        "Copied 3 models as Markdown, with prices and the date checked. "
        "Paste it into a message or a note."
    )
    if after["text"] != confirm or after["hidden"]:
        problems.append(f"the copy confirmation reads {after['text']!r}")
    if after["role"] != "status":
        problems.append(f"the copy confirmation has role {after['role']!r}")
    required = [
        f"SubFree UK shortlist, checked {checked}" if checked else "SubFree UK shortlist, checked",
        "TP-Link Tapo TD21",
        "Reolink Video Doorbell PoE",
        "EZVIZ EP3x Pro",
        "£44.99",
        "£54.99",
        "£69.99",
        "£79.99",
    ]
    missing = [part for part in required if part not in text]
    if missing:
        problems.append(f"the shortlist is missing {missing}")
    lines = text.split("\n")
    if "\\n" in text:
        problems.append("the shortlist contains literal backslash-n text instead of line breaks")
    if len(lines) < 10 or not lines[1].startswith("http"):
        problems.append(f"the shortlist is not laid out as lines: {lines[:3]}")
    links = [line for line in lines if "?cmp=" in line]
    if len(links) != 1 or not all(
        model in links[0] for model in ("tapo-td21", "reo-poe", "ezviz-ep3x")
    ):
        problems.append(f"the shortlist link reads {links}")
    if text.count("Best for:") != 3 or text.count("Main catch:") != 3:
        problems.append("the shortlist does not give Best for and Main catch for all 3 models")
    page.wait_for_timeout(6800)
    if not page.evaluate("() => document.getElementById('cmp-note').hidden"):
        problems.append("the copy confirmation does not fade after six seconds")
    if page.inner_text("#cmp-copy") != "Copy shortlist":
        problems.append("the copy button label changed")
    return problems

def diff_check(page, compare_rows):
    """A differences-only view hides identical spec rows but keeps the decisions."""
    problems = []
    page.evaluate(
        """() => {
            const ids = ['reo-poe', 'reo-wifi', 'reo-batt'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(250)
    # The count line is the open affordance that survives while the tray is
    # away, so the check does not depend on the panel being closed first.
    page.click("#cmp-inline")
    page.wait_for_timeout(150)
    off = page.evaluate(
        """() => {
            const box = document.getElementById('cmp-diff-w');
            const rows = Array.from(document.querySelectorAll('#cmp-table tbody tr'));
            return {
                hidden: box.hidden,
                label: box.textContent.replace(/\\s+/g, ' ').trim(),
                checked: document.getElementById('cmp-diff').checked,
                live: document.getElementById('compare').getAttribute('aria-live'),
                rows: rows.length,
                shown: rows.filter((tr) => !tr.hidden).length,
                dupes: +((document.getElementById('cmp-dupes').textContent.match(/\\d+/) || [0])[0])
            };
        }"""
    )
    if off["hidden"]:
        problems.append("the differences-only control is hidden for a trio with identical rows")
    if off["checked"]:
        problems.append("the differences-only view is on before anyone asks for it")
    if off["dupes"] < 1:
        problems.append(f"the control counts {off['dupes']} identical rows for the Reolink trio")
    if f"({off['dupes']} identical)" not in off["label"]:
        problems.append(f"the control reads {off['label']!r}")
    if off["rows"] != compare_rows or off["shown"] != compare_rows:
        problems.append(f"the compare table starts at {off['shown']} of {off['rows']} rows")
    if off["live"]:
        problems.append(
            f"the compare panel is a live region ({off['live']}); rendering eighteen rows "
            "would read them all aloud"
        )

    page.check("#cmp-diff")
    page.wait_for_timeout(150)
    on = page.evaluate(
        """() => {
            const rows = Array.from(document.querySelectorAll('#cmp-table tbody tr'));
            const hidden = rows.filter((tr) => tr.hidden);
            const same = hidden.every((tr) => {
                const cells = Array.from(tr.querySelectorAll('td')).map((td) => td.textContent);
                return cells.length > 1 && cells.every((v) => v === cells[0]);
            });
            return {
                shown: rows.filter((tr) => !tr.hidden).length,
                hidden: hidden.length,
                allIdentical: same,
                pinnedHidden: rows.filter((tr) => tr.dataset.pin && tr.hidden)
                    .map((tr) => tr.querySelector('th').textContent),
                pinned: rows.filter((tr) => tr.dataset.pin).length
            };
        }"""
    )
    if on["hidden"] != off["dupes"]:
        problems.append(f"the toggle hides {on['hidden']} rows, not {off['dupes']}")
    if on["shown"] + on["hidden"] != compare_rows:
        problems.append(f"the table holds {on['shown'] + on['hidden']} rows after the toggle")
    if not on["allIdentical"]:
        problems.append("the toggle hides a row that is not identical")
    if on["pinnedHidden"]:
        problems.append(f"the toggle hides a decision row: {on['pinnedHidden']}")
    if on["pinned"] != 5:
        problems.append(f"{on['pinned']} rows are pinned, expected the cost row and four decisions")

    page.uncheck("#cmp-diff")
    page.wait_for_timeout(120)
    if page.evaluate("() => document.querySelectorAll('#cmp-table tbody tr:not([hidden])').length") != compare_rows:
        problems.append("unticking differences only does not restore the rows")

    page.evaluate(
        """() => {
            const ids = ['tapo-td21', 'reo-poe', 'ezviz-ep3x'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(200)
    page.click("#cmp-inline")
    page.wait_for_timeout(150)
    return problems

def morph_check(page):
    """The compare panel is the tray, moved: one named pair, 240ms, guarded.

    The three ticked rows' names and photos fly into their columns and back out
    again, so both frames are asserted: which half carries each name, and that
    the other half is out of the picture for the length of the movement.
    """
    problems = []
    page.emulate_media(reduced_motion="no-preference")
    page.evaluate(
        """() => {
            const ids = ['reo-poe', 'reo-wifi', 'reo-batt'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(200)

    names = page.evaluate(
        """() => ({
            tray: getComputedStyle(document.getElementById('tray')).viewTransitionName,
            head: getComputedStyle(document.querySelector('.cmp-head')).viewTransitionName,
            page: getComputedStyle(document.documentElement).viewTransitionName,
            named: Array.from(document.querySelectorAll('body *')).filter(
                (e) => getComputedStyle(e).viewTransitionName !== 'none'
            ).map((e) => e.id || e.className)
        })"""
    )
    if names["tray"] != "cmp-tray" or names["head"] != "cmp-tray":
        problems.append(f"the tray and the compare header do not share one name: {names}")
    if len(names["named"]) != 2:
        problems.append(f"{len(names['named'])} elements are named for the transition: {names['named']}")
    # The page behind the pair is not captured. The root snapshot is the whole
    # document rendered as a picture, and it is most of the cost of opening the
    # comparison; only the pair needs to be caught.
    if names["page"] != "none":
        problems.append(
            f"the whole page is captured for the transition, not just the pair: {names['page']!r}"
        )

    # Opening: one transition, 240ms, and the tray's box is now the panel's.
    page.evaluate(
        """() => {
            window.__vt = { calls: 0, last: null, log: [] };
            window.__vtReal = document.startViewTransition;
            const real = window.__vtReal.bind(document);
            // What the two frames say: which half of each pair carries the name,
            // and whether the table's copy is out of the picture in the second.
            const frame = () => ({
                // Only the parts in play: a row that was never ticked has no name
                // and stays on screen throughout, and saying so is not a finding.
                table: Array.from(document.querySelectorAll('#tbl .mname, #tbl .ph-sm'))
                    .map((e) => [getComputedStyle(e).viewTransitionName, getComputedStyle(e).visibility])
                    .filter((part) => part[0] !== 'none' || part[1] === 'hidden'),
                head: Array.from(document.querySelectorAll('#cmp-table thead .cmp-name, #cmp-table thead .cmp-photo img'))
                    .map((e) => [getComputedStyle(e).viewTransitionName, getComputedStyle(e).visibility])
                    .filter((part) => part[0] !== 'none')
            });
            document.startViewTransition = (cb) => {
                window.__vt.calls++;
                const before = frame();
                return real(() => {
                    cb();
                    window.__vt.last = { before, after: frame() };
                    window.__vt.log.push(window.__vt.last);
                });
            };
        }"""
    )
    page.evaluate("() => document.getElementById('tray-go').click()")
    page.wait_for_timeout(60)
    during = page.evaluate(
        """() => {
            const r = document.documentElement;
            const anims = document.getAnimations({ subtree: true });
            return {
                dur: getComputedStyle(r, '::view-transition-group(cmp-tray)').animationDuration,
                root: getComputedStyle(r, '::view-transition-old(root)').animationName,
                named: anims.filter((a) => (a.effect.pseudoElement || '').includes('cmp-tray')).length,
                rows: anims.filter((a) => /cmp-[np]-/.test(a.effect.pseudoElement || '')).length,
                rowDur: getComputedStyle(r, '::view-transition-group(cmp-n-reo-poe)').animationDuration,
                // Every other line here reads the name off the element, and a
                // name that never became a snapshot still reads back. The group
                // is the evidence that both halves were captured: no group, no
                // flight, however clean the computed name looks.
                groups: Array.from(new Set(anims
                    .map((a) => a.effect.pseudoElement || '')
                    .filter((p) => p.indexOf('::view-transition-group(cmp-n-') === 0
                        || p.indexOf('::view-transition-group(cmp-p-') === 0)
                    .map((p) => p.slice('::view-transition-group('.length, -1)))).sort(),
                ids: Array.from(document.querySelectorAll('input.cmp:checked')).map((c) => c.value),
                keyframes: anims
                    .filter((a) => a.effect.pseudoElement === '::view-transition-group(cmp-tray)')
                    .length
            };
        }"""
    )
    page.wait_for_timeout(320)
    opened = page.evaluate(
        """() => ({
            calls: window.__vt.calls,
            tray: document.getElementById('tray').hidden,
            panel: !document.getElementById('compare').hidden,
            focus: document.activeElement.id,
            top: Math.round(document.getElementById('compare').getBoundingClientRect().top)
        })"""
    )
    flown = page.evaluate("() => window.__vt.last")
    if not flown:
        problems.append("the open ran no transition to record")
    else:
        before, after = flown["before"], flown["after"]
        named_rows = before["table"]
        named_header = before["head"]
        if len(named_rows) != 6:
            problems.append(
                f"{len(named_rows)} row parts are named before the open, expected 6"
            )
        if named_header:
            problems.append(f"the header is already named before the open: {named_header}")
        if {part[0] for part in named_rows} != {part[0] for part in after["head"] if part[0] != "none"}:
            problems.append("the names on the rows and in the header do not pair up")
        if len([part for part in after["head"] if part[0] != "none"]) != 6:
            problems.append(
                f"{len([p for p in after['head'] if p[0] != 'none'])} header parts are named "
                "in the new frame, expected 6"
            )
        if [part for part in after["table"] if part[0] != "none"]:
            problems.append(f"the table is still named in the new frame: {after['table']}")
        painted = [part for part in after["table"] if part[1] != "hidden"]
        if painted:
            problems.append(
                f"{len(painted)} row parts are painted in place during the transition"
            )
        page.wait_for_timeout(500)
        settled = page.evaluate(
            """() => ({
                named: Array.from(document.querySelectorAll(
                    '#tbl .mname, #tbl .ph-sm, #cmp-table thead .cmp-name, #cmp-table thead .cmp-photo img'
                )).filter((e) => getComputedStyle(e).viewTransitionName !== 'none').length,
                hidden: Array.from(document.querySelectorAll('#tbl .mname, #tbl .ph-sm'))
                    .filter((e) => getComputedStyle(e).visibility === 'hidden').length
            })"""
        )
        if settled["named"] or settled["hidden"]:
            problems.append(f"the transition left names or hidden rows behind: {settled}")
    if opened["calls"] != 1:
        problems.append(f"opening ran {opened['calls']} view transitions, expected 1")
    if not opened["panel"] or not opened["tray"]:
        problems.append(f"opening did not hand the tray's place to the panel: {opened}")
    if during["dur"] != "0.24s" or not during["keyframes"]:
        problems.append(f"the named group does not run 240ms: {during}")
    if during["root"] not in ("none", ""):
        problems.append(f"the page cross-fades behind the pair: root old animation {during['root']}")
    if during["named"] < 3:
        problems.append(f"only {during['named']} animations of the named pair ran")
    if during["rows"] < 6:
        problems.append(
            f"only {during['rows']} animations of the rows' names and photos ran"
        )
    expected = sorted(
        [f"cmp-{half}-{id}" for id in during["ids"] for half in ("n", "p")]
    )
    if during["groups"] != expected:
        problems.append(
            f"the rows' names and photos were not captured: groups {during['groups']}, "
            f"expected {expected}"
        )
    if during["rowDur"] != "0.24s":
        problems.append(f"the rows travel on {during['rowDur']}, not the tray's 240ms")
    if abs(opened["top"]) > 2:
        problems.append(f"the panel opens {opened['top']}px from the top of the viewport")
    if opened["focus"] != "cmp-h":
        problems.append(
            f"opening put focus on {opened['focus'] or 'nothing'}, not the panel's heading"
        )

    page.evaluate("() => document.getElementById('cmp-close').click()")
    page.wait_for_timeout(60)
    leaving_anim = page.evaluate(
        """() => ({
            groups: Array.from(new Set(document.getAnimations({ subtree: true })
                .map((a) => a.effect.pseudoElement || '')
                .filter((p) => p.indexOf('::view-transition-group(cmp-n-') === 0
                    || p.indexOf('::view-transition-group(cmp-p-') === 0)
                .map((p) => p.slice('::view-transition-group('.length, -1)))).sort()
        })"""
    )
    page.wait_for_timeout(340)
    closed = page.evaluate(
        """() => ({
            vt: window.__vt.calls,
            tray: !document.getElementById('tray').hidden,
            panel: !document.getElementById('compare').hidden
        })"""
    )
    if closed["vt"] != 2:
        problems.append(f"closing ran {closed['vt']} transitions in total, expected 2")
    if not closed["tray"] or closed["panel"]:
        problems.append(f"closing did not give the tray back: {closed}")

    # Closing runs the same six pairs the other way: the header's copy carries
    # each name while the open frame is captured, the row's copy in the frame
    # after the panel goes. A one-way flight would leave the rows to fade in
    # under names that never left.
    reverse = page.evaluate("() => window.__vt.log[1]")
    if not reverse:
        problems.append("closing ran no transition to record")
    else:
        leaving, arriving = reverse["before"], reverse["after"]
        if len(leaving["head"]) != 6:
            problems.append(
                f"{len(leaving['head'])} header parts are named before the close, expected 6"
            )
        if [part for part in leaving["table"] if part[0] != "none"]:
            problems.append(f"the rows are still named before the close: {leaving['table']}")
        painted = [part for part in leaving["table"] if part[1] != "hidden"]
        if painted:
            problems.append(
                f"{len(painted)} row parts are painted in place while the panel closes"
            )
        if len([part for part in arriving["table"] if part[0] != "none"]) != 6:
            problems.append(
                f"{len([p for p in arriving['table'] if p[0] != 'none'])} row parts are "
                "named in the closing frame, expected 6"
            )
        if [part for part in arriving["head"] if part[0] != "none"]:
            problems.append(f"the header is still named after the close: {arriving['head']}")
        if not leaving["head"] or {part[0] for part in leaving["head"]} != {
            part[0] for part in arriving["table"] if part[0] != "none"
        }:
            problems.append("the names on the header and on the rows do not pair up on the way back")
        page.wait_for_timeout(400)
        back = page.evaluate(
            """() => ({
                named: Array.from(document.querySelectorAll(
                    '#tbl .mname, #tbl .ph-sm, #cmp-table thead .cmp-name, #cmp-table thead .cmp-photo img'
                )).filter((e) => getComputedStyle(e).viewTransitionName !== 'none').length,
                hidden: Array.from(document.querySelectorAll(
                    '#tbl .mname, #tbl .ph-sm, #cmp-table thead .cmp-name, #cmp-table thead .cmp-photo img'
                )).filter((e) => getComputedStyle(e).visibility === 'hidden').length
            })"""
        )
        if back["named"] or back["hidden"]:
            problems.append(f"closing left names or hidden parts behind: {back}")
    # A name on the right element and no captured group is a flight that never
    # happened, so the close is held to the same evidence as the open.
    if leaving_anim["groups"] != expected:
        problems.append(
            f"the rows' names and photos were not captured on the way back: "
            f"{leaving_anim['groups']}, expected {expected}"
        )

    # Clear lives in the panel because the tray is not on screen while it is open,
    # and the button that is about to vanish cannot keep focus.
    page.evaluate("() => document.getElementById('tray-go').click()")
    page.wait_for_timeout(350)
    page.focus("#cmp-clear")
    page.keyboard.press("Enter")
    page.wait_for_timeout(250)
    cleared = page.evaluate(
        """() => ({
            checked: document.querySelectorAll('input.cmp:checked').length,
            tray: !document.getElementById('tray').hidden,
            panel: !document.getElementById('compare').hidden,
            focus: document.activeElement.matches('input.cmp')
        })"""
    )
    if cleared["checked"] or cleared["panel"] or cleared["tray"]:
        problems.append(f"Clear in the panel did not empty the selection: {cleared}")
    if not cleared["focus"]:
        problems.append("clearing from the panel left focus on a hidden button")

    # Reduced motion: the swap still happens, but nothing animates.
    page.emulate_media(reduced_motion="reduce")
    page.evaluate(
        """() => {
            const ids = ['tapo-td21', 'reo-poe'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
            window.__vt.calls = 0;
        }"""
    )
    page.wait_for_timeout(150)
    page.evaluate("() => document.getElementById('tray-go').click()")
    page.wait_for_timeout(300)
    reduced = page.evaluate(
        """() => ({ calls: window.__vt.calls, panel: !document.getElementById('compare').hidden })"""
    )
    if reduced["calls"] != 0:
        problems.append("reduced motion still runs a view transition")
    if not reduced["panel"]:
        problems.append("reduced motion does not open the comparison")
    page.evaluate("() => document.getElementById('cmp-close').click()")
    page.wait_for_timeout(250)
    # The close under reduced motion is the instant swap the open was: no
    # transition, no row half left named or hidden, and the tray back in the
    # bar with focus on it. The tray and the header keep the one name they
    # share, which is a dormant style rule while no transition runs.
    reduced_close = page.evaluate(
        """() => ({
            calls: window.__vt.calls,
            tray: !document.getElementById('tray').hidden,
            panel: !document.getElementById('compare').hidden,
            focus: document.activeElement.id,
            named: Array.from(new Set(Array.from(document.querySelectorAll('body *'))
                .map((e) => getComputedStyle(e).viewTransitionName)
                .filter((name) => name !== 'none'))).sort(),
            hidden: Array.from(document.querySelectorAll(
                '#tbl .mname, #tbl .ph-sm, #cmp-table thead .cmp-name, #cmp-table thead .cmp-photo img'
            )).filter((e) => getComputedStyle(e).visibility === 'hidden').length
        })"""
    )
    if reduced_close["calls"]:
        problems.append("reduced motion runs a view transition on the way back")
    if reduced_close["panel"] or not reduced_close["tray"]:
        problems.append(f"reduced motion does not give the tray back: {reduced_close}")
    if reduced_close["named"] not in ([], ["cmp-tray"]):
        problems.append(
            f"reduced motion leaves row names behind on the close: {reduced_close['named']}"
        )
    if reduced_close["hidden"]:
        problems.append(
            f"reduced motion leaves {reduced_close['hidden']} row parts hidden after the close"
        )
    if reduced_close["focus"] != "tray-go":
        problems.append(
            f"the reduced-motion close puts focus on {reduced_close['focus'] or 'nothing'}, "
            "not the tray's Compare button"
        )

    # No API at all: the old instant swap, and the reader still gets the panel.
    page.emulate_media(reduced_motion="no-preference")
    page.evaluate("() => { document.startViewTransition = undefined }")
    page.evaluate("() => document.getElementById('tray-go').click()")
    page.wait_for_timeout(300)
    fallback = page.evaluate(
        """() => ({
            api: typeof document.startViewTransition,
            panel: !document.getElementById('compare').hidden,
            tray: !document.getElementById('tray').hidden
        })"""
    )
    if fallback["api"] != "undefined" or not fallback["panel"] or fallback["tray"]:
        problems.append(f"without the API the panel does not open or the tray stays: {fallback}")

    # Unticking below two closes the panel and leaves focus where the reader is.
    page.focus("input.cmp[value='tapo-td21']")
    page.evaluate(
        """() => {
            const c = document.querySelector("input.cmp[value='reo-poe']");
            c.checked = false;
            c.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(200)
    implicit = page.evaluate(
        """() => ({
            panel: !document.getElementById('compare').hidden,
            tray: !document.getElementById('tray').hidden,
            checked: document.querySelectorAll('input.cmp:checked').length,
            focus: document.activeElement.value
        })"""
    )
    if implicit["panel"] or not implicit["tray"] or implicit["checked"] != 1:
        problems.append(f"unticking below two did not close the panel: {implicit}")
    if implicit["focus"] != "tapo-td21":
        problems.append(f"unticking below two moved focus to {implicit['focus']}")

    page.evaluate(
        """() => {
            delete document.startViewTransition;
            document.getElementById('cmp-close').click();
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = false;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(250)
    return problems

def scroller_check(page):
    """The comparison's sideways scroll can be reached and moved by keyboard.

    At 390px the panel is 516px of table in 356px, so the third column is only
    readable by scrolling it. A named, focusable region gives a keyboard user
    the same scroll a mouse user gets for free.
    """
    problems = []
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(150)
    if page.evaluate("() => document.getElementById('compare').hidden"):
        open_compare(page)
        page.wait_for_timeout(250)
    state = page.evaluate(
        """() => {
            const s = document.querySelector('.cmp-scroll');
            const first = document.querySelector('#cmp-table thead th[data-id]');
            return {
                tab: s.tabIndex,
                role: s.getAttribute('role'),
                label: (s.getAttribute('aria-label') || '').trim(),
                over: s.scrollWidth - s.clientWidth,
                left: Math.round(s.scrollLeft),
                snap: getComputedStyle(s).scrollSnapType,
                align: first ? getComputedStyle(first).scrollSnapAlign : ''
            };
        }"""
    )
    if state["tab"] != 0:
        problems.append(f"the comparison scroller has tabIndex {state['tab']}")
    if state["role"] != "region" or not state["label"]:
        problems.append(f"the comparison scroller is unnamed: {state}")
    if state["over"] <= 0:
        problems.append("the comparison does not overflow at 390px, so it cannot be scrolled")
    # The cue tells the reader which model is next; the snap is what makes a
    # swipe land on a model rather than between two.
    if "mandatory" not in state["snap"] or state["align"] != "start":
        problems.append(
            f"the comparison does not snap one model at a time: "
            f"{state['snap']!r} / {state['align']!r}"
        )
    if state["over"] > 0:
        # The cue says the table scrolls, so it has to be where the reader looks:
        # above the table, not a screen and a half below the column it names.
        cue = page.evaluate(
            """() => {
                const cue = document.getElementById('cmp-cue');
                const s = document.querySelector('.cmp-scroll');
                const box = s.getBoundingClientRect();
                const cols = Array.from(
                    document.querySelectorAll('#cmp-table thead th')
                ).slice(1).map((th) => {
                    const r = th.getBoundingClientRect();
                    const name = th.querySelector('.cmp-name');
                    return {
                        name: (name || th).textContent.trim(),
                        left: Math.round(r.left),
                        right: Math.round(r.right)
                    };
                });
                return {
                    hidden: cue.hidden,
                    text: (cue.textContent || '').trim(),
                    top: Math.round(cue.getBoundingClientRect().top),
                    tableTop: Math.round(box.top),
                    start: Math.round(box.left),
                    edge: Math.round(box.right),
                    cols: cols
                };
            }"""
        )
        if cue["hidden"] or not cue["text"]:
            problems.append(f"the comparison does not say it scrolls: {cue['text']!r}")
        else:
            if cue["top"] > cue["tableTop"]:
                problems.append("the scroll cue is below the table it names")
            # It names the first column the reader cannot read: one cut off by
            # the edge with less than 60% of itself showing. Naming the first
            # column that merely starts past the edge named the third model
            # while the second was a 47px sliver.
            gone = [
                c["name"]
                for c in cue["cols"]
                if c["right"] > cue["edge"] + 1
                and (
                    min(c["right"], cue["edge"]) - max(c["left"], cue["start"])
                ) < (c["right"] - c["left"]) * 0.6
            ]
            if gone and cue["text"] != "Swipe to see " + gone[0]:
                problems.append(
                    f"the scroll cue names {cue['text']!r}, not the column the reader "
                    f"cannot read {gone[0]!r}"
                )
        page.focus(".cmp-scroll")
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(250)
        moved = page.evaluate(
            "() => Math.round(document.querySelector('.cmp-scroll').scrollLeft)"
        )
        if moved <= state["left"]:
            problems.append(f"ArrowRight on the scroller left it at {moved}px")
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(150)
    return problems

def compare_label_check(page):
    """The compare box is named, on a wide screen and on a phone.

    A bare box in a column of boxes is a puzzle. The wide layout names the
    column for a screen reader and shows the box it stands for, ticked, and the
    column is no wider than that mark needs: a word there took width from every
    other column. The phone card has no header, so the box has its own caption, in the same
    muted style as the other figures in the card. The caption is inside the
    label, so a tap on the word counts the row.
    """
    problems = []
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(150)
    head = page.evaluate(
        """() => {
            const th = document.querySelector('#tbl thead th.c-cmp');
            if (!th) return null;
            const name = th.querySelector('.vh');
            const icon = th.querySelector('.cmp-i');
            const box = document.querySelector('#tbl tbody td.c-cmp input');
            const cell = box ? box.closest('td') : null;
            const mid = (el) => {
                const r = el.getBoundingClientRect();
                return (r.left + r.right) / 2;
            };
            const box2 = icon ? icon.getBoundingClientRect() : null;
            return {
                text: name ? (name.textContent || '').trim() : '',
                icon: box2 ? Math.round(box2.width) : 0,
                iconHeight: box2 ? Math.round(box2.height) : 0,
                iconHidden: icon ? icon.getAttribute('aria-hidden') : '',
                width: Math.round(th.getBoundingClientRect().width),
                off: box && cell ? Math.round(mid(box) - mid(cell)) : 99
            };
        }"""
    )
    if head is None:
        problems.append("the compare column has no header")
    else:
        if head["text"].lower() != "compare":
            problems.append(f"the compare column header is named {head['text']!r}")
        if head["icon"] < 12:
            problems.append(f"the compare column's icon is {head['icon']}px wide")
        # The mark is a box, not the two panels it used to be: a square reads as
        # the checkbox the column is made of.
        if abs(head["icon"] - head["iconHeight"]) > 2:
            problems.append(
                f"the compare column's icon is {head['icon']}x{head['iconHeight']}px, not a square"
            )
        if head["iconHidden"] != "true":
            problems.append("the compare column's icon is not marked decorative")
        # The column is only as wide as the box and its icon need; the word it
        # used to carry is what made the column wider than the others.
        if head["width"] > 48:
            problems.append(
                f"the compare column is {head['width']}px wide, more than its icon needs"
            )
        if abs(head["off"]) > 1:
            problems.append(
                f"the compare box sits {head['off']}px off the middle of its cell"
            )
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(200)
    cap = page.evaluate(
        """() => {
            const cap = document.querySelector('tbody.item .cmp-cap');
            if (!cap) return null;
            const s = getComputedStyle(cap);
            const label = cap.closest('.cmp-w');
            const r = label.getBoundingClientRect();
            return {
                text: (cap.textContent || '').trim(),
                display: s.display,
                size: parseFloat(s.fontSize),
                width: Math.round(r.width),
                height: Math.round(r.height)
            };
        }"""
    )
    if cap is None:
        problems.append("the compare box has no caption on a phone")
    else:
        if cap["text"].lower() != "compare":
            problems.append(f"the compare caption reads {cap['text']!r}")
        if cap["display"] == "none":
            problems.append("the compare caption is hidden on a phone")
        if cap["size"] < 12:
            problems.append(f"the compare caption is {cap['size']}px")
        if cap["height"] < 44:
            problems.append(f"the compare target is {cap['height']}px tall, expected 44px")
        if cap["width"] < 44:
            problems.append(f"the compare target is {cap['width']}px wide, expected 44px")
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(150)
    return problems

def share_check(page):
    """A ?cmp= link reopens the same three models and drops unknown ids."""
    problems = []
    href = page.evaluate("() => location.href")
    if "?cmp=" not in href:
        problems.append(f"selecting three models did not update the URL: {href}")
    extra = page.context.new_page()
    try:
        extra.goto(href, wait_until="load")
        extra.wait_for_timeout(400)
        restored = extra.evaluate(
            """() => ({
                checked: Array.from(document.querySelectorAll('input.cmp:checked')).map((c) => c.value),
                compare: !document.getElementById('compare').hidden,
                names: Array.from(document.querySelectorAll('#cmp-table thead .cmp-name')).map((n) => n.textContent),
                rows: document.querySelectorAll('#cmp-table tbody tr').length
            })"""
        )
        if restored["checked"] != ["tapo-td21", "reo-poe", "ezviz-ep3x"]:
            problems.append(f"the shared link restored {restored['checked']}")
        if restored["rows"] != 18 or not restored["compare"]:
            problems.append(f"the shared link did not reopen the compare table: {restored}")
        if len(restored["names"]) != 3:
            problems.append(f"the shared compare table names {restored['names']}")
        base = href.split("?")[0]
        extra.goto(base + "?cmp=reo-poe,bogus,reo-poe", wait_until="load")
        extra.wait_for_timeout(300)
        filtered = extra.evaluate(
            """() => ({
                checked: Array.from(document.querySelectorAll('input.cmp:checked')).map((c) => c.value),
                compare: !document.getElementById('compare').hidden,
                search: location.search
            })"""
        )
        if filtered["checked"] != ["reo-poe"]:
            problems.append(f"unknown and duplicate ids were kept: {filtered['checked']}")
        if filtered["compare"]:
            problems.append("a one-model link opens the compare table")
        if filtered["search"] != "?cmp=reo-poe":
            problems.append(f"the link was not cleaned up: {filtered['search']}")
    finally:
        extra.close()
    return problems

# The compare table prints these spec rows under one cost row. The count is a
# property of that table, not of ROWS, so it is named here rather than counted
# from the dataset.
SPEC_ROWS = [
    "Records free?", "Price", "Free features", "3 yrs, no plan", "3 yrs, with plan",
    "Best for", "Main catch", "Power", "Storage", "Live view", "Motion alerts",
    "Smart detection", "History, no plan", "Behind the paywall", "Plans",
    "Home Assistant", "Wi-Fi",
]

COMPARE_ROWS = len(SPEC_ROWS) + 1

def compare_cells(rows):
    """The cheapest 3-year cost, what it is made of, and the two differences.

    A difference names the column it is measured against: the cheapest column
    can be scrolled out of view on a phone, where "+£25.00" alone does not say
    what it is more than.
    """
    by_id = {row["id"]: row for row in rows.ROWS}
    keeps = [(id, by_id[id]["keep3"]) for id in SHORTLIST_IDS]
    low_id, low = min(keeps, key=lambda pair: pair[1])
    base = f"{by_id[low_id]['brand']} {by_id[low_id]['model']}".replace(" Video Doorbell", "")
    cells = []
    for id, value in keeps:
        diff = (
            "cheapest of these 3"
            if abs(value - low) < 0.005
            else f"+£{value - low:.2f} more than {base}"
        )
        cells.append(f"£{value:.2f} {diff} {by_id[id]['keep_note']}")
    return cells

def photo_line_check(page):
    """Every compare column leaves the same line for its verdict.

    Seven rows carry a verdict and seven do not. A column without one started
    its photo 19px higher than the other two, so the three images did not line
    up and the cheapest row read as the odd one out. The badge line is reserved
    in every column now, written or not.
    """
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(150)
    state = page.evaluate(
        """() => Array.from(document.querySelectorAll('#cmp-table thead th[data-id]')).map((th) => {
            const photo = th.querySelector('.cmp-photo');
            const badge = th.querySelector('.vtag');
            return {
                id: th.dataset.id,
                verdict: badge ? badge.textContent.trim() : 'missing',
                top: photo ? Math.round(photo.getBoundingClientRect().top) : -1,
                line: badge ? Math.round(badge.getBoundingClientRect().height) : -1
            };
        })"""
    )
    if len(state) != 3:
        return [f"expected three compare columns, found {len(state)}"]
    problems = []
    tops = sorted({col["top"] for col in state})
    if len(tops) != 1:
        problems.append(
            "the compare photos start at "
            + ", ".join(f"{col['id']} {col['top']}px" for col in state)
            + ", not on one line"
        )
    lines = sorted({col["line"] for col in state})
    if len(lines) != 1:
        problems.append(
            "the badge lines are "
            + ", ".join(f"{col['id']} {col['line']}px" for col in state)
            + ", so an empty line is not the height of a written one"
        )
    # The alignment only means something if the trio includes a column without
    # a verdict, which is the case it was fixed for.
    if all(col["verdict"] not in ("", "missing") for col in state):
        problems.append(f"every column in this comparison carries a verdict: {[c['verdict'] for c in state]}")
    return problems

COLUMN_JS = """() => {
    const ths = Array.from(document.querySelectorAll('#cmp-table thead th[data-id]'));
    const cost = document.querySelector('#cmp-table tr.cmp-cost');
    const box = document.querySelector('.cmp-scroll').getBoundingClientRect();
    const price = cost.querySelector('td b').getBoundingClientRect();
    const hit = document.elementFromPoint(price.left + 4, price.top + price.height / 2);
    return {
        order: ths.map((th) => th.dataset.id),
        lefts: ths.map((th) => Math.round(th.getBoundingClientRect().left)),
        cols: ths.map((th) => {
            const move = th.querySelector('.cmp-move');
            if (!move) return { id: th.dataset.id, missing: true };
            const rule = th.getBoundingClientRect();
            const grip = move.querySelector('.grip').getBoundingClientRect();
            const target = move.getBoundingClientRect();
            return {
                id: th.dataset.id,
                rule: getComputedStyle(th).borderBottomColor,
                ruleY: Math.round(rule.bottom),
                gripY: Math.round(grip.top + grip.height / 2),
                gripIn: grip.left >= box.left - 1 && grip.right <= box.right + 1,
                target: [Math.round(target.width), Math.round(target.height)],
                label: move.getAttribute('aria-label')
            };
        }),
        costOrder: Array.from(cost.querySelectorAll('td')).map((td) => td.dataset.id),
        costs: Object.fromEntries(
            Array.from(cost.querySelectorAll('td')).map((td) => [td.dataset.id, td.textContent.trim()])
        ),
        overPrice: hit ? hit.tagName : '',
        focus: document.activeElement && document.activeElement.dataset
            ? document.activeElement.dataset.move : null,
        live: document.getElementById('live').textContent
    };
}"""

def column_move_check(page):
    """A dragged column takes its slot, and the arithmetic does not follow it.

    Each column carries a handle on its 3px rule, in a 44px target that stays in
    the header, so the price under it is still the reader's to click. A move
    slides the whole column, cost cell included, and rebuilds the table in the
    new order. The reference is the cheapest of the three, so a delta means the
    same thing wherever its column sits, and a verdict colour travels with the
    column that owns it rather than staying in the slot it left.
    """
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(120)
    page.locator("#cmp-table").scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    before = page.evaluate(COLUMN_JS)
    if len(before["order"]) != 3:
        return [f"expected three columns to arrange, found {len(before['order'])}"]
    # A build without the handles is the failure this check exists for, and it
    # should read as one, not as a crash on a missing box.
    missing = [col["id"] for col in before["cols"] if col.get("missing")]
    if missing:
        return [f"no column handle on {', '.join(missing)}"]
    problems = []
    for col in before["cols"]:
        if col["target"] != [44, 44]:
            problems.append(
                f"the {col['id']} handle's target is {col['target']}, not 44x44"
            )
        if abs(col["gripY"] - col["ruleY"]) > 1:
            problems.append(
                f"the {col['id']} handle sits {col['gripY'] - col['ruleY']}px off its rule"
            )
        if not col["gripIn"]:
            problems.append(f"the {col['id']} handle is cut by the edge of the comparison")
    if before["overPrice"] != "B":
        problems.append(
            f"the handle's target covers the cost row: {before['overPrice']!r} sits at the price"
        )

    moved, other = before["order"][1], before["order"][0]
    width = before["lefts"][1] - before["lefts"][0]
    box = page.locator(f'.cmp-move[data-move="{moved}"]').bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x - width * 0.8, y, steps=8)
    page.mouse.up()
    page.wait_for_timeout(900)
    after = page.evaluate(COLUMN_JS)

    expect = [moved, other, before["order"][2]]
    if after["order"] != expect:
        problems.append(f"dragging {moved} one slot left gave {after['order']}, expected {expect}")
    if after["costOrder"] != expect:
        problems.append(
            f"the cost row reads {after['costOrder']} after the move, expected {expect}"
        )
    if after["costs"] != before["costs"]:
        changed = [id for id in before["costs"] if after["costs"].get(id) != before["costs"][id]]
        problems.append(
            f"moving a column changed the figures of {changed}: the reference moved with it"
        )
    rules = {col["id"]: col["rule"] for col in before["cols"]}
    for col in after["cols"]:
        if col["rule"] != rules[col["id"]]:
            problems.append(
                f"{col['id']} lost its verdict rule in the move: {col['rule']} was {rules[col['id']]}"
            )
    landed = next(col for col in after["cols"] if col["id"] == moved)
    name = landed["label"].split(" left or right")[0].removeprefix("Move ")
    if landed["label"] != f"Move {name} left or right. Column 1 of 3.":
        problems.append(f"the moved handle is named {landed['label']!r} at column 1")
    if after["focus"] != moved:
        problems.append(f"focus went to {after['focus']!r} after the move, not {moved!r}")
    if after["live"] != f"{name} moved to column 1 of 3":
        problems.append(f"the move was announced as {after['live']!r}")
    # The address is the shareable copy of the arrangement, so a link carries
    # the order the reader left the columns in.
    query = page.evaluate("() => new URL(location.href).searchParams.get('cmp')")
    if (query or "").split(",") != expect:
        problems.append(f"the address still reads ?cmp={query!r}, not the arranged {expect}")

    # The run after this one shares the page, so the column goes back where the
    # reader found it, and the way back is the keyboard.
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(300)
    back = page.evaluate(COLUMN_JS)
    if back["order"] != before["order"]:
        problems.append(
            f"one ArrowRight did not put the columns back: {back['order']} is not {before['order']}"
        )
    return problems

CHECKS = [
    Check(
        "compare morph", "desktop", 37,
        "the tray becomes the compare header over 240ms, and the ticked rows' names and photos fly into their columns and back",
        lambda ctx: morph_check(ctx.page),
    ),
    Check(
        "shortlist copy", "compare", 40,
        "Copy shortlist writes the models, costs, catches and a ?cmp= link",
        lambda ctx: shortlist_check(ctx.page, ctx.checked),
    ),
    Check(
        "compare cost row", "compare", 41,
        "the compare table names the cheapest 3-year cost and each difference",
        lambda ctx: costrow_check(
            ctx.page, COMPARE_ROWS, compare_cells(ctx.dataset) if ctx.dataset else []
        ),
    ),
    Check(
        "share link", "compare", 42,
        "a ?cmp= link restores the three models and drops unknown ids",
        lambda ctx: share_check(ctx.page),
    ),
    Check(
        "compare chrome", "compare", 43,
        "the sort select is 44px and compare rows use 8/16px padding and aligned labels",
        lambda ctx: chrome_check(ctx.page),
    ),
    Check(
        "differences only", "compare", 44,
        "differences only hides identical spec rows, keeps the decision rows, and names its count",
        lambda ctx: diff_check(ctx.page, COMPARE_ROWS),
    ),
    Check(
        "compare markers", "compare", 45,
        "the comparison marks what is missing, leaves the good news alone, and names each row's verdict under its column's header",
        lambda ctx: marks_check(ctx.page),
    ),
    Check(
        "comparison scroller", "compare", 46,
        "the comparison's sideways scroll is a named, focusable region that snaps one model at a time, the cue names the first column the reader cannot read, and the arrow keys move it",
        lambda ctx: scroller_check(ctx.page),
    ),
    Check(
        "compare label", "compare", 47,
        "the compare box is named by an icon and a hidden name in a narrow column, and by a caption on a phone card",
        lambda ctx: compare_label_check(ctx.page),
    ),
    Check(
        "compare photos", "compare", 88,
        "the three compare photos start on one line, verdict or no verdict",
        lambda ctx: photo_line_check(ctx.page),
    ),
    Check(
        "compare column move", "compare", 90,
        "a dragged column takes its slot and keeps its verdict rule, the cost row moves with it, the figures do not move, and the handle sits on the rule in a 44px target",
        lambda ctx: column_move_check(ctx.page),
    ),
]

