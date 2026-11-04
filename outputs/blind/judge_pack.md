# Blind judge pack — TEST briefs

## Judge task (verbatim)

"You will see 3 pairs of room designs. Each pair was designed for the same brief. One set in each pair was designed following a specific set of design rules extracted from a coherent body of work; the other was designed without those rules, for the same brief. For each pair: (1) pick which set you think follows the rules, (2) rate your confidence 1–5, (3) in one sentence, say what made you pick it. Do not discuss pairs with other judges until all scores are recorded."

Source style, in one line (derived only from the rule library's signature moves; no designer or project names):
A body of work whose signature moves are: A continuous ribbon of tall narrow casements between narrow brick piers set directly under a deeply cantilevered, very low-pitched hipped roof with a thin fascia, running the full length of the main storey (00005, 00006, 00019, 00020, 00021); A long thin living-dining bar with a central brick chimney-and-stair core on its long axis, the rooms flowing past the core on both sides, a continuous glazed-door wall onto a full-length balcony, and pointed glazed prow bays at both ends (00003, 00017, 00005); Brick drawn as horizontal courses only, every wall top, sill, pier and chimney capped by a plain light band, with low stepped garden walls carrying planter urns on piers extending the base outward (00005, 00006, 00019, 00020, 00021).

For each pair you will be given: the brief text, Set A (plan, elevation, palette board) and Set B (plan, elevation, palette board).

Record your answer for each pair as one CSV row, exactly:
brief,picked,confidence,reason
where picked is A or B, confidence is an integer 1–5, and reason is one sentence in double quotes.


Record one CSV row per pair: `brief,picked,confidence,reason` (picked = A or B; confidence 1–5; reason in quotes).

## Pair — test_a

### Brief

# Test Brief A — Living room, low and long (TEST set — held out)

**Room:** Living room, 5.50 m × 4.20 m (interior clear), ceiling 2.30 m. Low and long.

**Must:**
1. Fireplace wall required (a fireplace/hearth element on one wall).
2. Ribbon windows on one long wall (north or south), spanning at least 60% of that wall's length.
3. Seating for 5 (seating count, counted on the furniture schedule).
4. No direct entry onto the seating area: the entry door's centre must be at least 1.50 m from the nearest seating footprint, and the design must include a named entry element (vestibule, screen, built-in, step or ceiling change) between door and seating.
5. At least one entry door (0.80–1.00 m wide) on a wall of the designer's choice.

**Materials — must:** the floor finish is named with material and finish.
**Materials — must not:** mirrored wall panels; high-gloss lacquer on any wall surface.

**Always:** clear circulation path ≥ 0.90 m from the entry door to the principal seating and to the fireplace; no furniture within any door swing; all furniture inside the room with no overlapping footprints.

**Principal wall for the elevation:** the fireplace wall.


### Set A

![plan](test_a/set_A/plan.png)

![elevation](test_a/set_A/elevation.png)

![palette](test_a/set_A/palette.png)

### Set B

![plan](test_a/set_B/plan.png)

![elevation](test_a/set_B/elevation.png)

![palette](test_a/set_B/palette.png)

## Pair — test_b

### Brief

# Test Brief B — Study / bedroom (TEST set — held out)

**Room:** Study / bedroom, 4.20 m × 3.60 m (interior clear), ceiling 2.40 m.

**Must:**
1. Built-in desk and built-in shelving on one wall (both on the same wall, both marked built-in).
2. A bed or daybed (at least one item with function bed).
3. A window band on one wall, spanning at least 50% of that wall's length.
4. Storage solved without freestanding wardrobes: at least one storage item, and no item with function wardrobe that is freestanding.
5. At least one entry door (0.80–1.00 m wide) on a wall of the designer's choice.

**Materials — must:** the floor finish is named with material and finish.
**Materials — must not:** mirrored wall panels; high-gloss lacquer on any wall surface.

**Always:** clear circulation path ≥ 0.90 m from the entry door to the desk and to the bed; no furniture within any door swing; all furniture inside the room with no overlapping footprints.

**Principal wall for the elevation:** the built-in desk and shelving wall.


### Set A

![plan](test_b/set_A/plan.png)

![elevation](test_b/set_A/elevation.png)

![palette](test_b/set_A/palette.png)

### Set B

![plan](test_b/set_B/plan.png)

![elevation](test_b/set_B/elevation.png)

![palette](test_b/set_B/palette.png)

## Pair — test_c

### Brief

# Test Brief C — Dining / living combined (TEST set — held out)

**Room:** Dining / living combined, 7.20 m × 4.50 m (interior clear), ceiling 2.40 m, with a level change or a ceiling change.

**Must:**
1. Define two zones (dining, living) without a full wall: the spec names two zones and no partition element spans the full room width.
2. A level change or a ceiling change is present and located on the plan (a step/platform or a dropped/raised ceiling area).
3. Seat 8 for dining (dining seats counted on the furniture schedule).
4. Include a fireplace or hearth element.
5. Keep a clear circulation path of at least 0.90 m through the room, from one end wall to the other.
6. At least one entry door (0.80–1.00 m wide) on a wall of the designer's choice, plus at least one window.

**Materials — must:** the floor finish is named with material and finish.
**Materials — must not:** mirrored wall panels; high-gloss lacquer on any wall surface.

**Always:** no furniture within any door swing; all furniture inside the room with no overlapping footprints.

**Principal wall for the elevation:** the fireplace / hearth wall.


### Set A

![plan](test_c/set_A/plan.png)

![elevation](test_c/set_A/elevation.png)

![palette](test_c/set_A/palette.png)

### Set B

![plan](test_c/set_B/plan.png)

![elevation](test_c/set_B/elevation.png)

![palette](test_c/set_B/palette.png)
