"""The JavaScript each probe runs in the page."""


AUDIT_JS = r"""() => {
  const all = (s) => Array.from(document.querySelectorAll(s));
  const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
  const name = (el) => {
    const aria = (el.getAttribute("aria-label") || "").trim();
    if (aria) return aria;
    if (el.labels && el.labels.length) return Array.from(el.labels).map(text).join(" ").trim();
    if (el.tagName === "INPUT" && (el.type === "submit" || el.type === "button")) return (el.value || "").trim();
    const own = text(el) || (el.getAttribute("title") || "").trim();
    if (own) return own;
    const img = el.querySelector("img[alt]");
    return img ? img.alt.trim() : "";
  };
  const box = (el) => el.getBoundingClientRect();
  const ids = all("[id]").map((el) => el.id);
  const anchors = all("a[href]").map((a) => ({ href: a.getAttribute("href"), text: name(a) }));
  const internal = anchors.filter((a) => a.href.startsWith("#") && a.href.length > 1);
  const external = anchors.filter((a) => /^https?:\/\//.test(a.href));
  return {
    lang: document.documentElement.lang,
    title: document.title,
    viewport: !!document.querySelector('meta[name="viewport"]'),
    mains: all("main").length,
    rows: all("tbody.item").length,
    duplicateIds: ids.filter((id, i) => ids.indexOf(id) !== i),
    brokenAnchors: internal.filter((a) => !document.getElementById(a.href.slice(1))).map((a) => a.href),
    emptyLinks: anchors.filter((a) => !a.text).map((a) => a.href),
    images: all("img").map((img) => ({ src: img.getAttribute("src") || "", alt: img.getAttribute("alt"), inRowHeader: !!img.closest("th[scope=row]") })),
    localRefs: all("img[src]").map((img) => img.getAttribute("src")),
    controls: all("input, select, textarea").map((el) => ({
      tag: el.tagName.toLowerCase(), type: el.type || "", name: name(el),
      width: Math.round(box(el).width), height: Math.round(box(el).height),
      visible: el.getClientRects().length > 0
    })),
    buttons: all("button").map((b) => ({
      name: name(b), width: Math.round(box(b).width), height: Math.round(box(b).height),
      visible: b.getClientRects().length > 0
    })),
    headings: all("h1,h2,h3,h4,h5,h6").map((h) => Number(h.tagName[1])),
    thNoScope: all("th").filter((th) => !th.getAttribute("scope")).length,
    // An entry is cited by a numbered marker or by the row's own list of sources,
    // which links the pages themselves now that every figure carries its card.
    // The two together are what reads the register; a marker lives in the markup
    // for the printed sheet and the reader without a script.
    footRefs: all('a[href^="#fn"], a[data-fn]').map((a) => {
      const n = a.getAttribute("data-fn");
      return n ? "fn" + n : a.getAttribute("href").slice(1);
    }),
    footTargets: all('li[id^="fn"]').map((li) => li.id),
    externals: external.map((a) => a.href),
    rowRule: (() => {
      const marked = all("tbody.item[data-v]")[0];
      const plain = all("tbody.item:not([data-v])")[0];
      const cell = (row) => row && row.querySelector("tr.main > td.c-cmp");
      if (!marked || !plain) return null;
      const a = getComputedStyle(cell(marked)), b = getComputedStyle(cell(plain));
      const input = cell(marked).querySelector('input');
      return { border: parseFloat(a.borderLeftWidth),
               gap: input ? Math.round(box(input).left - box(cell(marked)).left - parseFloat(a.borderLeftWidth)) : -1,
               plain: parseFloat(b.borderLeftWidth) };
    })(),
    tags: all("#tbl tbody .vtag").map(text),
    priceFootnotes: all(".c-price .fn").length,
    zoomGlyphs: all(".zoom .zi").length,
    icon: document.querySelector('link[rel="icon"]')
      ? document.querySelector('link[rel="icon"]').getAttribute("href") : "",
    canonical: document.querySelector('link[rel="canonical"]')
      ? document.querySelector('link[rel="canonical"]').getAttribute("href") : "",
    ogTitle: document.querySelector('meta[property="og:title"]')
      ? document.querySelector('meta[property="og:title"]').content : "",
    contactLinks: anchors.filter((a) => /github\.com\/lydenyardley\/subfree-uk\/issues/.test(a.href)).length,
    hasGlossary: /Power over Ethernet/.test(text(document.body)),
    tiny: all("body *").filter((el) => {
      if (!el.getClientRects().length) return false;
      const cs = getComputedStyle(el);
      if (cs.display === "none" || cs.visibility === "hidden") return false;
      const own = Array.from(el.childNodes).some((n) => n.nodeType === 3 && n.textContent.trim());
      return own && parseFloat(cs.fontSize) < 11;
    }).map((el) => el.tagName.toLowerCase() + "." + String(el.className || "").split(" ")[0] +
      " at " + getComputedStyle(el).fontSize + ": " + text(el).slice(0, 24))
  };
}"""

PHONE_JS = r"""() => {
  const filters = document.getElementById("filters");
  const row = document.querySelector("#tbl tbody.item:not([hidden])");
  const verdict = document.querySelector(".verdict");
  const short = document.querySelector(".vshort");
  return {
    open: filters ? filters.open : null,
    firstRowTop: row ? Math.round(row.getBoundingClientRect().top) : -1,
    viewport: window.innerHeight,
    verdict: verdict ? getComputedStyle(verdict).display : null,
    shortAnswer: short ? getComputedStyle(short).display : null
  };
}"""

COST_JS = r"""() => {
  const row = document.querySelector("#tbl tbody.item");
  const a = row.querySelector(".c-nosub"), b = row.querySelector(".c-sub");
  return {
    aFits: a.scrollWidth <= a.clientWidth + 1,
    bFits: b.scrollWidth <= b.clientWidth + 1,
    aWidth: a.clientWidth,
    bWidth: b.clientWidth
  };
}"""

FILTERS_JS = r"""() => {
  const filters = document.getElementById("filters");
  const body = filters.querySelector(".fbody");
  return {
    open: filters.open,
    display: getComputedStyle(body).display,
    visible: body.getClientRects().length > 0
  };
}"""

HEADER_JS = r"""() => {
  const thead = document.querySelector("#tbl thead");
  const ths = Array.from(thead.querySelectorAll("th[scope=col]"));
  const buttons = Array.from(thead.querySelectorAll("button"));
  return {
    display: getComputedStyle(thead).display,
    width: Math.round(thead.getBoundingClientRect().width),
    headers: ths.length,
    untabbable: buttons.length > 0 && buttons.every((b) => b.tabIndex === -1)
  };
}"""

OVERFLOW_JS = r"""() => {
  const de = document.documentElement;
  const over = de.scrollWidth - de.clientWidth;
  const offenders = over > 0
    ? Array.from(document.querySelectorAll("body *"))
        .filter((el) => el.getBoundingClientRect().right > window.innerWidth + 1)
        .slice(0, 4)
        .map((el) => el.tagName.toLowerCase() + "." + String(el.className || "").split(" ")[0])
    : [];
  return { over, offenders };
}"""

BARS_JS = r"""() => {
    const bars = Array.from(document.querySelectorAll('#tbl tbody.item:not([hidden]) .bar i'));
    const scale = (b) => {
        const m = getComputedStyle(b).transform.match(/matrix\(([-0-9.]+)/);
        return m ? +m[1] : NaN;
    };
    const score = (b) => {
        const cell = b.closest('td');
        const n = cell && cell.querySelector('.score b');
        return n ? +n.textContent / 8 : NaN;
    };
    return {
        n: bars.length,
        transition: getComputedStyle(bars[0]).transitionDuration,
        property: getComputedStyle(bars[0]).transitionProperty,
        scales: bars.map(scale),
        targets: bars.map(score)
    };
}"""

DESKTOP_ROWS_JS = r"""() => {
    const table = document.getElementById('tbl');
    // The numbered record marker belongs to the printed sheet and to the reader
    // without a script: with a script the figure itself opens its card and the
    // number is off the screen. The label's words, and the track they sit in,
    // are the same either way, so the placement is measured with it shown.
    const markers = document.createElement('style');
    markers.textContent = '.js .fn{display:inline!important}';
    document.head.appendChild(markers);
    const head = Array.from(table.querySelectorAll('thead th')).map((th) => {
        const r = th.getBoundingClientRect();
        return {left: r.left, width: r.width};
    });
    const row = table.querySelector('tr.main');
    const card = table.querySelector('tbody.item');
    const rows = Array.from(table.querySelectorAll('tbody.item:not([hidden])')).map((item) => {
        const main = item.querySelector('tr.main');
        const n = main.querySelector('.c-nosub').getBoundingClientRect();
        const s = main.querySelector('.c-sub').getBoundingClientRect();
        const rec = main.querySelector('.c-rec .rec');
        const recCell = main.querySelector('.c-rec').getBoundingClientRect();
        const mark = main.querySelector('.c-rec a.fn');
        const rr = rec.getBoundingClientRect(), mr = mark.getBoundingClientRect();
        // The catch is a column of the row, or a band under it. Measure the
        // words the reader sees rather than the box they sit in: a shrinkable
        // box reports no overflow while its words paint across the chevron.
        const catchCell = main.querySelector('.c-catch');
        const cr = catchCell.getBoundingClientRect();
        const textBox = catchCell.querySelector('.catch-t').getBoundingClientRect();
        const more = catchCell.querySelector('.more-w').getBoundingClientRect();
        const range = document.createRange();
        range.selectNodeContents(catchCell.querySelector('.catch-t'));
        const words = Array.from(range.getClientRects());
        return {
            id: item.id,
            lefts: Array.from(main.children).map((cell) => cell.getBoundingClientRect().left),
            bottoms: Array.from(main.children).map((cell) => cell.getBoundingClientRect().bottom),
            heights: Array.from(main.children).map((cell) => Math.round(cell.getBoundingClientRect().height)),
            recW: Math.round(recCell.width),
            pair: {ny: Math.round(n.top), sy: Math.round(s.top), nx: Math.round(n.left), sx: Math.round(s.left)},
            // Where the footnote number sits against the label it cites.
            mark: {
                left: Math.round(mr.left),
                top: Math.round(mr.top),
                recLeft: Math.round(rr.left),
                recBottom: Math.round(rr.bottom),
            },
            catch: {
                left: cr.left,
                right: cr.right,
                top: cr.top,
                textRight: words.length ? Math.max(...words.map((w) => w.right)) : cr.left,
                textBottom: words.length ? Math.max(...words.map((w) => w.bottom)) : cr.top,
                textBoxRight: textBox.right,
                textLines: words.length,
                moreLeft: more.left,
                moreTop: more.top,
                moreBottom: more.bottom,
                caption: getComputedStyle(catchCell, '::before').content,
            },
        };
    });
    const clipped = [];
    table.querySelectorAll('th, td').forEach((cell) => {
        // A header kept for assistive technology is 1px wide and clipped on
        // purpose; its scrollWidth says nothing about the reader's page.
        if (cell.getBoundingClientRect().width <= 2) return;
        if (cell.scrollWidth > cell.clientWidth + 1) clipped.push(cell.className || cell.tagName);
    });
    markers.remove();
    return {
        display: getComputedStyle(row).display,
        tracks: getComputedStyle(row).gridTemplateColumns.split(' ').length,
        cardDisplay: getComputedStyle(card).display,
        visibility: getComputedStyle(card).contentVisibility,
        size: getComputedStyle(card).containIntrinsicSize,
        right: table.getBoundingClientRect().right,
        head,
        rows,
        clipped,
        overflow: table.scrollWidth - table.clientWidth,
    };
}"""

STUCK_JS = r"""() => {
    const th = document.querySelector('#tbl thead th');
    const r = th.getBoundingClientRect();
    const under = document.elementFromPoint(r.left + 40, r.top + 10);
    return {
        top: Math.round(r.top),
        covers: !!(under && under.closest('#tbl thead')),
        bg: getComputedStyle(under || th).backgroundColor,
    };
}"""

INK_JS = r"""() => {
    const cs = getComputedStyle(document.documentElement);
    const rgb = (value) => {
        const m = value.trim().match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
        if (!m) return null;
        const hex = m[1].length === 3 ? m[1].replace(/(.)/g, '$1$1') : m[1];
        return [0, 2, 4].map((i) => parseInt(hex.substr(i, 2), 16) / 255);
    };
    const lum = (c) => c
        .map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)))
        .reduce((a, v, i) => a + v * [0.2126, 0.7152, 0.0722][i], 0);
    const cr = (a, b) => {
        const la = lum(a), lb = lum(b);
        return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
    };
    const ink3 = rgb(cs.getPropertyValue('--ink3'));
    const paper = rgb(cs.getPropertyValue('--paper'));
    const tint = rgb(cs.getPropertyValue('--tint'));
    const raw = cs.getPropertyValue('--ink3').trim();
    if (!ink3 || !paper || !tint) return { raw, theme: 'unparsed' };
    return { raw, theme: document.documentElement.getAttribute('data-theme') || 'auto',
             paper: Math.round(cr(ink3, paper) * 100) / 100,
             tint: Math.round(cr(ink3, tint) * 100) / 100 };
}"""

SORT_JS = r"""async (uncontained) => {
    const frame = () => new Promise((r) => requestAnimationFrame(() => setTimeout(r, 0)));
    document.getElementById('reset').click();
    await frame();
    await new Promise((r) => setTimeout(r, 300));
    let off = null;
    if (uncontained) {
        off = document.createElement('style');
        off.textContent = '.main-t tbody.item{content-visibility:visible!important}';
        document.head.appendChild(off);
    }
    const sort = document.getElementById('sort');
    const tbl = document.getElementById('tbl');
    const layout = [];
    for (const value of ['price', 'score', 'keep3', 'model', 'price', 'score']) {
        const t = performance.now();
        sort.value = value;
        sort.dispatchEvent(new Event('change', { bubbles: true }));
        tbl.offsetHeight;  // read back the height, so the sort's layout is in the figure
        layout.push(Math.round((performance.now() - t) * 10) / 10);
        await frame();
        await new Promise((r) => setTimeout(r, 150));
    }
    if (off) off.remove();
    return layout;
}"""
