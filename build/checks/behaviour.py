"""What the page does when it is used: the controls, the disclosures, the theme and the page's own text."""
import os

from .context import ROOT
from .js import BARS_JS, DESKTOP_ROWS_JS, FILTERS_JS, STUCK_JS
from .registry import Check


def lightbox_check(page):
    """Click the first photo, confirm the dialog, then dismiss it with Esc."""
    counts = page.evaluate(
        "() => ({buttons: document.querySelectorAll('.zoom').length, "
        "thumbs: document.querySelectorAll('img.ph-sm').length, "
        "dialog: !!document.getElementById('lightbox')})"
    )
    problems = []
    if not counts["dialog"]:
        return {"problems": ["photo lightbox is missing"], "buttons": 0}
    if counts["buttons"] < counts["thumbs"]:
        problems.append(
            f"only {counts['buttons']} lightbox buttons for {counts['thumbs']} photos"
        )
    if not counts["buttons"]:
        return {"problems": problems + ["no photo opens in the lightbox"], "buttons": 0}

    page.click(".zoom")
    page.wait_for_timeout(100)
    opened = page.evaluate(
        """() => {
            const d = document.getElementById('lightbox');
            const img = document.querySelector('#lb-img img');
            return {open: d.open, src: img ? (img.getAttribute('src') || '') : '',
                    name: document.getElementById('lb-name').textContent};
        }"""
    )
    if not opened["open"]:
        problems.append("clicking a photo did not open the lightbox")
    if not opened["src"].endswith("-lg.webp"):
        problems.append(f"lightbox opened {opened['src'] or 'no image'} instead of the large file")
    if not opened["name"]:
        problems.append("lightbox does not name the product")
    if opened["src"] and not os.path.exists(os.path.join(ROOT, opened["src"])):
        problems.append(f"lightbox image file is missing: {opened['src']}")

    page.keyboard.press("Escape")
    page.wait_for_timeout(50)
    if page.evaluate("() => document.getElementById('lightbox').open"):
        problems.append("Esc does not close the lightbox")

    # Three ways out: Escape, the button in the corner, and a tap anywhere off
    # the photo. The bar stays, because the name in it is there to be read.
    page.click(".zoom")
    page.wait_for_timeout(150)
    if not page.evaluate("() => document.getElementById('lightbox').open"):
        problems.append("the lightbox does not reopen for the close checks")
    else:
        page.click("#lb-x")
        page.wait_for_timeout(150)
        if page.evaluate("() => document.getElementById('lightbox').open"):
            problems.append("the close button in the corner does not close the photo")
        page.click(".zoom")
        page.wait_for_timeout(200)
        page.mouse.click(4, 4)
        page.wait_for_timeout(200)
        if page.evaluate("() => document.getElementById('lightbox').open"):
            problems.append("a tap off the photo does not close the lightbox")
        else:
            page.keyboard.press("Escape")
    return {"problems": problems, "buttons": counts["buttons"]}

def filters_check(page):
    """The phone filter panel is collapsed, and has to come back when the window widens."""
    problems = []
    page.set_viewport_size({"width": 900, "height": 900})
    page.wait_for_timeout(150)
    wide = page.evaluate(FILTERS_JS)
    if not wide["open"] or not wide["visible"]:
        problems.append(f"the filter panel stays closed at 900px: {wide}")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(150)
    narrow = page.evaluate(FILTERS_JS)
    if narrow["open"] or narrow["visible"]:
        problems.append(f"the filter panel stays open at 390px: {narrow}")
    return problems

def copy_check(page):
    """Three selections explain the cap, announce it, and refuse a fourth."""
    problems = []
    page.eval_on_selector_all(
        "input.cmp",
        """els => els.slice(0, 3).forEach(el => {
            el.checked = true;
            el.dispatchEvent(new Event("change", { bubbles: true }));
        })""",
    )
    page.wait_for_timeout(450)
    state = page.evaluate(
        """() => ({
            tray: document.getElementById("tray-txt").textContent,
            live: document.getElementById("live").textContent,
            inline: document.getElementById("cmp-inline").hidden
                ? null : document.getElementById("cmp-inline").textContent,
            disabled: Array.from(document.querySelectorAll("input.cmp"))
                .filter((c) => c.disabled).length
        })"""
    )
    if "maximum" not in state["tray"]:
        problems.append(f"the 3-row cap is not explained: {state['tray']!r}")
    if "maximum" not in state["live"]:
        problems.append(f"the 3-row cap is not announced: {state['live']!r}")
    if state["inline"] != "Compare 3":
        problems.append(f"the inline compare action reads {state['inline']!r}")
    # A box that greys out looks broken. The box stays live and the refusal is
    # explained where the reader is looking.
    if state["disabled"]:
        problems.append(f"{state['disabled']} checkboxes are disabled at three selections")
    # A real tap, because the refusal is a reader's rule: a script that sets
    # the selection is not second-guessed. The box is centred first, so the
    # sticky header and the tray cannot stand in the way of the click.
    page.evaluate(
        """() => {
            const fourth = Array.from(document.querySelectorAll('input.cmp'))
                .find((el) => !el.checked);
            fourth.scrollIntoView({ block: 'center' });
        }"""
    )
    page.click("input.cmp:not(:checked)")
    page.wait_for_timeout(300)
    refused = page.evaluate(
        """() => ({
            ticked: Array.from(document.querySelectorAll("input.cmp"))
                .filter((c) => c.checked).length,
            cap: document.getElementById("cmp-cap").textContent.trim(),
            hidden: document.getElementById("cmp-cap").hidden
        })"""
    )
    if refused["ticked"] != 3:
        problems.append(f"{refused['ticked']} boxes are ticked after a fourth was tried")
    if refused["hidden"] or "3" not in refused["cap"]:
        problems.append(f"the refused fourth box says nothing: {refused['cap']!r}")
    return problems

def recovery_check(page):
    """Filtering announces its count; an empty result offers the nearest match."""
    problems = []
    page.eval_on_selector_all(
        "input.cmp",
        """els => els.forEach(el => {
            el.checked = false;
            el.dispatchEvent(new Event("change", { bubbles: true }));
        })""",
    )
    page.eval_on_selector("#filters", "el => { el.open = true }")
    page.eval_on_selector(
        "#f-rec",
        "el => { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })) }",
    )
    page.wait_for_timeout(450)
    filtered = page.evaluate(
        "() => ({count: document.getElementById('count').textContent, "
        "live: document.getElementById('live').textContent})"
    )
    if filtered["count"] == "14" or "doorbells shown" not in filtered["live"]:
        problems.append(
            f"filtering set {filtered['count']} rows and announced {filtered['live']!r}"
        )

    for handle in ("#f-min", "#f-max"):
        page.eval_on_selector(
            handle,
            "el => { el.value = 300; el.dispatchEvent(new Event('input', { bubbles: true })) }",
        )
    page.wait_for_timeout(600)
    empty = page.evaluate(
        """() => ({
            visible: !document.getElementById("empty").hidden,
            text: document.getElementById("empty-txt").textContent.trim(),
            near: document.getElementById("near").hidden
                ? null : document.getElementById("near").textContent,
            live: document.getElementById("live").textContent
        })"""
    )
    if not empty["visible"] or not empty["near"]:
        problems.append(f"the empty state offers no nearest match: {empty}")
    elif "£" not in empty["near"]:
        problems.append(f"the nearest-match label has no price: {empty['near']!r}")
    # The message says which filter emptied the list, and the button says what
    # it moves, so one tap is enough to get out of the dead end.
    if "£" not in empty["text"] or "doorbell" not in empty["text"]:
        problems.append(f"the empty state does not name the filter: {empty['text']!r}")
    if empty["near"] and not any(
        word in empty["near"] for word in ("maximum", "minimum", "Show")
    ):
        problems.append(f"the recovery button does not say what it changes: {empty['near']!r}")
    if "No doorbells match" not in empty["live"]:
        problems.append(f"the empty result is not announced: {empty['live']!r}")
    else:
        # The two ways out read as one sentence when a single space separates
        # them, so they keep a gap while sharing the line.
        acts = page.evaluate(
            """() => {
                const a = document.getElementById('near').getBoundingClientRect();
                const b = document.getElementById('empty-reset').getBoundingClientRect();
                return { gap: Math.round(b.left - a.right), same: Math.abs(a.top - b.top) < 2 };
            }"""
        )
        if not acts["same"] or acts["gap"] < 8:
            problems.append(
                f"the two recovery actions sit {acts['gap']}px apart on "
                f"{'one' if acts['same'] else 'two'} lines, expected 8px on one"
            )
        page.click("#near")
        page.wait_for_timeout(400)
        after = page.evaluate(
            "() => Array.from(document.querySelectorAll('tbody.item'))"
            ".filter((r) => !r.hidden).length"
        )
        if after < 1:
            problems.append("the nearest-match button leaves the table empty")
    page.click("#reset")
    page.wait_for_timeout(150)
    return problems

def labels_check(page, rec_label="Only briefly (3 hrs)"):
    """The record column names a time limit, the plan column names its absence,
    PoE is defined at the filter, and the phone card labels every figure."""
    problems = []
    state = page.evaluate(
        """() => {
            const all = (s) => Array.from(document.querySelectorAll(s));
            const spec = ['.c-rec', '.c-price', '.c-nosub', '.c-sub'];
            const cells = spec.map((cls) => document.querySelector('#tbl tbody.item ' + cls));
            const nest = document.querySelector('#m-nest .c-rec');
            const price = document.querySelector('#tbl tbody.item .c-price');
            const catchCell = document.querySelector('#tbl tbody.item .c-catch');
            const subs = all('#tbl tbody.item .c-sub');
            // The top of the figure itself, not of its cell: a wrapped label
            // pushes the number down inside a cell that still starts level.
            const figureTop = (td) => {
                const first = td.firstChild;
                if (!first) return -1;
                if (first.nodeType === 1) return Math.round(first.getBoundingClientRect().top);
                const range = document.createRange();
                range.selectNodeContents(first);
                return Math.round(range.getBoundingClientRect().top);
            };
            const figures = all('#tbl tbody.item')
                .filter((row) => row.getClientRects().length)
                .map((row) => {
                    const nosub = row.querySelector('.c-nosub'), sub = row.querySelector('.c-sub');
                    return {
                        id: row.id.slice(2),
                        nosub: {x: Math.round(nosub.getBoundingClientRect().x), y: figureTop(nosub)},
                        sub: {x: Math.round(sub.getBoundingClientRect().x), y: figureTop(sub)}
                    };
                });
            const hint = document.querySelector('#filters .hint');
            const power = hint ? hint.closest('fieldset') : null;
            const pseudo = (el) => getComputedStyle(el, '::before');
            return {
                // The footnote number sits inside the label's block, so the
                // label is read from its own span, not the block's text.
                nestText: (nest.querySelector('.rec-t') || nest.querySelector('.rec')).textContent.trim(),
                nestClass: nest.querySelector('.rec').className,
                planWords: subs.filter((td) => /No plan/.test(td.textContent)).length,
                planRows: Array.from(document.querySelectorAll('#tbl tbody.item'))
                    .filter((row) => row.dataset.sub3 === '0').length,
                planDashes: subs.filter((td) => /\u2014/.test(td.textContent)).length,
                priceLabel: pseudo(price).content,
                catchLabel: pseudo(catchCell).content,
                displays: cells.map((td) => getComputedStyle(td).display),
                labels: cells.map((td) => pseudo(td).content),
                figures: figures,
                hint: hint ? hint.textContent.trim() : '',
                hintPower: !!(power && /Power/.test(power.querySelector('legend').textContent)),
                hintSize: hint ? getComputedStyle(hint).fontSize : '',
                hintVisible: hint ? hint.getClientRects().length > 0 : false
            };
        }"""
    )
    if state["nestText"] != rec_label:
        problems.append(f"the Nest record cell reads {state['nestText']!r}")
    if "rec-brief" not in state["nestClass"]:
        problems.append(f"the Nest record marker has the class {state['nestClass']!r}")
    if state["planWords"] != state["planRows"] or state["planDashes"]:
        problems.append(
            f"the plan column prints {state['planWords']} words for "
            f"{state['planRows']} rows without a plan, and "
            f"{state['planDashes']} bare dashes"
        )
    if "Price" not in state["priceLabel"]:
        problems.append(f"the phone price cell carries the label {state['priceLabel']}")
    if "Main catch" not in state["catchLabel"]:
        problems.append(f"the catch cell lost its label: {state['catchLabel']}")
    # The two 3-year cells are subgrids on a phone, so their labels and figures
    # can share rows with the cell beside them; the rest are block rows.
    if any(display not in ("block", "grid") for display in state["displays"]):
        problems.append(
            f"the phone spec cells are {state['displays']}, expected block rows"
        )
    for want in ("Records free?", "Price", "3 years, no plan", "3 years, with plan"):
        if not any(want in label for label in state["labels"]):
            problems.append(f"the phone labels read {state['labels']}, missing {want!r}")
    # The two 3-year figures are read against each other, so they sit side by
    # side and their numbers start on the same line in every card, whichever of
    # the two labels wraps.
    if len(state["figures"]) < 10:
        problems.append(f"only {len(state['figures'])} phone cards to measure")
    crooked = [
        f"{fig['id']} {fig['nosub']['y']}/{fig['sub']['y']}px"
        for fig in state["figures"]
        if abs(fig["nosub"]["y"] - fig["sub"]["y"]) > 2
    ]
    if crooked:
        problems.append(f"the two 3-year figures start on different lines: {crooked[:3]}")
    stacked = [fig["id"] for fig in state["figures"] if fig["nosub"]["x"] >= fig["sub"]["x"]]
    if stacked:
        problems.append(f"{len(stacked)} cards stack the two 3-year figures")
    if not state["hint"].startswith("PoE"):
        problems.append(f"the Power filter has no PoE note: {state['hint']!r}")
    if not state["hintPower"]:
        problems.append("the PoE note is not inside the Power fieldset")
    if state["hintSize"] != "12px":
        problems.append(f"the PoE note is {state['hintSize']}, expected 12px")
    return problems

def card_check(page, dataset, checked):
    """Every figure opens its own source card, and the card carries the record.

    The card is where the page's evidence lives now: the figure a reader doubts
    opens a dialog holding the page behind it, the sentence in the dataset that
    supports it, the day the prices were checked and, for a 3-year total, the sum
    it is made of. A figure that opens nothing, or a card that arrives empty, is
    the failure this is here to catch.
    """
    if not dataset:
        return []
    problems = []
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(150)

    # A label is the sentence the reader hears before they go anywhere, so an
    # entity in one means the escaping went round twice: "Ring&#x27;s cloud" is
    # not a sentence, it is the markup of one.
    entities = page.evaluate(
        """() => Array.from(document.querySelectorAll('a.src[aria-label]'))
            .map((a) => a.getAttribute('aria-label'))
            .filter((name) => name.indexOf('&#') > -1 || name.indexOf('&amp;') > -1)"""
    )
    for name in entities[:3]:
        problems.append(f"a figure is announced as {name!r}, with an entity in it")

    def card_words(row, claim):
        """The sentence and the pages a card prints, read from the dataset.

        This is the rule the build follows, restated here, so that a card which
        drifts from the figure it opens from fails rather than agreeing with a
        copy of the build's own mistake. The sentence has to answer the
        question the card's title asks: the recording question is the row's
        history line, not the storage line, which said "None" beside a figure
        that reads "Only briefly (3 hrs)".
        """
        if claim == "plan":
            keys = [row["plan_src"], row["price_src"]] if row["sub"] is not None else [row["plan_src"]]
            words = row["sub_text"] if row["sub"] is not None else row["storage"]
        elif claim == "rec":
            keys, words = [row["rec_src"], row["history_src"]], row["history"]
        elif claim == "nosub":
            keys = [row["price_src"], row["rec_src"] if row["extra"] else row["history_src"]]
            words = row["storage"] if row["extra"] else row["history"]
        else:
            raise ValueError(f"no card sentence is read for the {claim} claim")
        return words, list(dict.fromkeys(keys))

    def read(id_, claim):
        return page.evaluate(
            """([id, claim]) => {
                const a = document.querySelector('#m-' + id + ' a.src[data-claim="' + claim + '"]');
                if (!a) return { missing: true };
                a.click();
                const card = document.getElementById('card');
                const line = (s) => {
                    const el = card.querySelector(s);
                    return el && !el.hidden ? el.textContent.trim() : '';
                };
                return {
                    missing: false,
                    open: card.open,
                    inside: card.contains(document.activeElement),
                    title: card.querySelector('#card-h').textContent.trim(),
                    say: line('.card-say'),
                    arc: line('.card-arc'),
                    note: line('.card-note'),
                    date: line('.card-date'),
                    srcs: Array.from(card.querySelectorAll('.card-srcs a'))
                        .map((l) => [l.textContent.trim(), l.getAttribute('href')])
                };
            }""",
            [id_, claim],
        )

    # A row with a plan, a row without one, and the row whose card opened this
    # check: the two 3-year figures are the page's own arithmetic and have to
    # show the sum they are, and the recording verdict has to quote the row.
    for id_, claim, title in (
        ("reo-poe", "nosub", "Reolink Video Doorbell PoE \u00b7 The 3-year cost with no plan"),
        ("ring", "plan", "Ring Battery Video Doorbell 2K \u00b7 The 3-year cost with a plan"),
        ("nest", "rec", "Google Nest Doorbell (battery) \u00b7 Records free without a plan"),
    ):
        row = next((r for r in dataset.ROWS if r["id"] == id_), None)
        if row is None:
            problems.append(f"no {id_} in the dataset to open a card from")
            continue
        state = read(id_, claim)
        if state.get("missing"):
            problems.append(f"{id_} has no {claim} source card")
            continue
        if not state["open"] or not state["inside"]:
            problems.append(f"the {id_} {claim} card opened without taking the reader to it")
        if state["title"] != title:
            problems.append(f"the {id_} {claim} card is titled {state['title']!r}, expected {title!r}")
        words, keys = card_words(row, claim)
        if state["say"] != words:
            problems.append(f"the {id_} {claim} card quotes {state['say']!r}, expected {words!r}")
        # A recording verdict is not a sum, so only the totals carry one.
        want_arc = "" if claim == "rec" else row["maths_sub" if claim == "plan" else "maths_free"]
        if state["arc"] != want_arc:
            problems.append(
                f"the {id_} {claim} card shows the sum as {state['arc']!r}, expected {want_arc!r}"
            )
        want = [[dataset.S[k][0], dataset.S[k][1]] for k in keys]
        if state["srcs"] != want:
            problems.append(f"the {id_} {claim} card lists {state['srcs']}, expected {want}")
        if state["date"] != f"Prices and plans checked {checked}.":
            problems.append(f"the {id_} {claim} card is dated {state['date']!r}")
        # The card or USB stick in a 3-year sum is the page's one assumption, so
        # the card showing that sum has to say so; a plan bought in the UK must
        # not carry the euro warning.
        if claim == "nosub":
            if row["extra"] and "assumption" not in state["note"]:
                problems.append(f"the {id_} {claim} card does not say its card price is an assumption")
        elif row["plan_region"] != "EU" and state["note"]:
            problems.append(
                f"the {id_} {claim} card warns {state['note']!r} about a UK price"
            )
        # Escape is the dialog's own; closing has to hand the reader back to the
        # figure they tapped, which is where they were reading.
        page.keyboard.press("Escape")
        page.wait_for_timeout(120)
        closed = page.evaluate(
            """([id, claim]) => ({
                open: document.getElementById('card').open,
                back: document.activeElement === document.querySelector(
                    '#m-' + id + ' a.src[data-claim="' + claim + '"]')
            })""",
            [id_, claim],
        )
        if closed["open"] or not closed["back"]:
            problems.append(f"closing the {id_} {claim} card left {closed} behind")

    # The two recording figures sit on every row, so their cards are read on
    # every row: one row was enough to find the fault, and not enough to hold
    # it, because whether the sentence answers the figure turns on what that
    # row's no-plan route does rather than on anything the row's neighbours do.
    every = page.evaluate(
        """() => {
            const card = document.getElementById('card');
            const out = [];
            for (const item of document.querySelectorAll('tbody.item')) {
                for (const claim of ['rec', 'nosub']) {
                    const a = item.querySelector('a.src[data-claim="' + claim + '"]');
                    if (!a) {
                        out.push({ id: item.dataset.id, claim, missing: true });
                        continue;
                    }
                    a.click();
                    out.push({
                        missing: false, id: item.dataset.id, claim, open: card.open,
                        say: card.querySelector('.card-say').textContent.trim(),
                        srcs: Array.from(card.querySelectorAll('.card-srcs a'))
                            .map((l) => l.getAttribute('href'))
                    });
                    card.close();
                }
            }
            return out;
        }"""
    )
    for state in every:
        row = next((r for r in dataset.ROWS if r["id"] == state["id"]), None)
        if row is None:
            problems.append(f"the table has a {state['id']} row the dataset does not")
            continue
        if state.get("missing"):
            problems.append(f"{state['id']} has no {state['claim']} source card")
            continue
        if not state["open"]:
            problems.append(f"the {state['id']} {state['claim']} card did not open")
        words, keys = card_words(row, state["claim"])
        if state["say"] != words:
            problems.append(
                f"the {state['id']} {state['claim']} card quotes {state['say']!r}, "
                f"expected the row's own {words!r}"
            )
        want = [dataset.S[k][1] for k in keys]
        if state["srcs"] != want:
            problems.append(
                f"the {state['id']} {state['claim']} card lists {state['srcs']}, expected {want}"
            )

    # The comparison repeats the table's figures, so it has to repeat their
    # cards: the anchor there is copied from the row's own, and this is what
    # proves the copy carries the same page and the same name.
    panel = page.evaluate(
        """() => {
            const a = document.querySelector('#cmp-table td a.src[data-claim]');
            if (!a) return { missing: true };
            a.click();
            const t = document.querySelector('#m-' + a.dataset.id + ' a.src[data-claim="' + a.dataset.claim + '"]');
            const card = document.getElementById('card');
            const srcs = Array.from(card.querySelectorAll('.card-srcs a')).map((l) => l.getAttribute('href'));
            const state = {
                missing: false, open: card.open, id: a.dataset.id, claim: a.dataset.claim,
                title: card.querySelector('#card-h').textContent.trim(),
                same: !!t && t.getAttribute('href') === a.getAttribute('href')
                    && t.getAttribute('aria-label') === a.getAttribute('aria-label'),
                srcs,
                spoke: a.getAttribute('aria-haspopup')
            };
            card.close();
            return state;
        }"""
    )
    if panel.get("missing"):
        problems.append("no figure in the comparison opens a source card")
    else:
        if not panel["open"]:
            problems.append("a comparison figure did not open a card")
        if not panel["same"]:
            problems.append(
                f"the comparison's {panel['id']} {panel['claim']} card does not match the table's"
            )
        name = next((f"{r['brand']} {r['model']}" for r in dataset.ROWS if r["id"] == panel["id"]), "")
        if not name or not panel["title"].startswith(name):
            problems.append(f"the comparison card is titled {panel['title']!r}, for {panel['id']}")
        if not panel["srcs"]:
            problems.append("the comparison's card has no source in it")
        if panel["spoke"] != "dialog":
            problems.append("a figure does not say it opens a dialog")

    # The comparison's 3-year total is the page's headline figure, and it is
    # whichever of the row's two 3-year figures is the cheaper route: the no-plan
    # total for a row that records without a plan, the plan's for a row whose
    # cheapest route is a plan. Its card has to be the one behind that figure, so
    # a reader who doubts the number lands on the page the number came from.
    totals = page.evaluate(
        """() => Array.from(document.querySelectorAll('#cmp-table .cmp-cost td')).map((td) => ({
            id: td.dataset.id,
            keep: (document.getElementById('m-' + td.dataset.id) || { dataset: {} }).dataset.keep,
            claim: (td.querySelector('a.src') || { dataset: {} }).dataset.claim || ''
        }))"""
    )
    if not totals:
        problems.append("the comparison has no 3-year total to open a card from")
    for cell in totals:
        want = {"nosub": "nosub", "sub": "plan"}.get(cell["keep"], "")
        if want and cell["claim"] != want:
            problems.append(
                f"the comparison's {cell['id']} total ({cell['keep']}) opens "
                f"{cell['claim'] or 'nothing'}, expected the {want} card"
            )

    # The phase's three models all record without a plan, so no total taken from
    # the plan route is in the panel to be read. One is put in their place, read,
    # and their three are handed back, because the checks after this one read the
    # page this check found.
    plan_row = next(
        (r for r in dataset.ROWS if r["keep_basis"] == "sub" and r["sub3"] is not None), None
    )
    if plan_row is None:
        problems.append("no row's cheapest 3-year route is a plan, so nothing can be read")
    else:
        swapped = page.evaluate(
            """([id]) => {
                const boxes = Array.from(document.querySelectorAll('input.cmp'));
                const before = boxes.filter((c) => c.checked).map((c) => c.value);
                const box = boxes.find((c) => c.value === id);
                if (!box || before.indexOf(id) > -1) return { skipped: true };
                const drop = boxes.find((c) => before.indexOf(c.value) > -1);
                const flip = (el, on) => {
                    el.checked = on;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                };
                flip(drop, false);
                flip(box, true);
                const td = document.querySelector('#cmp-table .cmp-cost td[data-id="' + id + '"]');
                const a = td && td.querySelector('a.src');
                const state = {
                    skipped: false,
                    claim: (a || { dataset: {} }).dataset.claim || '',
                    href: a ? a.getAttribute('href') : '',
                    total: td ? td.textContent.trim() : ''
                };
                flip(box, false);
                flip(drop, true);
                return state;
            }""",
            [plan_row["id"]],
        )
        if swapped.get("skipped"):
            problems.append(
                f"{plan_row['id']} is not in the comparison, so its total cannot be read"
            )
        else:
            if swapped["claim"] != "plan":
                problems.append(
                    f"the plan-route total for {plan_row['id']} opens "
                    f"{swapped['claim'] or 'nothing'}, expected the plan's card"
                )
            if swapped["href"] != dataset.S[plan_row["plan_src"]][1]:
                problems.append(
                    f"the plan-route total for {plan_row['id']} points at {swapped['href']!r}"
                )
            want_total = dataset.money(plan_row["keep3"], None)
            if not swapped["total"].startswith(want_total):
                problems.append(
                    f"the plan-route total for {plan_row['id']} reads {swapped['total']!r}, "
                    f"expected it to start with {want_total!r}"
                )

    # On a phone the card docks to the bottom edge, and the figure the reader
    # tapped stays on the screen: in the middle, that is where it was, and at the
    # bottom edge the page brings it up rather than leaving it behind the card.
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(150)

    def tap(block):
        return page.evaluate(
            """(block) => {
                const a = document.querySelector('#m-reo-poe .c-nosub a.src');
                const card = document.getElementById('card');
                if (card.open) card.close();
                a.scrollIntoView({ block });
                a.click();
                const c = card.getBoundingClientRect(), r = a.getBoundingClientRect();
                const state = {
                    open: card.open,
                    docked: Math.round(window.innerHeight - c.bottom),
                    width: Math.round(c.width),
                    view: window.innerWidth,
                    // Geometry, not hit-testing: a modal dialog's backdrop covers
                    // the page, so whether the figure is still readable is
                    // decided by where the two boxes are. Read after the click,
                    // because the card may have moved the page to get there.
                    figureVisible: r.bottom <= c.top + 1
                };
                card.close();
                return state;
            }""",
            block,
        )

    for where, block in (("the middle of the screen", "center"), ("the bottom edge", "end")):
        phone = tap(block)
        if not phone["open"]:
            problems.append(f"a phone figure tapped at {where} did not open a card")
        if phone["docked"] > 16:
            problems.append(f"the phone card floats {phone['docked']}px off the bottom edge")
        if phone["width"] < phone["view"] - 32:
            problems.append(
                f"the phone card is {phone['width']}px wide on a {phone['view']}px screen"
            )
        if not phone["figureVisible"]:
            problems.append(f"the phone card covers the figure it opened from, tapped at {where}")
    page.set_viewport_size({"width": 1280, "height": 900})
    return problems


def sources_check(page, source_count):
    """The numbered sources sit with the working, grouped by host.

    Every figure carries its own card now, so a reader with a script never opens
    this list; it is what the printed sheet and the reader without a script
    read, which is why it stays on the page and why its layout is still
    measured. The measurement shows it, and puts the page back as it was.
    """
    problems = []

    def read():
        return page.evaluate(
            """() => {
                const box = document.getElementById('sources');
                const restore = box.style.display;
                box.style.display = 'block';
                const summary = box.querySelector('summary');
                const fits = box.scrollWidth <= box.clientWidth + 1;
                const values = Array.from(box.querySelectorAll('li')).map((li) => +li.getAttribute('value'));
                const groups = Array.from(box.querySelectorAll('.fns-g')).map((g) => ({
                    host: g.querySelector('h3').textContent.trim(),
                    n: g.querySelectorAll('li').length,
                    foreign: Array.from(g.querySelectorAll('li a'))
                        .filter((a) => !a.href.toLowerCase().includes(g.querySelector('h3').textContent.trim()))
                        .map((a) => a.href)
                }));
                const method = box.closest('section.method');
                const copy = method.querySelector('.method-copy');
                const b = box.getBoundingClientRect();
                const c = copy.getBoundingClientRect();
                // The copy's cap is 80ch of its own font, and a ch measured the
                // same way is the only comparable width: a pixel cap would be
                // one font's cap.
                const probe = document.createElement('span');
                probe.style.cssText = 'position:absolute;left:0;top:0;visibility:hidden;width:80ch;height:0';
                method.appendChild(probe);
                const ch80 = probe.getBoundingClientRect().width;
                probe.remove();
                const m = method.getBoundingClientRect();
                const gap = parseFloat(getComputedStyle(box.querySelector('.fns-wrap')).columnGap);
                // How many lists of groups the reader sees, read off the boxes
                // rather than the column-count the stylesheet asked for.
                const cols = new Set(Array.from(box.querySelectorAll('.fns-g'))
                    .map((g) => Math.round(g.getBoundingClientRect().left))).size;
                // A host name is one unbreakable word, so a list narrower than
                // the longest one paints it across the gap.
                const clipped = Array.from(box.querySelectorAll('.fns-g h3'))
                    .filter((h) => h.scrollWidth > h.clientWidth + 1)
                    .map((h) => h.textContent.trim());
                const out = {
                    inMethod: !!box.closest('section.method'),
                    clipped,
                    // Above the phone layout the list is a column of its own,
                    // beside the working; on a phone it follows it.
                    beside: b.left >= c.right - 1 && Math.abs(b.top - c.top) <= 2,
                    below: b.top >= c.bottom - 1,
                    ch80,
                    copyWidth: c.width,
                    methodRight: m.right,
                    boxRight: b.right,
                    gap,
                    cols,
                    visible: box.getClientRects().length > 0,
                    fits,
                    tag: box.tagName,
                    open: box.open,
                    summary: summary.textContent.replace(/\s+/g, ' ').trim(),
                    headingInSummary: !!summary.querySelector('h2'),
                    summaryHeight: Math.round(summary.getBoundingClientRect().height),
                    count: values.length,
                    values: values.slice().sort((a, b) => a - b),
                    groups: groups
                };
                // Put the page back as the check found it: with a script the
                // register is off the screen, and the checks after this one read
                // the live page.
                box.style.display = restore;
                return out;
            }"""
        )

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(200)
    phone = read()

    page.set_viewport_size({"width": 821, "height": 900})
    page.wait_for_timeout(200)
    narrow = read()

    page.set_viewport_size({"width": 900, "height": 900})
    page.wait_for_timeout(200)
    mid = read()

    page.set_viewport_size({"width": 1101, "height": 900})
    page.wait_for_timeout(200)
    tight = read()

    page.set_viewport_size({"width": 1200, "height": 900})
    page.wait_for_timeout(200)
    three = read()

    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(200)
    wide = read()

    page.set_viewport_size({"width": 1300, "height": 900})
    page.wait_for_timeout(200)
    four = read()

    # The host headings are the one unbreakable word in the list, and the CI
    # machine's DejaVu is wider than Windows' Segoe UI: a width that fits one
    # font clips the other. Widen the type at the narrowest four-list width so
    # a missing break shows up on either machine, not only on Linux.
    page.evaluate(
        "() => document.documentElement.style.setProperty('--sans', 'Verdana, DejaVu Sans, sans-serif')"
    )
    page.wait_for_timeout(150)
    wide_font = read()
    page.evaluate("() => document.documentElement.style.removeProperty('--sans')")
    page.wait_for_timeout(150)
    if wide_font["clipped"]:
        problems.append(f"a host name clips under a wide font: {wide_font['clipped']}")
    if not wide_font["fits"]:
        problems.append("the source list is wider than its column under a wide font")

    desktop = (("1300px", four), ("1280px", wide), ("1200px", three), ("1101px", tight), ("900px", mid), ("821px", narrow))
    for where, state in desktop + (("390px", phone),):
        if not state["inMethod"]:
            problems.append(f"the source list is not with the working at {where}")
        if not state["visible"]:
            problems.append(f"the source list is not on screen at {where}")
        if state["clipped"]:
            problems.append(f"a host name is clipped at {where}: {state['clipped']}")
    for where, state in desktop:
        if not state["open"]:
            problems.append(f"the source list is closed at {where}, so nothing was measured")
        if not state["beside"] or state["below"]:
            problems.append(
                f"the source list is not beside the working at {where}: {state['beside']}"
            )
        if state["copyWidth"] > state["ch80"] + 1:
            problems.append(
                f"the copy runs {state['copyWidth']:.0f}px wide at {where}, past its "
                f"80ch measure of {state['ch80']:.0f}px"
            )
        if abs(state["boxRight"] - state["methodRight"]) > 1:
            problems.append(
                f"the sources leave {state['methodRight'] - state['boxRight']:.0f}px of "
                f"the working's row unused at {where}"
            )
    if not phone["below"]:
        problems.append("the source list does not sit under the working on a phone")
    for where, state, expected in (
        ("1300px", four, 4),
        ("1280px", wide, 3),
        ("1200px", three, 3),
        ("1101px", tight, 2),
        ("900px", mid, 1),
        ("821px", narrow, 1),
    ):
        if state["cols"] != expected:
            problems.append(
                f"the sources run in {state['cols']} list(s) at {where}, expected {expected}"
            )
    for where, state in (("1300px", four), ("1200px", three), ("1101px", tight)):
        if round(state["gap"]) != 32:
            problems.append(
                f"the source columns sit {state['gap']:.0f}px apart at {where}, expected 32px"
            )
    if phone["tag"] != "DETAILS" or wide["tag"] != "DETAILS":
        problems.append(f"the source list is a {phone['tag']}, not a disclosure")
    if phone["open"]:
        problems.append("the source list is open on a 390px screen")
    if wide["count"] != source_count:
        problems.append(f"the source list holds {wide['count']} entries, expected {source_count}")
    if wide["values"] != list(range(1, source_count + 1)):
        problems.append(f"the footnote numbers are not 1 to {source_count}: {wide['values'][:6]}")
    if wide["headingInSummary"] is False:
        problems.append("the Sources heading is no longer a heading inside the summary")
    if f"{source_count} links" not in wide["summary"]:
        problems.append(f"the summary reads {wide['summary']!r}")
    for where, state in desktop + (("390px", phone),):
        if state["summaryHeight"] < 24:
            problems.append(f"the summary is {state['summaryHeight']}px tall at {where}")
        if not state["fits"]:
            problems.append(f"the source list is wider than its column at {where}")
    if len(wide["groups"]) < 10:
        problems.append(f"the list has {len(wide['groups'])} host groups")
    if sum(group["n"] for group in wide["groups"]) != source_count:
        problems.append(f"the groups hold {[g['n'] for g in wide['groups']]}")
    foreign = [link for group in wide["groups"] for link in group["foreign"]]
    if foreign:
        problems.append(f"links sit under the wrong host: {foreign[:3]}")
    return problems

def footer_check(page, checked=None):
    """The page ends with the date, an owner, a contact route and a way back."""
    state = page.evaluate(
        """() => {
            const f = document.querySelector('footer.foot');
            if (!f) return null;
            return {
                text: f.textContent.replace(/\\s+/g, ' ').trim(),
                size: getComputedStyle(f).fontSize,
                border: parseFloat(getComputedStyle(f).borderTopWidth),
                links: Array.from(f.querySelectorAll('a')).map((a) => a.getAttribute('href')),
                paragraphs: f.querySelectorAll('p').length,
                height: Math.round(f.getBoundingClientRect().height),
                last: f === document.querySelector('main').lastElementChild
            };
        }"""
    )
    if not state:
        return ["the page has no closing line"]
    problems = []
    expected = f"Last checked {checked}" if checked else "Last checked "
    if not state["text"].startswith(expected):
        problems.append(f"the closing line reads {state['text'][:40]!r}")
    if "#tbl" not in state["links"]:
        problems.append(f"the closing line has no way back: {state['links']}")
    if not any((link or "").startswith("mailto:") for link in state["links"]):
        problems.append(f"the closing line has no email address: {state['links']}")
    if state["paragraphs"] < 2:
        problems.append("the closing line does not say who runs the site")
    if "SubFree UK is" not in state["text"]:
        problems.append("the closing line does not name the site")
    if state["size"] != "13px" or state["border"] != 1:
        problems.append(
            f"the closing line is {state['size']} with a {state['border']}px rule, "
            "expected 13px and 1px"
        )
    if not state["last"] or state["height"] > 320:
        problems.append(f"the closing line sits at {state['height']}px and is not last")

    # Back to top: out of the way above the table, offered once the reader is
    # into it, and it returns the reader and the keyboard to the heading.
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    top = page.evaluate(
        """() => {
            const b = document.getElementById('totop');
            return b ? { hidden: b.hidden, label: b.getAttribute('aria-label') } : null;
        }"""
    )
    if not top:
        problems.append("the page has no back-to-top button")
    else:
        if not top["hidden"]:
            problems.append("the back-to-top button is offered at the top of the page")
        if not (top["label"] or "").lower().startswith("back to top"):
            problems.append(f"the back-to-top button is named {top['label']!r}")
        # Past the sentinel, which sits above the table, so the button has a
        # reason to appear whatever the page's height happens to be.
        page.evaluate(
            """() => {
                const s = document.getElementById('totop-s');
                const y = s.getBoundingClientRect().top + window.scrollY;
                window.scrollTo(0, y + 600);
            }"""
        )
        shown = True
        try:
            page.wait_for_function(
                "() => !document.getElementById('totop').hidden", timeout=2000
            )
        except Exception:
            shown = False
        if not shown:
            problems.append("the back-to-top button never appears once the table has scrolled")
        else:
            page.click("#totop")
            page.wait_for_timeout(900)
            back = page.evaluate(
                """() => ({
                    y: Math.round(window.scrollY),
                    focus: document.activeElement ? document.activeElement.tagName : ''
                })"""
            )
            if back["y"] > 40:
                problems.append(f"Back to top left the page at {back['y']}px")
            if back["focus"] != "H1":
                problems.append(f"Back to top leaves focus on {back['focus'] or 'nothing'}")
    return problems

def rule_check(page, row_count):
    """A hairline along the table reports scroll position; it never hijacks it."""
    problems = []
    page.evaluate("() => scrollTo(0, 0)")
    page.wait_for_timeout(150)
    box = page.evaluate(
        """() => {
            const w = document.querySelector('.tbl-w'), pr = w.querySelector('.prog'), i = pr.querySelector('i');
            const t = document.getElementById('tbl'), s = getComputedStyle(i);
            return {
                inWrapper: w.contains(t) && w.firstElementChild === pr,
                static: { h: getComputedStyle(pr).height, pe: getComputedStyle(pr).pointerEvents,
                          hidden: pr.getAttribute('aria-hidden') },
                anim: { name: s.animationName, timeline: s.animationTimeline, range: s.animationRange },
                height: Math.round(w.getBoundingClientRect().height - t.getBoundingClientRect().height),
                rows: t.querySelectorAll('tbody.item').length
            };
        }"""
    )
    if not box["inWrapper"] or box["rows"] != row_count:
        problems.append(f"the rule is not the first child of the table's box: {box}")
    if box["static"] != {"h": "2px", "pe": "none", "hidden": "true"}:
        problems.append(f"the rule is not a silent 2px hairline: {box['static']}")
    if box["height"] != 0:
        problems.append(f"the wrapper adds {box['height']}px to the table")
    if box["anim"] != {"name": "rule", "timeline": "--tbl", "range": "cover"}:
        problems.append(f"the rule is not driven by the table's own timeline: {box['anim']}")

    samples = []
    for frac in (0.2, 0.5, 0.9):
        page.evaluate(
            """(f) => {
                const r = document.getElementById('tbl').getBoundingClientRect();
                scrollTo(0, scrollY + r.top + r.height * f - 300);
            }""",
            frac,
        )
        page.wait_for_timeout(120)
        samples.append(
            page.evaluate(
                """() => {
                    const pr = document.querySelector('.prog');
                    const m = new DOMMatrix(getComputedStyle(pr.querySelector('i')).transform);
                    return { top: Math.round(pr.getBoundingClientRect().top), fill: +m.a.toFixed(3) };
                }"""
            )
        )
    fills = [s["fill"] for s in samples]
    if any(b <= a for a, b in zip(fills, fills[1:])):
        problems.append(f"the rule does not grow with scroll: {fills}")
    if fills[-1] < 0.7 or fills[0] > 0.45:
        problems.append(f"the rule does not track the table's own span: {fills}")
    if any(s["top"] != 0 for s in samples[1:]):
        problems.append(f"the rule does not stay at the top of the viewport: {samples}")

    # No timeline support means the @supports block never applies: an empty hairline.
    page.evaluate("() => { document.querySelector('.prog i').style.animation = 'none' }")
    page.wait_for_timeout(80)
    plain = page.evaluate(
        """() => {
            const i = document.querySelector('.prog i');
            return { t: getComputedStyle(i).transform, h: getComputedStyle(i).height };
        }"""
    )
    if plain != {"t": "matrix(0, 0, 0, 1, 0, 0)", "h": "2px"}:
        problems.append(f"without the timeline the rule is not a plain hairline: {plain}")
    page.evaluate("() => { document.querySelector('.prog i').style.animation = ''; scrollTo(0, 0) }")
    page.wait_for_timeout(150)
    return problems

def head_check(page):
    """The compare header keeps its heading on one line and its links together.

    Clear sits beside Copy shortlist and Close, so a phone must not break the
    heading across two lines or leave one link alone on a third.
    """
    problems = []
    width = page.evaluate("() => innerWidth")
    page.evaluate(
        """() => {
            const ids = ['reo-poe', 'reo-wifi', 'reo-batt'];
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = ids.indexOf(c.value) > -1;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(150)
    page.evaluate("() => document.getElementById('cmp-inline').click()")
    page.wait_for_timeout(450)
    shape = page.evaluate(
        """() => {
            const head = document.querySelector('.cmp-head');
            const h2 = document.getElementById('cmp-h').getBoundingClientRect();
            const links = Array.from(document.querySelectorAll('.cmp-links > *'))
                .map((el) => Math.round(el.getBoundingClientRect().top));
            return {
                headH: Math.round(head.getBoundingClientRect().height),
                heading: [Math.round(h2.width), Math.round(h2.height)],
                linkTops: links,
                over: Math.round(head.scrollWidth - head.clientWidth)
            };
        }"""
    )
    if shape["heading"][1] > 30:
        problems.append(f"at {width}px the compare heading wraps: {shape['heading']}")
    if len(set(shape["linkTops"])) != 1:
        problems.append(f"at {width}px the header links split across rows: {shape['linkTops']}")
    if shape["over"] > 1:
        problems.append(f"at {width}px the compare header overflows by {shape['over']}px")
    page.evaluate(
        """() => {
            document.getElementById('cmp-close').click();
            document.querySelectorAll('input.cmp').forEach((c) => {
                c.checked = false;
                c.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }"""
    )
    page.wait_for_timeout(250)
    return problems

def sort_figure_check(page):
    """The order follows a figure the row bolds, and the note names it.

    The default sort is by the 3-year cost to keep recordings, which is not a
    column of its own: Ring's figure comes from its plan and Reolink PoE's from
    the card in its box. Without the bold cell and the note under the control,
    the list reads as mis-sorted. The other sorts bold what they order by, or
    nothing when the figure is a column of its own.
    """
    problems = []
    state = page.evaluate(
        """() => {
            const read = () => {
                const note = document.getElementById('sortnote');
                return {
                    note: (note.textContent || '').trim(),
                    rows: Array.from(document.querySelectorAll('#tbl tbody.item')).map((t) => ({
                        id: t.id.slice(2),
                        basis: t.dataset.keep,
                        bold: Array.from(t.querySelectorAll('.c-nosub,.c-sub'))
                            .filter((c) => c.classList.contains('keep'))
                            .map((c) => (c.classList.contains('c-sub') ? 'sub' : 'nosub'))
                    }))
                };
            };
            const sort = document.getElementById('sort');
            const pick = (value) => {
                sort.value = value;
                sort.dispatchEvent(new Event('change', { bubbles: true }));
            };
            const states = {};
            pick('keep3');
            states.keep = read();
            pick('price');
            states.price = read();
            pick('nosub3');
            states.nosub = read();
            pick('sub3');
            states.sub = read();
            pick('keep3');
            // The sort mark: one per sortable header, pale until its column is
            // the one ordering the list, then the direction it is going in.
            const marks = () => Array.from(document.querySelectorAll('#tbl thead th[data-sort]')).map((th) => {
                const si = th.querySelector('.si');
                return {
                    sort: th.getAttribute('aria-sort'),
                    has: !!si,
                    up: si ? getComputedStyle(si, '::before').opacity : '',
                    down: si ? getComputedStyle(si, '::after').opacity : ''
                };
            });
            states.unsorted = marks();
            pick('price');
            states.ascending = marks().find((m) => m.sort === 'ascending');
            document.querySelector('#tbl thead th[data-sort=price] button').click();
            states.descending = marks().find((m) => m.sort === 'descending');
            pick('keep3');
            return states;
        }"""
    )
    keep = state["keep"]
    if "3-year cost to keep recordings" not in keep["note"]:
        problems.append(f"the note under the sort control reads {keep['note']!r}")
    for row in keep["rows"]:
        if len(row["bold"]) != 1:
            problems.append(
                f"{row['id']} bolds {len(row['bold'])} cost cells at the default sort"
            )
        elif row["bold"][0] != row["basis"]:
            problems.append(
                f"{row['id']} bolds its {row['bold'][0]} figure but keeps records on the {row['basis']} one"
            )
    if state["price"]["note"] != "Order: price, low to high.":
        problems.append(f"the price sort note reads {state['price']['note']!r}")
    still = [r["id"] for r in state["price"]["rows"] if r["bold"]]
    if still:
        problems.append(f"{len(still)} rows keep a bold cost cell when sorting by price")
    for key, cell, words in (
        ("nosub", "nosub", "no plan"),
        ("sub", "sub", "with a plan"),
    ):
        wrong = [r["id"] for r in state[key]["rows"] if r["bold"] != [cell]]
        if wrong:
            problems.append(
                f"{len(wrong)} rows do not bold their {cell} figure when sorting by it"
            )
        if words not in state[key]["note"].lower():
            problems.append(f"the {cell} sort note reads {state[key]['note']!r}")
    marks = state["unsorted"]
    if len(marks) < 6:
        problems.append(f"{len(marks)} sortable headers, expected 6")
    if any(not mark["has"] for mark in marks):
        problems.append("a sortable header has no sort mark")
    # The default order is the computed 3-year cost, which is no column, so no
    # header claims a direction. A column that does claim one has to be the
    # column the list is sorted by.
    live = [mark for mark in marks if mark["sort"] != "none"]
    if live:
        problems.append(f"the default sort marks {[mark['sort'] for mark in marks]}")
    if not state["ascending"]:
        problems.append("sorting by price marks no header as ascending")
    quiet = [mark for mark in marks if mark["sort"] == "none" and mark["has"]]
    if any(mark["up"] != mark["down"] for mark in quiet):
        problems.append("an unsorted header leans one way instead of reading as one mark")
    if state["ascending"] and float(state["ascending"]["up"]) <= float(state["ascending"]["down"]):
        problems.append("the ascending mark does not lift its up half")
    if state["descending"] and float(state["descending"]["down"]) <= float(state["descending"]["up"]):
        problems.append("the descending mark does not lift its down half")
    return problems

def price_link_check(page):
    """Each price is the link to the page it came from.

    The intro promises that every price links to its source. A plain number
    under that promise is the one thing a reader checking a price cannot use,
    and the details name their sources by shop rather than by number.
    """
    problems = []
    state = page.evaluate(
        """() => {
            const rows = Array.from(document.querySelectorAll('#tbl tbody.item'));
            return {
                rows: rows.length,
                prices: rows.map((t) => {
                    const cell = t.querySelector('.c-price');
                    const a = cell.querySelector('a');
                    return {
                        id: t.id.slice(2),
                        text: (cell.textContent || '').trim(),
                        href: a ? a.getAttribute('href') : '',
                        rel: a ? (a.getAttribute('rel') || '') : '',
                        name: a ? (a.getAttribute('aria-label') || '') : '',
                        target: a ? (a.getAttribute('target') || '') : ''
                    };
                }),
                sourceNames: Array.from(document.querySelectorAll('#m-reo-poe .srcs a'))
                    .map((a) => a.textContent.trim())
            };
        }"""
    )
    if len(state["prices"]) < 2:
        return [f"found {len(state['prices'])} price cells to check"]
    unlinked = [p["id"] for p in state["prices"] if not p["href"].startswith("http")]
    if unlinked:
        problems.append(f"prices with no link to their source: {unlinked[:3]}")
    unpriced = [p["id"] for p in state["prices"] if "£" not in p["text"]]
    if unpriced:
        problems.append(f"price cells with no figure in them: {unpriced[:3]}")
    unnamed = [p["id"] for p in state["prices"] if " at " not in p["name"]]
    if unnamed:
        problems.append(f"price links without a shop in their name: {unnamed[:3]}")
    loose = [p["id"] for p in state["prices"]
             if "nofollow" not in p["rel"] or "noopener" not in p["rel"]]
    if loose:
        problems.append(f"price links without nofollow noopener: {loose[:3]}")
    numeric = [name for name in state["sourceNames"] if len(name) < 4 or name.isdigit()]
    if numeric:
        problems.append(f"the details name their sources by number: {numeric[:3]}")
    return problems

def details_check(page):
    """The details panel says each row in a sentence, and the two columns end level."""
    problems = []
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(150)
    page.evaluate(
        """() => {
            const b = document.querySelector('#m-reo-poe .more');
            if (b.getAttribute('aria-expanded') !== 'true') b.click();
        }"""
    )
    page.wait_for_timeout(200)
    state = page.evaluate(
        """() => {
            const panel = document.querySelector('#m-reo-poe tr.detail');
            const pairs = Array.from(panel.querySelectorAll('.dspec .pair'));
            const dl = panel.querySelector('.dspec');
            const left = (el) => Math.round(el.getBoundingClientRect().left);
            const value = (i) => (pairs[i] ? pairs[i].querySelector('dd').textContent.trim() : '');
            return {
                open: panel.classList.contains('open'),
                pairs: pairs.length,
                columns: Array.from(new Set(pairs.map(left))).sort((a, b) => a - b),
                stacked: pairs.slice(0, -1).map(left),
                foot: Math.round(pairs[pairs.length - 1].getBoundingClientRect().width),
                grid: Math.round(dl.getBoundingClientRect().width),
                sources: !!panel.querySelector('figure.dimg .srcs'),
                power: value(0),
                storage: value(2),
                labels: pairs.map((p) => p.querySelector('dt').textContent.trim())
            };
        }"""
    )
    if not state["open"]:
        problems.append("Details did not open")
    if state["pairs"] < 12:
        problems.append(f"the details panel lists {state['pairs']} rows, expected 13")
    if len(state["columns"]) != 2:
        problems.append(
            f"the details panel's pairs sit at {state['columns']}, expected two columns"
        )
    # Seven pairs on the left and six on the right left the two columns ending
    # 77px apart, so the longest pair (the score breakdown) takes the foot and
    # the twelve above it divide evenly.
    per_column = [state["stacked"].count(side) for side in state["columns"]]
    if per_column != [6, 6]:
        problems.append(f"the details panel's columns hold {per_column} pairs, expected 6 and 6")
    if state["grid"] - state["foot"] > 4:
        problems.append(
            f"the last pair is {state['foot']}px wide in a {state['grid']}px grid, "
            "not across the foot"
        )
    # The photo left 160px of blank grid under it; the sources fill it.
    if not state["sources"]:
        problems.append("the sources sit at the panel's foot, not under the photo")
    # A sentence rather than a data string: long, punctuated, and not a list of
    # terms joined by punctuation.
    for name, text in (("power", state["power"]), ("storage", state["storage"])):
        if len(text) < 40 or not text.rstrip().endswith("."):
            problems.append(f"the {name} line reads {text!r}")
        if " / " in text or ";" in text:
            problems.append(f"the {name} line is still a list of terms: {text!r}")
    for want in ("Power", "Storage", "Wi-Fi", "History without a plan"):
        if want not in state["labels"]:
            problems.append(f"the details panel has no {want!r} row")
    # Below the two-column layout the panel is one list, and the pair moved to
    # the foot has to go back to the end of it rather than land in the middle.
    page.set_viewport_size({"width": 900, "height": 900})
    page.wait_for_timeout(200)
    narrow = page.evaluate(
        """() => {
            const panel = document.querySelector('#m-reo-poe tr.detail');
            const more = document.querySelector('#m-reo-poe .more');
            if (more.getAttribute('aria-expanded') !== 'true') more.click();
            const pairs = Array.from(panel.querySelectorAll('.dspec .pair'));
            const tops = pairs.map((p) => Math.round(p.getBoundingClientRect().top));
            return {
                open: panel.classList.contains('open'),
                columns: Array.from(new Set(pairs.map((p) => Math.round(p.getBoundingClientRect().left)))).length,
                order: pairs.map((p) => p.querySelector('dt').textContent.trim()),
                stacked: tops.every((top, i) => i === 0 || top >= tops[i - 1]),
                last: pairs[pairs.length - 1].querySelector('dt').textContent.trim()
            };
        }"""
    )
    if not narrow["open"]:
        problems.append("the details panel did not open at 900px")
    if narrow["columns"] != 1:
        problems.append(f"the details panel's pairs sit in {narrow['columns']} columns at 900px")
    if not narrow["stacked"] or narrow["last"] != "Score breakdown":
        problems.append(
            f"the details panel's rows are out of order at 900px: {narrow['order']}"
        )
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(150)
    page.evaluate(
        """() => {
            const b = document.querySelector('#m-reo-poe .more');
            if (b.getAttribute('aria-expanded') === 'true') b.click();
        }"""
    )
    page.wait_for_timeout(120)
    return problems

PRINT_STATE = """() => {
    const row = document.querySelector('#tbl tbody.item tr.main');
    const left = (el) => Math.round(el.getBoundingClientRect().left);
    const shown = (el) => getComputedStyle(el).display !== 'none';
    const headings = Array.from(document.querySelectorAll('#tbl thead th')).filter(shown);
    const values = Array.from(row.children).filter(shown);
    const th = document.querySelector('#tbl thead th.c-cmp');
    const td = row.querySelector('td.c-cmp');
    return {
        headings: headings.map(left),
        values: values.map(left),
        box: [th, td].map((el) => (el ? getComputedStyle(el).display : 'missing')),
        badge: getComputedStyle(document.querySelector('.zi')).display,
        marks: getComputedStyle(document.querySelector('#tbl thead th .si')).display,
        chevron: getComputedStyle(document.querySelector('.more-w')).display
    };
}"""

def print_check(page):
    """On paper each figure sits under its own heading.

    Printing drops the compare box. A grid cell that is hidden leaves its
    track behind, so the seven cells that remain start one track left of where
    the seven remaining headings start, and every value prints under the
    heading of the column before it. The page is also narrower on paper than
    on screen, so this is measured at 1123px: A4 landscape, the width at which
    the numbered columns are laid out as columns at all.
    """
    problems = []
    page.set_viewport_size({"width": 1123, "height": 900})
    page.emulate_media(media="print")
    try:
        page.wait_for_timeout(200)
        # Switching to print re-lays the page out, and the first read after the
        # switch can still describe the screen layout: it reported the first
        # cell one compare-track right of where the printed page puts it. Read
        # until two reads agree, then judge the layout that settled.
        state = page.evaluate(PRINT_STATE)
        for _ in range(4):
            page.wait_for_timeout(80)
            settled = page.evaluate(PRINT_STATE)
            if settled == state:
                break
            state = settled
    finally:
        page.emulate_media(media="screen")
        page.set_viewport_size({"width": 1280, "height": 900})
        page.wait_for_timeout(150)
    if state["box"] != ["none", "none"]:
        problems.append(f"the compare column prints as {state['box']}")
    if len(state["headings"]) != len(state["values"]):
        problems.append(
            f"{len(state['headings'])} headings print over {len(state['values'])} cells"
        )
    else:
        shifted = [
            heading
            for heading, value in zip(state["headings"], state["values"])
            if abs(heading - value) > 1
        ]
        if shifted:
            problems.append(
                f"printed cells start at {state['values']}, headings at {state['headings']}"
            )
    if state["badge"] != "none":
        problems.append("the photo's magnifier badge prints beside every photo")
    if state["marks"] != "none":
        problems.append("the sort marks print beside every heading")
    if state["chevron"] != "none":
        problems.append("the row's chevron prints where there is nothing to open")
    return problems

def jump_check(page):
    """A jump announces its model, verdict and position, then clears."""
    problems = []
    page.click(".verdict a.jump[data-ids='tapo-d230']")
    page.wait_for_timeout(700)
    state = page.evaluate(
        """() => ({ live: document.getElementById('live').textContent,
                     active: document.activeElement.className }) """
    )
    expected = "TP-Link Tapo D230S1, easiest battery setup, row 4 of 14"
    if state["live"] != expected:
        problems.append(f"the jump announced {state['live']!r}, expected {expected!r}")
    if "cmp" not in state["active"]:
        problems.append(f"focus after the jump is on {state['active']!r}")
    page.wait_for_timeout(4200)
    cleared = page.evaluate("() => document.getElementById('live').textContent")
    if cleared:
        problems.append(f"the jump announcement is not cleared: {cleared!r}")
    return problems

def motion_check(page):
    """The theme disc turns and the page fades, unless reduced motion is set."""
    problems = []

    def read():
        return page.evaluate(
            """() => ({
                disc: getComputedStyle(document.querySelector('#theme i')).transform,
                discT: getComputedStyle(document.querySelector('#theme i')).transitionDuration,
                bodyT: getComputedStyle(document.body).transitionDuration,
                theme: document.documentElement.getAttribute('data-theme')
            })"""
        )

    dark = read()
    page.click("#theme")
    page.wait_for_timeout(250)
    light = read()
    if dark["disc"] == light["disc"]:
        problems.append(f"the disc does not turn between themes: {dark['disc']}")
    if "0.18s" not in dark["discT"] or "0.18s" not in dark["bodyT"]:
        problems.append(
            f"theme transitions are disc {dark['discT']!r}, body {dark['bodyT']!r}"
        )
    page.emulate_media(reduced_motion="reduce")
    page.wait_for_timeout(50)
    reduced = read()
    if reduced["discT"] != "0s" or reduced["bodyT"] != "0s":
        problems.append(
            f"reduced motion still animates: disc {reduced['discT']!r}, body {reduced['bodyT']!r}"
        )
    page.click("#theme")
    page.wait_for_timeout(50)
    page.emulate_media(reduced_motion="no-preference")
    return problems

def bars_check(page, row_count):
    """Score bars are painted once at their score and never redrawn on a sort."""
    problems = []
    page.wait_for_timeout(800)
    initial = page.evaluate(BARS_JS)
    if initial["n"] != row_count:
        problems.append(f"{initial['n']} score bars are visible, expected {row_count}")
    if initial["transition"] != "0s":
        problems.append(
            f"the score bar still transitions {initial['property']} over {initial['transition']!r}"
        )
    off = [(a, b) for a, b in zip(initial["scales"], initial["targets"]) if abs(a - b) > 0.01]
    if off:
        problems.append(f"a bar is scaled {off[0][0]:.2f}, not its score {off[0][1]:.2f}")

    # A sort must not touch them: no zero phase, no timers, no redraw. Keyed by
    # row, because the sort reorders the DOM under the selector.
    before = page.evaluate(
        """() => Object.fromEntries(Array.from(document.querySelectorAll('#tbl tbody.item .bar i'))
            .map((b) => [b.closest('tbody.item').id, b.style.transform]))"""
    )
    painted = page.evaluate(
        """() => {
            const sel = document.getElementById('sort');
            sel.value = 'price';
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            return Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'))
                .map((b) => getComputedStyle(b).transform);
        }"""
    )
    page.wait_for_timeout(400)
    after = page.evaluate(
        """() => Object.fromEntries(Array.from(document.querySelectorAll('#tbl tbody.item .bar i'))
            .map((b) => [b.closest('tbody.item').id, b.style.transform]))"""
    )
    moved = [k for k in before if before[k] != after.get(k)]
    if moved:
        problems.append(f"a sort rewrites the bar transforms on {len(moved)} rows")
    if not painted or not all(t.startswith("matrix") for t in painted):
        problems.append(f"a bar has no computed transform after the sort: {painted[:2]}")

    page.emulate_media(reduced_motion="reduce")
    page.wait_for_timeout(80)
    reduced = page.evaluate(BARS_JS)
    off = [(a, b) for a, b in zip(reduced["scales"], reduced["targets"]) if abs(a - b) > 0.01]
    if off:
        problems.append(f"reduced motion shows a bar at {off[0][0]:.2f}, not {off[0][1]:.2f}")
    page.emulate_media(reduced_motion="no-preference")
    return problems

def contain_check(page, row_count):
    """Off-screen phone cards skip layout, with an intrinsic size to stand in."""
    problems = []
    got = page.evaluate(
        """() => {
            const card = document.querySelector('#tbl tbody.item');
            const cs = getComputedStyle(card);
            const cards = Array.from(document.querySelectorAll('#tbl tbody.item'));
            return { visibility: cs.contentVisibility,
                     size: cs.containIntrinsicSize,
                     n: cards.length,
                     hidden: cards.filter((c) => c.hidden).length };
        }"""
    )
    if got["visibility"] != "auto":
        problems.append(f"a phone card's content-visibility is {got['visibility']!r}, expected auto")
    if got["size"] != "auto 445px":
        problems.append(f"the phone card's intrinsic size is {got['size']!r}, expected 'auto 445px'")
    if got["n"] != row_count or got["hidden"]:
        problems.append(
            f"{got['n']} cards with {got['hidden']} hidden, expected {row_count} shown"
        )
    return problems

def desktop_rows_check(page, row_count):
    """At desktop widths a row is a contained grid track, and its columns line up.

    The table's own column widths cannot survive a sort cheaply, so the rows are
    grid tracks with the widths the table chose; a mistyped track silently
    squeezes a column or breaks the row rule, which nothing else catches.

    Below 901px the catch leaves the tracks. Eight columns there leave it 68px
    at 821, where its words paint under the chevron and a row grows to 394px; it
    becomes a band from the model column to the table's edge, captioned by its
    own cell, and the model column takes the width the band freed.
    """
    def judge(width, got, fallback):
        where = f"{width}px{fallback}"
        found = []
        band = width <= 900
        tracks = 7 if band else 8
        if got["display"] != "grid" or got["tracks"] != tracks:
            found.append(
                f"at {where} a row is {got['display']!r} with {got['tracks']} tracks, "
                f"expected a grid of {tracks}"
            )
        if got["cardDisplay"] != "block":
            found.append(f"at {where} a row group is {got['cardDisplay']!r}, expected block")
        if got["visibility"] != "auto" or not got["size"].startswith("auto "):
            found.append(
                f"at {where} the rows are not contained: {got['visibility']!r} {got['size']!r}"
            )
        if len(got["rows"]) != row_count:
            found.append(f"at {where} {len(got['rows'])} of {row_count} rows are showing")
            return found
        heads = [th for th in got["head"] if th["width"] > 2]
        if len(heads) != tracks:
            found.append(f"at {where} {len(heads)} header cells are showing, expected {tracks}")
        if heads:
            skew = max(
                abs(left - head["left"])
                for row in got["rows"]
                for left, head in zip(row["lefts"], heads)
            )
            if skew > 1:
                found.append(f"at {where} a row's columns sit {skew:.0f}px off the header's")
        # The header's rule is drawn cell by cell, so a cell that stops short of
        # its track leaves a hole in the line. The compare box painted 40px into
        # a 42px track and every rule under the header was broken by 2px.
        if heads:
            gaps = [
                (i, nxt["left"] - (th["left"] + th["width"]))
                for i, (th, nxt) in enumerate(zip(heads, heads[1:]))
                if nxt["left"] - (th["left"] + th["width"]) > 0.6
            ]
            if gaps:
                found.append(
                    f"at {where} the header rule has a {gaps[0][1]:.0f}px hole after "
                    f"column {gaps[0][0]}"
                )
            if not band and abs(heads[-1]["left"] + heads[-1]["width"] - got["right"]) > 0.6:
                found.append(f"at {where} the header's last cell stops short of the table edge")
        # The catch is the one cell with a sentence in it, and the button that
        # opens its costs sits on the line below the words, not beside them: a
        # word wider than a narrow column paints across the button without the
        # box reporting it. A word the font makes wider than the box leaves the
        # box itself unbroken, so both the words' end and the box are measured.
        over = [
            (row["id"], row["catch"]["textBottom"] - row["catch"]["moreTop"] - 2)
            for row in got["rows"]
        ]
        over = [item for item in over if item[1] > 0]
        if over:
            found.append(
                f"at {where} the catch in {over[0][0]} runs {over[0][1]:.0f}px "
                "into its button"
            )
        outside = [
            (row["id"], row["catch"]["textRight"] - row["catch"]["textBoxRight"])
            for row in got["rows"]
        ]
        outside = [item for item in outside if item[1] > 0.5]
        if outside:
            found.append(
                f"at {where} a word in the catch of {outside[0][0]} is "
                f"{outside[0][1]:.0f}px wider than its text box"
            )
        # A record label is a bulleted phrase, and its lines lose 1rem to the
        # hanging indent, so the track's width decides whether it reads as
        # words or one word a line: 92px gave "Only with extra kit" a line
        # each, 118px gives it two, here and under a fallback 15% wider.
        # From 1200 the catch pays for that width without a row growing; below
        # 1200 the same 28px comes out of the catch's own rows, so the track
        # stays at 90 and the labels take four lines.
        rec = got["rows"][0]["recW"]
        if width >= 1200 and rec < 118:
            found.append(
                f"at {where} the record track is {rec}px, under the 118 its "
                "two-word lines need"
            )
        if width < 1200 and rec >= 118:
            found.append(
                f"at {where} the record track is {rec}px, wider than the 90 the "
                "catch's rows can pay for below 1200"
            )
        # A footnote number belongs to the sentence it cites. Left outside the
        # label's block it has no room after a wrapped label's last line, so it
        # drops to a new line at the hanging indent and reads as a note on the
        # cell instead. Both halves of that are the defect: back at the indent,
        # or below the label's own box.
        loose = [
            f"{row['id']} at {row['mark']['left']},{row['mark']['top']} "
            f"against the label box {row['mark']['recLeft']},{row['mark']['recBottom']}"
            for row in got["rows"]
            if row["mark"]["left"] <= row["mark"]["recLeft"] + 1
            or row["mark"]["top"] > row["mark"]["recBottom"] - 4
        ]
        if loose:
            found.append(
                f"at {where} a record footnote is not on its label's last line: {loose[0]}"
            )
        if band:
            if len(heads) == tracks:
                for row in got["rows"]:
                    catch = row["catch"]
                    if abs(catch["left"] - heads[1]["left"]) > 1 or abs(catch["right"] - got["right"]) > 1:
                        found.append(
                            f"at {where} the catch band in {row['id']} does not run from "
                            "the model column to the table edge"
                        )
                        break
                    if catch["top"] < max(row["bottoms"][:tracks]) - 1:
                        found.append(
                            f"at {where} the catch band in {row['id']} is not below the figures"
                        )
                        break
                    if "Main catch" not in catch["caption"]:
                        found.append(
                            f"at {where} the catch band in {row['id']} is uncaptioned: "
                            f"{catch['caption']!r}"
                        )
                        break
                    if catch["textLines"] > 3:
                        found.append(
                            f"at {where} the catch in {row['id']} still reads in "
                            f"{catch['textLines']} lines"
                        )
                        break
        else:
            ragged = [row["id"] for row in got["rows"] if max(row["heights"]) - min(row["heights"]) > 1]
            if ragged:
                found.append(f"at {where} the row rule breaks in {ragged[0]}")
            if got["rows"][0]["catch"]["caption"] != "none":
                found.append(
                    f"at {where} the catch column repeats its own caption: "
                    f"{got['rows'][0]['catch']['caption']!r}"
                )
        if got["clipped"]:
            found.append(f"at {where} a cell clips its text: {got['clipped'][0]}")
        if got["overflow"] > 1:
            found.append(f"at {where} the table overflows by {got['overflow']}px")
        return found

    def read_at(width):
        page.set_viewport_size({"width": width, "height": 900})
        page.wait_for_timeout(120)
        return page.evaluate(DESKTOP_ROWS_JS)

    problems = []
    # The panels are hidden by a class rather than the `hidden` attribute, so
    # the desktop rule that shows an open one (`.main-t tr.detail`) has to be
    # beaten on load. It was not: every panel printed open at 821 and wider,
    # which doubled the page and left nothing to open.
    shut = page.evaluate(
        """() => ({
            shown: Array.from(document.querySelectorAll('#tbl tr.detail'))
                .filter((row) => row.getBoundingClientRect().height > 0).length,
            expanded: Array.from(document.querySelectorAll('button.more'))
                .filter((b) => b.getAttribute('aria-expanded') === 'true').length
        })"""
    )
    if shut["shown"] or shut["expanded"]:
        problems.append(
            f"the page loads with {shut['shown']} of the costs-and-sources panels "
            f"open and {shut['expanded']} buttons expanded"
        )
    widths = (1440, 1280, 1200, 1199, 1101, 1100, 1000, 901, 900, 821)
    for width in widths:
        problems += judge(width, read_at(width), "")
    # The tracks are fixed pixels, so a wide fallback font moves words with no
    # box changing: at 821 the catch once painted 51px under its chevron with
    # every cell reporting fit. Every width is measured again at Verdana, about
    # 15% wider than Arial, so a font this machine has and CI's does not cannot
    # hide a break the other sees.
    page.evaluate(
        "() => document.documentElement.style.setProperty('--sans', 'Verdana, DejaVu Sans, sans-serif')"
    )
    page.wait_for_timeout(150)
    for width in widths:
        problems += judge(width, read_at(width), " under the wider fallback")
    page.evaluate("() => document.documentElement.style.removeProperty('--sans')")
    page.wait_for_timeout(150)
    # A sticky cell cannot outrun its parent, so the header row has to stick as
    # a block here; sticking the cells leaves the table header behind on scroll.
    page.evaluate("document.getElementById('tbl').scrollIntoView()")
    page.mouse.wheel(0, 900)
    page.wait_for_timeout(300)
    stuck = page.evaluate(STUCK_JS)
    if stuck["top"] != 0 or not stuck["covers"]:
        problems.append(f"the header leaves the top of the page when the table scrolls: {stuck}")
    page.evaluate("window.scrollTo(0, 0)")

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(160)
    cards = page.evaluate(DESKTOP_ROWS_JS)
    # A phone card is three tracks: the compare box, then two columns of
    # figures. The two 3-year costs share a row, so a card is a third shorter
    # than it was when each figure had a line of its own.
    if cards["tracks"] != 3:
        problems.append(f"at 390px a row has {cards['tracks']} tracks, expected the 3-track card")
    for row in cards["rows"]:
        if abs(row["pair"]["ny"] - row["pair"]["sy"]) > 2 or row["pair"]["nx"] == row["pair"]["sx"]:
            problems.append(f"at 390px the two 3-year figures in {row['id']} are not side by side")
            break
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(120)
    return problems

def hit_check(page):
    """The row's button names the panel it opens, and is a 44px target.

    The trust layer used to open from a bare chevron: a 24px icon with a hidden
    name, two clicks deep, and the details themselves were gone without
    JavaScript. The button says what is behind it now, and the panel is hidden
    by a class rather than the `hidden` attribute, so the no-JS reader keeps
    every panel open. This measures the name, the target and the class.
    """
    problems = []
    button = page.locator("button.more").first
    button.scroll_into_view_if_needed()
    box = button.bounding_box()
    if not box:
        return ["no visible row toggle"]
    shape = page.evaluate(
        """() => {
            const b = document.querySelector('button.more');
            return {
                width: Math.round(b.getBoundingClientRect().width),
                height: Math.round(b.getBoundingClientRect().height),
                text: (b.textContent || '').replace(/\\s+/g, ' ').trim(),
                turn: getComputedStyle(b, '::before').transform
            };
        }"""
    )
    if shape["text"].lower() != "costs & sources":
        problems.append(f"the row toggle reads {shape['text']!r}, expected 'Costs & sources'")
    if shape["width"] < 44 or shape["height"] < 44:
        problems.append(f"the row toggle is {shape['width']}x{shape['height']}px, expected 44x44")
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(150)
    if button.get_attribute("aria-expanded") != "true":
        problems.append("a click on the row toggle does not open the row")
    opened = page.evaluate(
        """() => {
            const b = document.querySelector('button.more');
            const panel = document.getElementById(b.getAttribute('aria-controls'));
            return {
                turn: getComputedStyle(b, '::before').transform,
                open: !!panel && panel.classList.contains('open')
            };
        }"""
    )
    if opened["turn"] == shape["turn"]:
        problems.append("the chevron does not turn when the row opens")
    if not opened["open"]:
        problems.append("the row's panel does not take the open class")
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(80)
    return problems

def theme_check(page):
    """The toggle names its action, carries no pressed state, and is its own 44px target."""
    problems = []
    state = page.evaluate(
        """() => {
            const b = document.getElementById("theme");
            return { pressed: b.getAttribute("aria-pressed"),
                     label: b.getAttribute("aria-label"), text: b.textContent.trim() };
        }"""
    )
    if state["pressed"] is not None:
        problems.append(f"the theme button still claims aria-pressed={state['pressed']}")
    if not (state["label"] or "").startswith("Switch to "):
        problems.append(f"the theme button is named {state['label']!r}")
    # White photo tiles glare against the near-black page, so dark mode dims the
    # tile behind each photo as well as the photo itself.
    was = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
    page.evaluate("() => document.documentElement.setAttribute('data-theme', 'dark')")
    page.wait_for_timeout(120)
    tile = page.evaluate(
        """() => {
            const el = document.querySelector('.ph');
            return el ? getComputedStyle(el).backgroundColor : '';
        }"""
    )
    page.evaluate(
        """(was) => {
            if (was === null) document.documentElement.removeAttribute('data-theme');
            else document.documentElement.setAttribute('data-theme', was);
        }""",
        was,
    )
    numbers = [int(part) for part in tile.replace("rgb(", "").replace(")", "").replace(" ", "").split(",") if part.isdigit()]
    if len(numbers) < 3 or max(numbers[:3]) > 90:
        problems.append(f"the photo tile in dark mode is {tile!r}, expected a dim tile")
    # The button is its own target: 44px tall, so no pseudo-element has to
    # extend it, and a click on its last rows of pixels still lands on it.
    before = state["text"]
    toggle = page.locator("#theme")
    toggle.scroll_into_view_if_needed()
    box = toggle.bounding_box()
    if not box:
        problems.append("the theme button has no box")
    else:
        if round(box["height"]) < 44:
            problems.append(
                f"the theme button is {round(box['height'])}px tall, not the 44px it is meant to be"
            )
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] - 4)
        page.wait_for_timeout(150)
        after = toggle.inner_text().strip()
        if after == before:
            problems.append("a click on the theme button's lower edge does nothing")
        else:
            box = page.locator("#theme").bounding_box()
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] - 4)
            page.wait_for_timeout(150)
    return problems

def price_check(page):
    """Open the filters and exercise the two-handle price slider."""
    problems = []
    shapes = page.evaluate(
        """() => {
            const ranges = Array.from(document.querySelectorAll("#controls input[type=range]"));
            return {
                count: ranges.length,
                labels: ranges.map((el) => el.getAttribute("aria-label") || ""),
                values: ranges.map((el) => el.value),
                bounds: ranges.map((el) => [el.min, el.max]),
                outputs: [
                    document.getElementById("f-min-out").textContent,
                    document.getElementById("f-max-out").textContent
                ],
                extra: (() => {
                    const box = document.querySelector(".range").cloneNode(true);
                    box.querySelectorAll(".lab, .dual, output").forEach((n) => n.remove());
                    return (box.textContent || "").replace(/\s+/g, " ").trim();
                })()
            };
        }"""
    )
    if shapes["count"] != 2:
        return [f"expected two price handles, found {shapes['count']}"]
    if not all(shapes["labels"]):
        problems.append(f"price handles need labels, got {shapes['labels']}")
    if shapes["bounds"][0] != shapes["bounds"][1]:
        problems.append(f"price handles use different bounds: {shapes['bounds']}")
    if shapes["outputs"] != ["£" + v for v in shapes["values"]]:
        problems.append(
            f"the labels read {shapes['outputs']} for handles at {shapes['values']}"
        )
    # The two labels under the slider already print the range, so the column
    # prints no third copy of the figures.
    if shapes["extra"]:
        problems.append(f"the price column repeats its range: {shapes['extra']!r}")

    page.eval_on_selector("#filters", "el => { el.open = true }")
    page.wait_for_timeout(80)
    full = page.evaluate(
        """() => {
            const body = document.querySelector("#filters .fbody");
            const cs = getComputedStyle(body);
            const content = body.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
            return {
                column: Math.round(content),
                slider: Math.round(document.querySelector(".dual").getBoundingClientRect().width)
            };
        }"""
    )
    if full["slider"] < full["column"] - 4:
        problems.append(
            f"the price slider is {full['slider']}px wide in a {full['column']}px column"
        )

    page.eval_on_selector(
        "#f-min",
        "el => { el.value = 200; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.wait_for_timeout(80)
    filtered = page.evaluate(
        """() => {
            const rows = Array.from(document.querySelectorAll("tbody.item"));
            const shown = rows.filter((r) => !r.hidden);
            return {
                shown: shown.length,
                total: rows.length,
                cheapest: Math.min(...shown.map((r) => Number(r.dataset.price)))
            };
        }"""
    )
    if filtered["shown"] >= filtered["total"] or filtered["cheapest"] < 200:
        problems.append(
            f"the lower handle does not filter: {filtered['shown']} of "
            f"{filtered['total']} rows shown, cheapest £{filtered['cheapest']}"
        )
    moved = page.evaluate(
        "() => [document.getElementById('f-min-out').textContent, "
        "document.getElementById('f-max-out').textContent]"
    )
    if moved[0] != "£200":
        problems.append(f"the low label does not follow its handle: {moved!r}")

    page.eval_on_selector(
        "#f-max",
        "el => { el.value = 40; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.eval_on_selector(
        "#f-min",
        "el => { el.value = 300; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.wait_for_timeout(80)
    crossed = page.evaluate(
        "() => [Number(document.getElementById('f-min').value), "
        "Number(document.getElementById('f-max').value)]"
    )
    if crossed[0] > crossed[1]:
        problems.append(f"the handles crossed: lowest {crossed[0]} above highest {crossed[1]}")

    page.eval_on_selector(
        "#f-max",
        "el => { el.value = 150; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.eval_on_selector(
        "#f-min",
        "el => { el.value = 100; el.dispatchEvent(new Event('input', { bubbles: true })) }",
    )
    page.wait_for_timeout(80)
    edges = page.evaluate(
        """() => {
            const dual = document.querySelector(".dual");
            const track = document.querySelector(".dual-track");
            const fill = document.querySelector("#f-fill");
            const low = document.getElementById("f-min");
            const high = document.getElementById("f-max");
            const db = dual.getBoundingClientRect();
            const tb = track.getBoundingClientRect();
            const fb = fill.getBoundingClientRect();
            const min = Number(low.min), max = Number(low.max);
            const thumb = parseFloat(getComputedStyle(dual).getPropertyValue("--thumb")) || 0;
            const centre = (v) => db.x + thumb / 2 + ((v - min) / (max - min)) * (db.width - thumb);
            return {
                fill: [fb.x - db.x, db.right - fb.right],
                want: [centre(Number(low.value)) - db.x, db.right - centre(Number(high.value))],
                track: [tb.x - db.x, db.right - tb.right]
            };
        }"""
    )
    if (
        abs(edges["fill"][0] - edges["want"][0]) > 1.5
        or abs(edges["fill"][1] - edges["want"][1]) > 1.5
    ):
        problems.append(
            f"the filled span {[round(v) for v in edges['fill']]} does not meet the "
            f"handles at {[round(v) for v in edges['want']]}"
        )

    page.click("#reset")
    page.wait_for_timeout(80)

    # Clicking the bare track is a shortcut for the nearer handle.
    track = page.locator(".dual-track")
    box = track.bounding_box()
    if not box or not box["width"]:
        return problems + ["the price track has no width to click on"]
    values = "() => [Number(document.getElementById('f-min').value), Number(document.getElementById('f-max').value)]"
    # Playwright's hit-target check sees the transparent range input at this
    # point even though it has pointer-events:none; a real mouse click is the
    # behaviour under test.
    page.mouse.click(box["x"] + box["width"] * 0.25, box["y"] + 1)
    page.wait_for_timeout(80)
    low = page.evaluate(values)
    if abs(low[0] - 105) > 5 or low[1] != 300:
        problems.append(
            f"a click a quarter along the track left the handles at {low}, "
            "expected the lower one near 105"
        )
    page.mouse.click(box["x"] + box["width"] * 0.75, box["y"] + 1)
    page.wait_for_timeout(80)
    high = page.evaluate(values)
    if abs(high[1] - 235) > 5 or high[0] != low[0]:
        problems.append(
            f"a click three quarters along the track left the handles at {high}, "
            "expected the upper one near 235"
        )

    # A range dragged shut still has to open by the pointer: with both handles
    # on one price, a click to their right moves the maximum and a click to
    # their left moves the minimum. The nearest-handle rule alone left both at
    # the minimum, so the maximum could not be raised at all.
    for handle in ("#f-min", "#f-max"):
        page.eval_on_selector(
            handle,
            "el => { el.value = 60; el.dispatchEvent(new Event('input', { bubbles: true })) }",
        )
    page.wait_for_timeout(80)
    page.mouse.click(box["x"] + box["width"] * 0.9, box["y"] + 1)
    page.wait_for_timeout(80)
    shut = page.evaluate(values)
    if shut[0] != 60 or shut[1] <= 60:
        problems.append(
            f"a click right of two handles at \u00a360 left the range at {shut}, "
            "expected the maximum to move"
        )

    page.click("#reset")
    page.wait_for_timeout(80)
    restored = page.evaluate(
        "() => Array.from(document.querySelectorAll('tbody.item')).filter((r) => !r.hidden).length"
    )
    if restored != filtered["total"]:
        problems.append(f"Reset left {restored} of {filtered['total']} rows showing")
    return problems

def skip_check(page):
    """Tab to the skip link, press Enter, and confirm focus lands on the table."""
    problems = []
    links = page.evaluate(
        "() => Array.from(document.querySelectorAll('a.skip')).map(a => a.getAttribute('href'))"
    )
    if links != ["#tbl"]:
        return [f"expected one skip link to #tbl, found {links or 'none'}"]
    if not page.evaluate("() => document.getElementById('tbl').tabIndex === -1"):
        problems.append("the skip link target is not focusable")
    page.keyboard.press("Tab")
    first = page.evaluate(
        """() => ({
            cls: document.activeElement.className,
            top: Math.round(document.activeElement.getBoundingClientRect().top),
            transform: getComputedStyle(document.activeElement).transform
        })"""
    )
    if "skip" not in first["cls"]:
        problems.append(f"the first Tab stop is {first['cls'] or 'nothing'}, not the skip link")
    elif first["transform"] != "none" or first["top"] < 0:
        problems.append(
            f"the skip link stays off-screen when focused (top {first['top']}px, "
            f"transform {first['transform']})"
        )
    page.keyboard.press("Enter")
    page.wait_for_timeout(150)
    landed = page.evaluate(
        "() => ({hash: location.hash, focus: (document.activeElement || {}).id || ''})"
    )
    if landed["hash"] != "#tbl" or landed["focus"] != "tbl":
        problems.append(
            f"Enter moved to {landed['hash'] or 'nowhere'} with focus on "
            f"{landed['focus'] or 'nothing'}"
        )
    return problems

CHECKS = [
    Check(
        "filter panel", "phone", 13,
        "the phone filter panel reopens when the window grows past 520px",
        lambda ctx: filters_check(ctx.page),
    ),
    Check(
        "price slider", "phone", 14,
        "the price slider is one labelled handle per end, fills to the handles, and filters",
        lambda ctx: price_check(ctx.page),
    ),
    Check(
        "compare cap", "phone", 15,
        "the 3-row cap is explained and announced; Compare sits by the count",
        lambda ctx: copy_check(ctx.page),
    ),
    Check(
        "labels", "phone", 16,
        "Nest names its 3-hour limit, no-plan reads as words, PoE is defined at the filter",
        lambda ctx: labels_check(
            ctx.page, ctx.dataset.REC_LABEL["brief"] if ctx.dataset else None
        ),
    ),
    Check(
        "closing line", "phone", 17,
        "the page ends on one line with the date, an issue link and a way back",
        lambda ctx: footer_check(ctx.page, ctx.checked),
    ),
    Check(
        "empty result", "phone", 18,
        "filtering announces its count; an empty result offers the nearest match",
        lambda ctx: recovery_check(ctx.page),
    ),
    Check(
        "score bars", "phone", 19,
        "score bars are painted at their score and a sort never redraws them",
        lambda ctx: bars_check(ctx.page, ctx.row_count),
    ),
    Check(
        "source card", "compare", 89,
        "every figure opens its own source card, carrying the page, the row's own sentence for that figure, the sum and the day it was checked, and the comparison's figures open the table's own card",
        lambda ctx: card_check(ctx.page, ctx.dataset, ctx.checked),
    ),
    Check(
        "source list", "compare", 72,
        "the numbered sources sit beside the working in 1 to 4 lists by width, under the copy's 80ch measure, closed on a phone",
        lambda ctx: sources_check(ctx.page, ctx.source_count),
    ),
    Check(
        "compare header at 390", "phone", 22,
        "the compare heading stays on one line and its links in one row",
        lambda ctx: head_check(ctx.page),
    ),
    Check(
        "skip link", "desktop", 30,
        "the skip link is the first Tab stop and Enter lands on the table",
        lambda ctx: skip_check(ctx.page),
    ),
    Check(
        "details hit area", "desktop", 31,
        "a button that names the costs and sources opens the row, takes a 44px target, and hides a class rather than the row",
        lambda ctx: hit_check(ctx.page),
    ),
    Check(
        "theme toggle", "desktop", 32,
        "the theme toggle names its action and is its own 44px target",
        lambda ctx: theme_check(ctx.page),
    ),
    Check(
        "theme motion", "desktop", 34,
        "the theme disc turns and the page fades over 180ms, off under reduced motion",
        lambda ctx: motion_check(ctx.page),
    ),
    Check(
        "jump announcement", "desktop", 35,
        "a jump announces its model, verdict and row, then clears",
        lambda ctx: jump_check(ctx.page),
    ),
    Check(
        "desktop rows", "desktop", 36,
        "desktop rows are contained grid tracks: columns line up with the header, no cell clips or paints under its chevron, 821 to 1440px, and the catch takes the row below 901px",
        lambda ctx: desktop_rows_check(ctx.page, ctx.row_count),
    ),
    Check(
        "scroll rule", "desktop", 38,
        "a hairline along the table follows scroll, with a plain rule where timelines are missing",
        lambda ctx: rule_check(ctx.page, ctx.row_count),
    ),
    Check(
        "compare header at 1280", "desktop", 39,
        "the compare heading stays on one line and its links in one row at 1280",
        lambda ctx: head_check(ctx.page),
    ),
    Check(
        "sort figure", "compare", 48,
        "the note names the figure, each row bolds the cell the order uses, and every sortable header shows its direction",
        lambda ctx: sort_figure_check(ctx.page),
    ),
    Check(
        "price links", "compare", 49,
        "every price opens the page it came from, and the details name their sources by shop",
        lambda ctx: price_link_check(ctx.page),
    ),
    Check(
        "details panel", "compare", 51,
        "a details panel says power and storage in sentences, six pairs a column with the score across the foot and the sources under the photo",
        lambda ctx: details_check(ctx.page),
    ),
    Check(
        "print", "compare", 53,
        "on paper each figure prints under its own heading, with no compare box",
        lambda ctx: print_check(ctx.page),
    ),
    Check(
        "photo lightbox", "compare", 76,
        lambda ctx: f"{ctx.lightbox['buttons']} photos open in the lightbox, named, "
        "sized from the large file, and Esc closes it",
        lambda ctx: ctx.lightbox["problems"],
    ),
]

