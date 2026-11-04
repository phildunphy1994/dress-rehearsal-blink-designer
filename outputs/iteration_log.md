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

(filled after rendering and checking the four iteration designs)

## C. Changes v1 → v2

(filled; every change names the iteration drawing or iteration design that motivated it)
