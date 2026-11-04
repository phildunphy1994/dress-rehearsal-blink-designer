# Discussion pack — BLINK, Friday 6 November 2026, 09:30–10:00 IST

> **Read this first.** This rehearsal used archival measured drawings of one house by one architect (Library of
> Congress, HABS survey) as a stand-in corpus. It proves that the learning loop works end to end. It does **not** prove
> that a living designer's hotel interiors can be reproduced, and no BLINK data was used or invented.

## 1. Before / after summary (one page)

<!-- RESULTS: filled from outputs/metrics.md at the end of the run -->

## 2. The reusable pipeline (one page)

| Step | What happens | Where it lives |
|---|---|---|
| Collect | Fetch the corpus, log source and rights per item, resize for analysis | `scripts/01_collect.py`, `data/provenance_rights.csv` |
| Freeze | Seeded split (learn / iterate / test) and briefs frozen **before** any drawing is opened | `scripts/00_freeze_splits.py`, `data/splits.json`, `briefs/` |
| Extract | One drawing per request: transcribe every legible dimension, then fill the fixed form (room, size, openings, built-ins, materials, palette, what is absent) | `prompts/transcribe_v1.txt`, `prompts/extract_v1.txt`, `scripts/02_extract.py`, `data/extractions/` |
| Aggregate | 10–15 testable rules, each citing ≥3 drawings with a quoted phrase per citation; mechanical audit of every quote | `prompts/aggregate_v1.txt`, `scripts/03_aggregate.py`, `scripts/audit_evidence.py`, `outputs/rule_library_v*.json/.md` |
| Iterate | Generate on practice briefs, compare with the practice drawings, fix rules or prompt, **freeze v2** | `outputs/iteration_log.md` |
| Generate | Same brief to two isolated designers: brief only vs brief + frozen rules; identical prompt otherwise | `prompts/generate_{baseline,learned}_v2.txt`, `scripts/04_generate.py`, `outputs/designs/` |
| Draw and check | Dimensioned plan, elevation, palette board from the spec; 8-point constraint checklist | `scripts/05_svg.py` |
| Blind test | Coin-flipped A/B, stripped diagrams, judge pack; A/B key kept apart | `scripts/06_blind.py`, `outputs/blind/` |
| Held-out check | Frozen rules checked against the locked drawings, once | `scripts/08_held_out_check.py` |
| Report | Metrics computed from the recorded files, never by hand | `scripts/07_report.py`, `outputs/metrics.md` |

To run the same loop on BLINK rooms: replace the corpus (plans, elevations, FF&E schedules, boards, photos, why-notes),
keep everything else. Every model step was run by the session model in isolated contexts; no fine-tuning, no API.

## 3. What this does and does not prove

- **Proves:** rules can be extracted from drawings with evidence that survives a mechanical audit; a frozen rulebook
  measurably changes what an otherwise identical designer produces; the loop (collect → extract → aggregate →
  iterate → generate → blind test) runs end to end with split discipline and no leakage.
- **Does not prove:** that modern hotel interiors or any living designer's work can be reproduced; that taste
  transfers from a 12-drawing archival corpus to a different building type; that judges would prefer the rule-driven
  rooms (the test asks which set *follows the rules*, not which is *better*).
- **Caveats to say out loud:** no control corpus (Corpus B was gated), so the library is untested against generic
  practice; the constraint-violation metric hit a floor (the baseline already satisfies every checkable constraint),
  so it cannot discriminate on these briefs; supplementary Claude judges are not human judges.

## 4. Talk track

- "We tested whether learned rules help. Same briefs, same model, with and without the rules. <!-- RESULTS -->"
- "Capture first, train last. Designer data, designer judging, NDA first."
- "Pilot: one room type, one interview, sample data only, BLINK owns everything."
- "Proof before scale: blind test — clone vs generic vs past work — before scaling."

## 5. Data request for the pilot

For 20–30 hotel rooms, ideally one room type to start (e.g. standard king):

1. Sketches / concept boards for each room.
2. Plans and elevations (PDF or DWG); 3D or Revit files if they exist.
3. FF&E schedules.
4. Material boards / palettes.
5. Finished photographs.
6. **Most valuable:** short why-notes on decisions that changed — what was tried, what was rejected, and why.
7. Brand / operator standards that applied.

Sample data only until an NDA is signed. BLINK retains all ownership. Nothing leaves BLINK's control without the NDA.

## 6. What not to claim

- Do not name the proxy corpus as a hotel precedent.
- Do not claim the rehearsal used BLINK data.
- Do not promise autonomous generation without a designer in the loop.
- Do not quote a price or timeline for the full build; the pilot establishes both.
