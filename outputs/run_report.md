# Run report — Dress rehearsal: learn a design language, generate, test

Run date: 2026-11-04 (UTC). Executor: Claude Fable 5.1 running in a Claude Code cloud session on this repository
(branch `claude/stoic-maxwell-1np0zy`). Every model step was run in-session; no API key, SDK or external service was used.

> **Limitation (PRD §0.2, §9.3), stated first:** this run proves a learning loop on archival residential
> architecture (one architect, one house, measured drawings). It does **not** show that a living designer's hotel
> interiors can be reproduced. No BLINK data was used or invented.

## 1. Verdict

**PARTIAL PASS AT BEST — constraint criterion failed (floor effect: both arms 0 violations); human blind test not yet recorded; supplementary Claude-judge identification passes (cannot substitute for the human result).**

- Constraint criterion: **not met** (floor effect — baseline and learned both 0 violations on every test design).
- Blind criterion: **human result pending**; supplementary Claude judges 9/9 correct at confidence 5.
- Traceability: **met** (100% of major decisions cite a rule; 100% of citations are real rules).
- Held-out drawings: 14/15 rules supported by ≥2 unseen drawings; 1 partial contradiction (R14).
Full numbers: `outputs/metrics.md`; reading: §8.

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

### 8.1 Pre-registered criteria (PRD §2.4)

| Criterion | Pass bar | Measured | Result |
|---|---|---|---|
| Constraint violations (§5.4, 8 checks per design) | learned ≥ 2 fewer per design than baseline | baseline 0.00, learned 0.00 (every one of the 6 designs: 0) | **not met — floor effect** |
| Style consistency, blind (§6) | learned picked in ≥ 2 of 3 briefs by human judges | **human judges: not yet recorded** · supplementary Claude judges: 3 of 3 for each of 3 judges | **pending (human)** |
| Rule traceability | ≥ 80 % of major decisions cite a rule; 100 % of cited rules exist | 46/46 major decisions = 100%; 272/272 citations real = 100% | **met** |
| Reproducibility | fresh executor can re-run from PRD + repo | scripts, prompts, splits, seeds, versions and logs all in the repo (README) | **met** |

**Verdict: PARTIAL PASS AT BEST — constraint criterion failed (floor effect: both arms 0 violations); human blind test not yet recorded; supplementary Claude-judge identification passes (cannot substitute for the human result).** Under the pre-registered rules this cannot become a full PASS even with a perfect human
result, because the constraint criterion is unreachable when the baseline already scores 0: the metric did not
discriminate, which is itself a finding (see 8.5). If the human blind test passes, the result is a **partial pass**
(blind criterion met, constraint criterion not met); if it fails, the result is a **fail** under §2.4.

### 8.2 Constraint violations (test briefs)

All six test designs pass all eight checks. `outputs/violations.csv` holds the 48 rows. Check-7 do-not-list review of
the learned arm is recorded in `outputs/manual_checks.json` (no violations; every hit is a compliance statement).

### 8.3 Blind test

Pack: `outputs/blind/judge_pack.md` (brief text + stripped plan, elevation and palette PNGs per set; no specs).
A/B key (`outputs/blind/KEY.json`, seed 20261106, recorded coin per brief): test_a → A baseline / B learned;
test_b → A learned / B baseline; test_c → A learned / B baseline.

*Human judges (primary):* not yet run. Procedure for before Friday: two people, at least one who has not seen the
rule library or any spec, each spend ~15 minutes on `outputs/blind/judge_pack.md` and record one row per pair in
`outputs/blind_test_scores.csv` (`judge_type = human`; leave `correct` empty, it is computed from the key; map the
reason to a rule id or `null` after scoring), then run `python3 scripts/07_report.py`. The first score stands (§6.5).

*Supplementary Claude judges (cannot substitute for or overturn the human result):* three fresh, isolated Fable
agents that saw only the judge pack. Each identified the rule-following set in 3/3 pairs at confidence 5
(confidence-weighted score 1.00); 9/9 reasons name a real library rule (R03 hearth core, R07
casement ribbon between piers, R08 horizontal brick coursing with light cap bands). Rows in `outputs/blind_test_scores.csv`.

### 8.4 Held-out drawing check (PRD §6.4)

Seven test-set drawings (opened for the first time after v2 was frozen and all six test designs existed), one fresh
agent per sheet, each rule marked supported / contradicted / not assessable from that sheet alone
(`data/held_out/*.json`, summary `outputs/held_out_check.json`):

- 93% of rules (14/15) are supported by at least one held-out drawing, and the same 14 by at least two.
- Contradicted: 7% (1/15): R14 (stacked rectangular layers, no curved profile) is supported by three
  held-out sheets but partially contradicted by sheet 15, where the dining-table post foot flares in a concave curve.
- Not assessable anywhere: R15 (framed infill panels, a "sometimes" rule); no held-out sheet shows a top-storey band.
- Rules supported per sheet: sheet 4: 8, sheet 9: 1, sheet 10: 10, sheet 14: 1, sheet 15: 1, sheet 18: 8, sheet 23: 11 (the detail sheets 9, 14, 15 can each assess only one rule).
- Do-not list: every entry is supported by 2–4 held-out sheets and contradicted by none.

### 8.5 Reading the result

1. **The rules change what the model designs, and judges can see it.** The learned designs are recognisably built
   from the library (brick hearth mass on an internal wall, casement ribbons between piers on a module, light cap
   bands on every masonry edge, stacked-slab joinery, flush entry into a compressed vestibule) while the baselines
   are competent contemporary rooms; three independent Claude judges separated them 9/9 at full confidence. This is
   the supplementary evidence; the human blind test is the primary one and is still owed.
2. **The constraint metric cannot discriminate on these briefs.** A frontier model given a precise, checkable brief
   satisfies every §5.4 check without any rules, in both arms, on all five briefs it was given (2 iteration + 3
   test). "Fewer violations" is the wrong lever for measuring taste; the metric still earns its place as a buildability
   gate. A future version should pre-register a style-specific checklist (derived from the do-not list) alongside it.
3. **The rulebook generalises within the corpus.** 14/15 rules are visible in drawings the extraction never saw;
   the one partial contradiction (a curved post foot) is exactly the kind of exception a designer would annotate.
4. **No control corpus.** Because Corpus B was gated, nothing here shows that the rules are specific to this
   architect rather than to good practice of the period; the contrast pass remains to be done.

## 9. Leakage, assumptions and deviations

- Leakage: none. Test sheets were first opened at the held-out check, after v2 was frozen and all six test designs
  were generated (`scripts/08_held_out_check.py` enforces this order).
- Assumptions (PRD §11): (1) split as above; (2) Corpus B skipped; (3) judges — no human judge was available during the run; the pack is ready and the procedure is in §8.3; (4) SVG path: Python
  standard library renderer `scripts/05_svg.py`, rasterised for judges with the pre-installed Chromium via
  Playwright (`scripts/svg2png.js`); (5) v2 is the evaluated library.
- Deviations: model tiers and temperatures (§5); Batch API and prompt caching not applicable in-session; images
  were tiled at full resolution for the transcription pre-step (the PRD extraction call itself used the 1,568-px
  sheet as specified).
