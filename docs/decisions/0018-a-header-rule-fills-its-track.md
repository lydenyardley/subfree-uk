# 18. A header's rule fills its track and takes its column's colour

- Status: Accepted
- Date: 23 October 2026
- Source: the owner's review of 23 October 2026: a gap on the table's bottom
  border, and the comparison header no longer rendering its columns' colours.

## Context

Two defects in the table's rules, both visible on the page and neither caught
by an assertion.

**The 2px gap.** ADR 6's first track was `calc(2.5rem + 2px)`: the compare
box's own 40px plus the 2px where the collapsed table border sat. ADR 6 then
made each row a grid track, so nothing collapses any more, but the 2px stayed.
The compare cell keeps `width:2.5rem`, so the header's cell painted 40px of rule
inside a 42px track and left a 2px hole before the model column. The body cell
was reset to `width:auto` and filled its track, which is why the hole showed
only under the header.

**The colour.** `ee2a7eb` replaced the per-column header rule with one 3px rule
in the page's ink. The column still carries `data-v` and `--vc`, and the badge
under it still shows the verdict in colour, but no rule read either, so a best
column and an avoid column drew the same ink line.

## Decision

The first track is 40px in all four grid templates, at 821, 1200 to 1279, 1280
and 821 to 900. A grid row has no collapsed border to pay for, and 40px is the
compare box's own width.

```
.cmp-t thead th[data-v]{border-bottom-color:var(--vc)}
```

The spec column holds no model and keeps the page's ink. The rule stays 3px,
the width of every verdict line on the page, so colour is not the only signal.

## Measurements

At 1280 the header's compare cell and its track were 40px and 42px, and the
model column started at 58. After the change both are 40px and the model column
starts at 56. The `best` column's rule is `#5fc896` where it was the ink.

The 2px goes to the catch at every desktop width, and it changes one height:
the page is 19px shorter at 940, where the wider catch loses a line. At 1440,
1300, 1280, 1101, 1100, 1000, 900 and 821 the page keeps its height.

## Rejected

- **Widening the compare cell to 42px.** It keeps the stale 2px as a second
  number to keep in step, and the body cell would carry 42px for a 24px box.
- **Colouring every header rule.** The spec column has no verdict, so one of
  the colours would be a guess.
- **A `data-v` on the table with a selector over its columns.** Each column
  already carries its own attribute and its own custom property.

## Consequences

- `desktop rows` asserts that each header cell's box reaches the next cell's
  left edge, and that the last one reaches the table's. On the old tracks it
  reports a 2px hole after column 0 at 1280 and 1440, in both fonts.
- `compare markers` asserts each column's rule is 3px in its verdict's colour
  and that the spec column's is 3px in ink. On the old CSS it reports the best
  and avoid columns in ink.
- ADR 6's 2px is gone, and its note about the first track describes history
  rather than the stylesheet.
