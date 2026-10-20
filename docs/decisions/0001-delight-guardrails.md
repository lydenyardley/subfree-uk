# 1. Delight guardrails for the comparison page

- Status: Accepted
- Date: 19 October 2026
- Source: the first delight audit run on 19 October 2026, superseded by the
  read-only re-run in `docs/audits/2026-10-19-delight.md`. This record keeps
  the durable decisions from the first run.

## Context

SubFree UK is a one-page research surface. A reader arrives with a vague
question, scans 14 UK doorbells, and leaves with a shortlist or a purchase.
It is used once or twice, often on a phone in a hallway. The page earns trust
with evidence, not with brand theatre.

The first 19 October audit set a thesis and a set of guardrails. The shipped items
from that audit were D6 (compare cost row), D7 (nearest-match recovery),
D9 (jump announcement), D10 (theme motion), D11 (score-bar draw),
D13 (copy shortlist) and D14 (favicon and Open Graph). The decisions below
are what later work must preserve.

## Decision

### The delight thesis

> The reader should feel they have just read the best-argued page on the
> subject, and that the page did the arithmetic for them.

Delight here means relief. The relief of a decision made cheap, an assumption
stated rather than buried, and a dead end that turns into a nudge. It is not
whimsy, and it is not a campaign voice.

### Personality visits four moments

1. **The short answer.** The reader arrives with a vague question and leaves
   with a named model.
2. **The comparison.** Specs become a decision, and the money does the talking.
3. **Recovery.** A filter asks for something the dataset cannot give, and the
   page offers the nearest real option.
4. **Completion.** The reader has a shortlist worth sending to someone.

Everything else, including sorting, filtering and the table, stays quiet and
immediate. Reliability carries the page.

### Protect the register

These five things are the page's authored signature. Do not sand them off in
a redesign.

- The verdict is an argument, not a summary. Three named picks, each with a
  reason and a consequence, set beside 3px colour rules.
- The tray speaks like a person. "1 selected (tick 1 or 2 more)" anticipates
  the next move instead of reporting state.
- The record markers and the score bar form one notation. Filled, half and
  empty shapes read without a legend.
- The assumption is confessed in the sentence that uses it. The £10 card
  figure is labelled as uncited in the same breath.
- The page is fast because it is honest. No webfonts, analytics, tracking or
  third-party requests. The byte budget is part of the experience.

### Closed and deferred decisions

- **Price bounds stay as bounds.** D8 proposed "No minimum" and "No maximum"
  labels. It is declined. The labels read £40 and £300, the bounds are
  accurate, and the reader is not misled. Revisit only with evidence that the
  first state reads as pre-filtered.
- **The three-model cap stays.** The count line explains the cap and offers a
  swap instruction. D12's automatic replacement with Undo is deferred. It is
  worth building only if the cap proves to be a real stopping point. If it is
  built, Undo must restore the exact previous selection, and the swap must not
  steal focus or scroll.
- **The identity work stays shipped.** The local SVG favicon, canonical URL
  and Open Graph tags are part of the page. The Open Graph image must stay a
  real product photo already used on the page.

### Quiet zones

Do not add any of the following to this page:

- a loading spinner, because there is nothing to load;
- confetti, sound or a celebration on compare;
- a cookie banner, because there are no cookies;
- a scroll-triggered fade on every row;
- a new font, analytics script or share SDK.

### Verification contract

Every future delight item is done only when:

1. It works with the keyboard alone, in the same order a sighted reader uses.
2. Any state change is announced once, politely, and is also visible as text.
3. `prefers-reduced-motion: reduce` removes the motion without removing the
   information.
4. It adds no external request and no dependency, and the page stays under
   about 200 KB total.
5. `python build/check.py` still exits 0, with axe clean in both themes at
   1280, 820 and 390, and no horizontal overflow at the seven tested widths.

## Consequences

New work can still surprise the reader at the four moments above. It must not
turn the quiet parts into a performance, reopen a declined decision without
new evidence, or spend the byte budget on a font or a library. The next
delight audit can propose new moments, but it inherits these guardrails.
