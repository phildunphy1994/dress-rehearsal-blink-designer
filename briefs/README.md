# Briefs — frozen at T0, before any drawing was opened

All five briefs below were written and frozen **before** any Corpus A drawing was downloaded or
analysed, and before any rule library existed. Frozen on 2026-11-04 (see `briefs/briefs.json`
`frozen_at`). No brief may change after this point (PRD §4).

The room text (type, size, ceiling, functions, openings) is copied verbatim from PRD §4.2–4.3.
PRD §4.1 additionally requires every brief to state materials that must / must not be used and at
least three objectively checkable constraints. The PRD's brief texts omit the materials clause, so the
executor added one **identical neutral materials clause to every brief at T0** (before extraction):

- **Must:** the floor finish is named with material and finish.
- **Must not:** mirrored wall panels; high-gloss lacquer on any wall surface.

These were chosen to be style-neutral (a generic designer and a rule-following designer can each
satisfy or violate them equally) so that they do not tip the before/after comparison.

## Geometry convention (used by every spec, SVG and checker)

- The room is a rectangle `length_m` (x axis) × `width_m` (y axis), interior clear dimensions.
- Origin (0, 0) is the interior south-west corner. x runs east, y runs north.
- **South wall** is y = 0; **north wall** is y = width; **west wall** is x = 0; **east wall** is x = length.
- "Long walls" are the two walls whose length equals `length_m` (north and south).
  "Short walls" are west and east.
- All dimensions in metres, 2 decimal places. Heights are measured from finished floor level (FFL).

## Checkable constraints

Each brief's machine-readable constraints are in `briefs/briefs.json` and are what `scripts/05_svg.py
--check` scores (PRD §5.4). The `.md` files are the human-readable brief that the generator receives.
