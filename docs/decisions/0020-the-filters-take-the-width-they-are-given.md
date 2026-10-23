# 20. The filters take the width the row gives them

- Status: Accepted
- Date: 23 October 2026
- Source: the owner's review of 23 October 2026: the power options wrap onto
  two lines in a widescreen view, and the price slider could be wider.

## Context

The controls row is `display:flex` with the filter details, the sort control
and the count. The details box was `flex:0 1 auto`, so it sat at its own
max-content width, and inside it `.fbody` is a nowrap flex row of two
fieldsets and the price control.

Measured at 1280, the details box was 794px inside a line that could give it
909px. Its max-content width is the sum of its items' flex bases, and the price
control contributes its 180px basis rather than the 320px it may grow to, which
left the two fieldsets a few pixels short of their own labels:

| Group | Width | Labels need | Result |
|---|---|---|---|
| Show only | 351px | 356px | two rows |
| Power | 201px | 205px | two rows |

So "Battery", "Wired" and "PoE" wrapped onto two lines in a space that had room
for them, and the price slider sat at 178px with the rest of the row empty.

## Decision

From 821px the details box takes the line the controls row gives it, and the
price control is no longer capped at 320px:

```
@media (min-width:821px){
 .filters{flex:1 1 auto}
 .range{max-width:none}
}
```

## Measurements

Chromium, every option group measured by the distinct top edges of its labels.

| Width | Details box | Option groups | Price slider | Page height |
|---|---|---|---|---|
| 1440px | 794 → 1,069px | 2, 2 → 1, 1 rows | 178 → 445px | 3,950 → 3,914px |
| 1280px | 794 → 909px | 2, 2 → 1, 1 rows | 178 → 285px | 4,217 → 4,181px |
| 901px | 794 → 853px | 2, 2 → 1, 1 rows | 178 → 229px | 6,358 → 6,322px |
| 821px | 773 → 773px | 2, 2 → 2, 2 rows | 172 → 172px | 6,538 → 6,542px |

The 40px each page loses from 901 up is the controls row dropping one line,
less the 4px the shorter mast adds back; at 821 the row is still too narrow to
gain a line and only the mast shows. The whole width between 821 and 901 is
still squeezed, which is a separate problem this does not solve.

The 1280 row has about 50px of slack in the page's own font. Under a fallback
font 15% wider the sort control grows 46px and the row is within a pixel of
fitting again, so a font that wide wraps the groups at 1280 and needs 1440,
where the slider is still 337px. That limit is the row's own: the filter
content is about 95% of the line at 1280 before the sort control takes its
share, and the flex line cannot make the sort yield without letting the
fieldsets overflow at 821.

## Rejected

- **Letting `.fbody` wrap.** The price control would drop to a second line at
  widths where the row is only a few pixels short, which makes the controls
  two lines tall to save one line of options.
- **A 320px slider from 821px.** The row is 853px at 901, which leaves 229px
  for the slider once the groups have their width; a fixed 320 would take the
  space back from them and wrap them again.
- **Trimming the gaps to make the old box fit.** 16px on the inner gaps would
  make the groups fit at 1280 and wrap again under a wider fallback font.

## Consequences

- `filters row` measures the 1440 page, where a 15% wider fallback font still
  has room: one line per option group, and the price slider at least 300px
  wide. On the old stylesheet it reports two rows and a 178px slider.
- `docs/performance-budget.md` carries the page heights above.
- The mast's padding and the theme button's 44px target are in the same
  review but need no decision record: both are the site's own type sizes and
  the 44px is the smallest target a thumb can hit.
