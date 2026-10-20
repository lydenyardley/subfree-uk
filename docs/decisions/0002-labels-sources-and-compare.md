# 2. Labels that match the data, and a shorter proof

- Status: Accepted
- Date: 20 October 2026
- Source: the four read-only audits of 19 October 2026. All four are
  completed and removed; what was declined rather than built is in ADR 5.

## Context

The audits found the page behaving well and its words drifting from its data.
Nest said "Only with extra kit" for a three-hour limit, three rows showed a
bare dash where they have no plan at all, and the Power filter asked the
reader to choose "PoE" a screen before the method defined it. The proof at the
end of the page was 2,207px of numbered links on a phone, and the copy action
confirmed success without saying what had been copied.

Each of the seven changes below is now in the page and asserted in
`build/check.py`.

## Decision

### The record column has four states, and the fourth names a time limit

`yes`, `kit` and `no`, plus `brief` for a model that records with no extra
hardware but keeps the footage for a short time. The label is
"Only briefly (3 hrs)", not "kit", because the reader's next move differs: one
needs to buy a hub, the other needs to decide whether three hours is enough.

A new row must pick the state that describes its limit. If a future model
records free for a day and then stops, that is a fifth state with its own
number, not a stretch of `brief`.

### The plan column says "No plan" instead of nothing

An empty cell reads as missing data, a zero cost or a rendering bug. The words
cost one line and answer the column's question. Sorting treats "No plan" as
zero, so the cheapest plan is the one you do not buy.

### A term used in a filter is defined at the filter

The Power group carries "PoE: one cable carries both power and data." The
method keeps the full glossary. The rule generalises: if a control asks the
reader to choose a term, the definition belongs within sight of the control.

### Copying says what was copied, and the button keeps its name

The confirmation is a polite status line under the compare header, naming the
model count, the prices and the date, and telling the reader what to do with
it. It fades after six seconds. The button label never changes, so the
control does not move under the pointer.

### Identical rows can be hidden, but the decisions never are

"Differences only" hides spec rows that match across every selected model and
says how many it hid. It is off by default, because hidden rows on a first
visit read as missing data. Four rows and the cost row stay whatever the
toggle says: records free, price, both three-year costs. Equality there is the
finding, not noise.

### The source list is a disclosure, grouped by host, with stable numbers

Below 821px the list is closed; above it, open. Each link sits under the site
it points at, ordered by first appearance, and every `li` carries its footnote
number as a value, so grouping never renumbers a claim. Print opens it.

### The phone card has one label column

Four spec cells put a muted label to the left of the value; the price carries
no label, because the pound sign names it; the main catch keeps its label
above its prose. A 136px label column would have squeezed four lines of
argument into 150px.

## Consequences

- The compare panel no longer carries `aria-live`. It used to announce all
  eighteen rows on every render. The tray says how many doorbells are being
  compared, and the copy confirmation has its own status region.
- The bar draw no longer forces a reflow. The task boundary commits the zeroed
  bars, which is what the reflow was there for.
- `docs/performance-budget.md` holds the numbers a change has to keep. Two are
  enforced by `build/check.py`; the long-task line is open and named there.
- A change that adds a row, a source or a phone field has an obvious home for
  each: a record state that names its limit, a host group, and a label or a
  stated reason for none.
