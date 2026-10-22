# 10. The header words lead the tracks

- Status: Accepted
- Date: 22 October 2026
- Source: the GitHub audit that failed on Ubuntu: `at 1100px a cell clips its
  text: TH`, the same at 1000 and 900, and `the sub cost header takes 4 lines`.

## Context

ADR 6 read the tracks off the table at 1280px, and until now they held. The
audit passed on Windows and failed on CI, at widths it had always passed, so
the page was not the difference: `system-ui` is Segoe UI on Windows, Arial on a
Mac and DejaVu Sans on a bare Ubuntu, and DejaVu is 5 to 8% wider at 12px.

Two of the eight columns were sized to the words they carry rather than to a
floor. Under DejaVu the score header needed 89px against an 84px column — which
is what `a cell clips its text: TH` was, a clipped header, not a cell — and the
two cost columns at 10% of 1280px left each button 68px, so
`3-year cost, with plan` and its marker took four lines instead of three.

Nothing in the audit could see the font: every check measured the browser it
ran in.

## Decision

### Every header word gets a floor

`minmax(90px,7.4%)`, `minmax(84px,6.7%)` and `minmax(96px,8.2%)` replace the
fixed 120px, 6.7% and 8.2% on the three columns whose header is a word a font
can widen. The floor is the width that word needs under the widest common
fallback; the percentage above it is still the table's own proportion, so the
columns only move where the font forces them to.

### The cost columns are 152px from 1280px

At 12px, `3-year cost,` and its marker need about 100px, and the header button
has 32px of padding. A 152px track is a two-line header at 1280 and a three-line
one anywhere above it. Below 1100px there is no width to take: eight columns at
1100 leave the catch 284px, and the five-line cost headers the narrow band
already had. From 1101 to 1279px the 10% columns stay and the sub header takes
four lines; the band was outside the audit before this change and is outside it
now.

## Rejected

- **Tuning the percentages until CI passed.** The next fallback font, or a
  browser with a minimum font size, moves it again. A floor states the
  requirement; a percentage only spends what is left.
- **Smaller header text.** The type floor is 12px and `type floor` asserts it.
- **Letting the header take five lines everywhere.** The header is the tallest
  row of the table, so every line it takes is a line off the first paint of
  every row.
- **Giving 1101 to 1279px the 152px cost columns too.** Measured on the tracks:
  the catch falls from 255px to 164px, and the catch holds the longest
  sentences, so most rows gain a line.

## Consequences

- The line count alone could not catch this on a machine with a narrow default
  font, so `cost header name` also asserts each cost header's button is at
  least 100px at 1280px. The button's width is the track less the marker and
  the padding, so it does not depend on the font, and it is the number the line
  count is decided by.
- Built with Verdana in place of `system-ui` — 5 to 8% wider than Arial and
  within a pixel of DejaVu Sans on these words — no cell clips at 1440, 1280,
  1100, 1000 or 900, and both cost headers take two lines at 1280 and five at
  1100. That is the state CI will build; the audit on a Segoe or Arial machine
  is the narrower case.
- The table measures 1,420px at 1280 against 1,419px before, and 1,359px at
  1440 against 1,346px: the floored columns hand 13px to the catch, which takes
  a line back on a few rows.
- The catch cell at 821px still clips a long sentence: by 11px with Segoe UI,
  22px with Verdana. It clipped before the floors too — 82px of content then,
  80px now — and the audit does not measure 821.
