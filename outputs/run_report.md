# Run report — Dress rehearsal: learn a design language, generate, test

Run date: 2026-11-04 (UTC). Executor: Claude Fable 5.1 running in a Claude Code cloud session on this repository
(branch `claude/stoic-maxwell-1np0zy`). Every model step was run in-session; no API key, SDK or external service was used.

> **Limitation (PRD §0.2, §9.3), stated first:** this run proves a learning loop on archival residential
> architecture (one architect, one house, measured drawings). It does **not** show that a living designer's hotel
> interiors can be reproduced. No BLINK data was used or invented.

## 1. Verdict

<!-- RESULTS: filled by the final section once the test phase is complete -->
See §8 (filled at the end of the run). The pre-registered criteria are in PRD §2.4 and the computed numbers in
`outputs/metrics.md`.

## 2. Corpus A — collection and rights

- Source: Library of Congress, HABS survey `hhh.il0039`, call number HABS ILL,16-CHIG,33-, 25 measured drawings
  (two drawing sets: sheets 1-1 … 1-14, 2-1, 3-1 … 3-10) and 9 photographs.
- Collected by `scripts/01_collect.py`: master TIFFs (≈9,650 × 7,616 px) for the drawings, 1,024-px JPEGs for the
  photographs; each resized to ≤1,568 px on the longest edge for analysis; sha256, pixel sizes and the item-page
  rights advisory recorded per item in `data/provenance_rights.csv`.
- Rights advisory on every item page, verbatim: "No known restrictions on images made by the U.S. Government;
  images copied from other sources may be restricted." All 25 drawings are U.S. Government HABS work → included.
  Three photographs are photocopies of 1911 published plates (Wasmuth) → excluded as "copied from other sources".
  Six 1963 HABS photographs → included but unused (photographs are corroboration only; no rule rests on one).
- The survey's written data pages (20 pp.) were fetched as text for attribution only; they are not learning material.
- Network note: at T0 the environment's network policy denied www.loc.gov and tile.loc.gov; the catalogue metadata was
  obtained through the Firecrawl tool, and the images were downloaded after the user opened the hosts.

## 3. Corpus B — skipped

Hugging Face `Pointcept/structured3d-compressed` is access-gated (login + terms acceptance). No credentials exist in
this session and the PRD forbids depending on the approval. **Consequence: the contrast pass (PRD §3.2) was not run;
the rule library is untested against a generic control.** `generic_rules_removed` is empty. See
`data/corpus_b_decision.md`.

## 4. Splits and briefs — frozen before any drawing was opened

- `data/splits.json`: seed 20261104; sheets grouped by subject so the two HABS sets' duplicates (e.g. 1-2 and 3-1
  first-floor plans) never straddle learning and test; stratified by drawing type; greedy assignment to 12 / 6 / 7.
  Learning: 1, 3, 5, 6, 7, 8, 12, 13, 17, 19, 20, 21. Iteration: 2, 11, 16, 22, 24, 25. Test: 4, 9, 10, 14, 15, 18, 23.
- `briefs/`: PRD §4.2–4.3 text, plus one neutral materials clause (identical for every brief) added at T0 to satisfy
  §4.1; machine-checkable thresholds in `briefs/briefs.json`. Frozen before extraction; unchanged since.
- Leakage guard: `scripts/02_extract.py` refuses to process test sheets outside the held-out check and flags any
  test-set extraction file that appears early. No leakage occurred (see §9).

## 5. Extraction (PRD §3.1)

- 18 sheets (12 learning + 6 iteration), one fresh isolated Fable subagent per sheet, instructed to open only that
  sheet's images and prompt. Two passes per sheet: a transcription pre-step (`prompts/transcribe_v1.txt`, reading
  full-resolution 4 × 3 tiles and, where needed, finer crops) and the PRD extraction prompt verbatim
  (`prompts/extract_v1.txt`) with the transcription embedded, answered from the 1,568-px sheet.
- Result: 18/18 transcriptions and 18/18 extractions schema-valid. 277 dimension strings transcribed verbatim
  (zero on sheets that carry none; up to 115 on the chair sheet). 365 images viewed. One retry (sheet 17 extraction:
  a null where the schema wants a string; no observation changed). Nothing flagged for manual review.
- Per-sheet attempts, images and notes: `data/extractions/*.meta.json`; stage log: `data/run_log.csv`.
- Deviation from PRD §7.2: Claude Haiku at temperature 0 was specified; the session model (Fable 5.1) ran every
  step with default sampling because no API was used (user instruction). Token counts per call are not available
  in-session; subagent totals are in the session transcript.

## 6. Rule library

- v1 (`outputs/rule_library_v1.json`): one fresh Fable subagent answered `prompts/aggregate_v1.txt` verbatim with the
  12 learning-set extractions embedded. 15 rules, 3–8 evidence sheets each, 6 do-not entries, 3 signature moves.
  Seven candidate rules were dropped for insufficient evidence (listed in `rule_library_v1.meta.json`).
- Evidence audit (`scripts/audit_evidence.py`): 81 evidence lines, every quoted phrase found verbatim in the cited
  sheet's extraction, every cited sheet quoted. 0 problems for v1 and v2.
- Iteration (PRD §3.3, `outputs/iteration_log.md`): no v1 rule was contradicted by the iteration drawings; the
  generated iteration designs showed the rules were written at whole-building scale. v2 appends one "At room
  scale: …" clause per rule (and to two do-not entries), each tied to the iteration sheet that motivated it; no
  evidence changed. v2 frozen before test generation.
- Anonymisation: the generation prompt embeds `rule_library_v2.generation.md`, in which the corpus name and any
  identifying words are withheld, so the learned arm is driven by the rules rather than by name recall.

## 7. Generation and checking

- Prompts: `prompts/generate_baseline_v2.txt` and `prompts/generate_learned_v2.txt` — identical except for the
  rules block (v2 fixed an ambiguous circulation sentence found in iteration; both arms changed identically).
- One fresh isolated Fable subagent per (brief, arm); it reads only its prompt and the spec schema, validates the JSON
  format once, and may not run the renderer or the checker. The orchestrator renders (`scripts/05_svg.py`, standard
  library only, same code path for both arms; arm and rule ids are never drawn) and checks (PRD §5.4, 8 checks,
  one violation per failed check).
- Checker fixes made during iteration (door-span clearance, dining-table reach, negated must-not terms, arrival
  zones at path ends) are listed in the iteration log; the scratch fixture's deliberate fault is still caught.

## 8. Results (test phase)

<!-- RESULTS: filled once outputs/metrics.md exists -->

## 9. Leakage, assumptions and deviations

- Leakage: none. Test sheets were first opened at the held-out check, after v2 was frozen and all six test designs
  were generated (`scripts/08_held_out_check.py` enforces this order).
- Assumptions (PRD §11): (1) split as above; (2) Corpus B skipped; (3) judges — see §8; (4) SVG path: Python
  standard library renderer `scripts/05_svg.py`, rasterised for judges with the pre-installed Chromium via
  Playwright (`scripts/svg2png.js`); (5) v2 is the evaluated library.
- Deviations: model tiers and temperatures (§5); Batch API and prompt caching not applicable in-session; images
  were tiled at full resolution for the transcription pre-step (the PRD extraction call itself used the 1,568-px
  sheet as specified).
