# Iteration log — rule library v1 → v2 (PRD §3.3)

Iteration set (6 sheets, never used for extraction into the library): 02 first (ground) floor plan, 11 furniture (dresser,
headboard, footboard), 16 first floor plan (second survey), 22 section, 24 front detail, 25 window detail.
Iteration briefs: I1 living room 6.0 × 4.5 m; I2 dining room 4.8 × 3.6 m. Both arms generated for both briefs so that any
prompt fix is tested on both arms, but only the learned arm is used to judge the rules.

## A. Iteration-set evidence review of v1 (from the iteration extractions, before seeing the generated designs)

| v1 rule | Iteration-set evidence | Verdict |
|---|---|---|
| R03 central chimney-and-stair core on the long axis | 02 and 16: thick hatched central core with the stair inside, two long rooms either side, openings past it | supported |
| R04 pointed prow bays at both ends | 02, 16: pointed/chevron bays at room ends; 24: V-plan bay with chamfered piers and continuous glazing on both angled faces | supported |
| R05 low hipped roofs, deep cantilevered eaves | 22: low-pitched roof, deep overhang, tapered soffit, thin fascia; 24: deep three-line eave band | supported |
| R07 windows as continuous ribbons between narrow piers | 02: five sashes between six short hatched piers; 16: identical window group in every 4'-0" bay; 24: tall narrow paired lights under a continuous head line | supported; the 4'-0" pier module recurs on 16 (as on 03/17 in the learning set) |
| R08 horizontal coursing, every edge capped by a plain band | 22, 24: brick as close horizontal coursing; continuous projecting sill course of plain blocks (24); copings on every parapet (22) | supported |
| R09 straight-line leaded glass (mixed) | 25: both lights are straight-line leaded patterns (ladder bars, chevron heads, diamond band, V-came) | supported; stays "usually" because 20/21 in the learning set show plain thin-framed glazing |
| R11 glazed-door band onto a full-length balcony | 22: very narrow full-height glazed openings between every terrace and its interior, floor to underside of slab | supported |
| R12 no expressed entrance; entry is a recessed ground-level door into a small hall, then a stair up against the core | 02: recessed doorway in the north wall into a small hall; stair rises against the core; 16: vestibule at the junction of bar and wing | supported — and 02 adds the *interior* entry sequence (small hall → stair → main level) that v1 only implied |
| R14 stepped rectangular layers, no carving or turning | 11: paired slender posts ending in stacked square block feet, slab-like oversailing top rails with a thinner secondary rail beneath, square pulls on a grid | supported |
| Do-not: hearth never on an outside wall | 02, 16: fireplace/stair core is internal on both ground-floor plans | supported |
| New candidate from the iteration set only: interior doorways with dropped heads (lintel notches) — 22 | only one sheet; cannot become a rule (≥3 learning sheets required) | not added |

No v1 rule is contradicted by the iteration drawings. The question for v2 is therefore not correctness but **usability at
room scale**: most v1 statements describe whole-building massing, and the briefs are single rooms. Section B records what
the generated iteration designs showed.

## B. Iteration designs (generated with v1) — findings

### B.1 Checker (scripts/05_svg.py) fixes found on the first iteration design (I2 baseline) — apply to both arms
1. Check 5 penalised a path for approaching its own door (wall clearance measured to the wall even inside a door
   opening). Fixed: inside a door/opening span the clearance is measured to the jambs.
2. Check 5 "path reaches dining_table" used a 0.8 m tolerance, which a row of chairs between path and table always
   breaks. Fixed: 1.5 m for the dining table target.
3. Check 7 flagged "no high-gloss lacquer" (a sentence *complying* with the brief) as a forbidden term. Fixed: a
   mention preceded within 40 characters by a negation (no / not / never / without / avoid / free of / rather than /
   instead of / non) is not a violation. Known limit: "avoid X and use Y" reads Y as negated too; check-7 flags are
   therefore reviewed by hand whenever they fire, and the review is recorded in outputs/violations.csv notes.
4. Renderer cosmetics only (no metric effect): no doubled "built-in built-in" prefix, long item names truncated,
   rug/pendant labels moved to the item's top edge.
After these fixes the I2 baseline design scores 0 violations; the scratch fixture still scores its 1 deliberate
violation (path through a sofa), so the checker still catches real faults.

### B.2 Design-level findings (all four iteration designs rendered and checked with the fixed checker)

| design | violations | rule traceability | notes |
|---|---|---|---|
| I1 baseline | 0 | n/a | limestone fireplace on the west short wall, slatted oak screen + 2.20 m soffit vestibule, 3.90 m window band, engineered oak |
| I1 learned | 0 | 10/10 major decisions cite a rule; 61/61 citations are real rules | brick chimney mass with raised hearth plinth and plain cap bands, 4.50 m casement band with 0.45 m sill course and leaded lattice, oak entry screen under a 2.10 m gallery soffit, built-in window seat, planter trough; 4 rule/brief conflicts recorded |
| I2 baseline | 0 | n/a | one joinery wall (sideboard · banquette · sideboard), slim table, chairs on one side, straight 1.80 m corridor |
| I2 learned | 0 | 12/12; 70/70 | brick-plinth banquette, oak head band, three outward-swinging leaded glazed leaves on the south wall, tall narrow-backed chairs, leafless passage "past the chimney core"; 3 conflicts recorded |

Findings:
1. **Floor effect on the constraint metric.** Both baselines already score 0 violations: a frontier model given a precise,
   checkable brief satisfies every §5.4 check without rules. The pre-registered pass criterion "learned ≥ 2 fewer
   violations than baseline" therefore cannot be met on these briefs; the test phase will report it as measured and
   state the floor effect explicitly rather than move the bar.
2. **The learned arm is recognisably different.** Both learned designs carry the corpus's moves (brick mass, plain cap
   bands, low sill course, casement ribbon, stepped-layer joinery, flush entry into a compressed vestibule) while the
   baselines are competent contemporary rooms. Traceability is 100% in both learned designs.
3. **v1 rules are stated at building scale.** Every learned design had to translate whole-building rules (prow bays,
   balcony doors, no main-floor entrance, central chimney-and-stair core) into a single room and recorded the
   translation as a conflict. The translations the two designs chose agree with what the iteration drawings show
   (§A), so the fix for v2 is to write the room-scale application into each rule rather than to change any rule.
4. **Generation prompt ambiguity.** "at least min_clear_width_m of clear floor either side of its centreline" was read
   as 0.90 m per side by one agent (I2 learned) and as 0.45 m per side by another. Fixed in prompt v2 (both arms,
   identical wording): clear width is measured across the path, 0.45 m either side for a 0.90 m path.
5. **Renderer legibility.** Dense learned designs (11 elevation elements, 7 datums, 3 adjacent door leaves) produced
   colliding labels. Plans and elevations now use id tags with a key table; datum labels are stacked; openings are
   tagged. Cosmetic only, identical for both arms, and required for a fair blind test.

## C. Changes v1 → v2 (frozen)

**Rule library.** No rule added, dropped, re-ordered or re-evidenced; all 81 evidence quotes unchanged and re-audited.
Each rule statement gains one "At room scale: …" clause, and two do-not entries gain a room-scale clause. Motivating
iteration drawings (and, where relevant, the iteration design that exposed the need):

| rule | motivating iteration sheet(s) / design |
|---|---|
| R01 horizontals | 22, 24 |
| R02 service strip | 02, 16 |
| R03 hearth as internal core | 02, 16; I1 and I2 learned conflicts |
| R04 prow bay or honest end wall | 24; I1 learned conflict |
| R05 ceiling edge as deep band | 22 |
| R06 asymmetric whole, symmetric element | 24, 02, 16 |
| R07 casement band on a 4'-0" module | 16, 02 |
| R08 light cap on every masonry edge | 24, 22 |
| R09 leaded lattice where detailed | 25 |
| R10 built-in planting | 22 |
| R11 full-height narrow glazed leaves | 22 |
| R12 flush door into compressed vestibule | 02, 16 |
| R13 chimney breast as plain capped slab | 22 |
| R14 stacked slabs and square posts | 11 |
| R15 framed infill panels | 24 |
| do-not: hearth not on an outside wall | 02, 16 |
| do-not: no expressed entrance | 02, 16 |

**Generation prompt.** `prompts/generate_{baseline,learned}_v2.txt`: circulation wording fixed (finding B.2-4). The
two v2 files differ from each other only by the rules block, as in v1.

**Checker.** `scripts/05_svg.py` fixes B.1 (door-span clearance, dining-table reach, negated must-not terms, arrival
zones at path ends) and the renderer key/tag changes (B.2-5). Verified: the scratch fixture still scores its one
deliberate violation; the iteration designs score 0.

**Frozen.** `outputs/rule_library_v2.json` (+ `.md`, `.generation.md`, `_evidence.md`, `.meta.json`) is the library
evaluated in the test phase. After this point no rule, prompt, split or checker threshold changes.
