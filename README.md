# Dress rehearsal — learn a design language, generate new examples, test whether the learned rules help

A pre-registered before/after experiment: extract explicit, example-tied rules from a coherent set of measured
drawings (Corpus A: HABS survey of one house by one architect), generate new room designs for frozen briefs **with**
and **without** those rules, and compare the two arms blind on held-out briefs.

Outcome and verdict: see `outputs/run_report.md` (full record) and `outputs/discussion_pack.md` (Friday pack).

> **Limitation stated up front (PRD §0.2, §9.3):** this proves the *learning loop* on archival residential
> architecture. It does **not** prove that a living designer's hotel interiors can be reproduced. No BLINK data was
> used or invented.

## How the model steps are run

Every model step is run **in-session by the session model (Claude Fable 5.1)** — no API key, no SDK, no external
calls. Prompts are stored verbatim in `prompts/` and the exact prompt text sent for each sheet / brief is written to
disk before the step runs. Where isolation matters, a **fresh, isolated subagent** (same model, empty context) runs
the step so that:

- each drawing is extracted one-per-request without seeing any other drawing;
- the **baseline** generation arm never sees the rule library, and the **learned** arm sees it only through the
  frozen, anonymised one-pager;
- supplementary Claude judges never see the specs or the A/B key.

Deviation from PRD §7.2 (recorded in the run report): model tiers (Haiku / Sonnet) and temperatures (0 / 0.3) were
not used; the session model ran every step with identical default sampling in both arms.

## Pipeline

| Step | Script | Model step? | Output |
|---|---|---|---|
| 0 | `scripts/00_freeze_splits.py` | no | `data/splits.json` — seeded 12/6/7 split, frozen before any drawing was opened |
| 1 | `scripts/01_collect.py` | no | `corpus_a/` originals + `corpus_a/resized/` (≤1568 px), `data/provenance_rights.csv` |
| 2 | `scripts/02_extract.py --prepare/--validate`, `scripts/tiles.py` | yes (one subagent per sheet) | `data/transcriptions/*.json`, `data/extractions/*.json` + `.meta.json` |
| 3 | `scripts/03_aggregate.py --prepare/--validate/--render` | yes | `outputs/rule_library_v1.json/.md`, iteration → `v2` (frozen) |
| 4 | `scripts/04_generate.py --prepare/--validate` | yes (one subagent per brief × arm) | `outputs/designs/<brief>/<arm>/{prompt.txt,spec.json,spec.md}` |
| 5 | `scripts/05_svg.py render-all / check-all` | no | `plan.svg`, `elevation.svg`, `palette.svg`, `check_summary.json`, `outputs/violations.csv` |
| 6 | `scripts/06_blind.py --seed N` | judges | `outputs/blind/judge_pack.md` (+PNGs), `outputs/blind/KEY.json`, `outputs/blind_test_scores.csv` |
| 7 | `scripts/07_report.py` | no | `outputs/metrics.json/.md` → cited by `run_report.md`, `discussion_pack.md` |

Helpers: `scripts/svg2png.js` (rasterises SVGs with the pre-installed Chromium), `scripts/tiles.py` (full-resolution
tiles so a vision model can read dimension lettering; used for the transcription pre-step only).

## Re-running

```bash
pip install -r requirements.txt            # pillow, jsonschema (anthropic is listed only for an optional API re-run)
python3 scripts/00_freeze_splits.py        # refuses to overwrite the frozen split
python3 scripts/01_collect.py
python3 scripts/02_extract.py --phase learning --prepare
# model step: for each sheet, run prompts/transcribe_v1.txt then prompts/extract_v1.txt (see data/extraction_prompts/)
python3 scripts/02_extract.py --phase learning --validate
python3 scripts/03_aggregate.py --prepare  # model step: answer outputs/aggregate_prompt_v1.txt → outputs/rule_library_v1.json
python3 scripts/03_aggregate.py --validate outputs/rule_library_v1.json --render outputs/rule_library_v1.json
python3 scripts/04_generate.py --phase test --prepare --library outputs/rule_library_v2.json
# model step: answer each outputs/designs/<brief>/<arm>/prompt.txt → spec.json + spec.md
python3 scripts/04_generate.py --phase test --validate
python3 scripts/05_svg.py render-all && python3 scripts/05_svg.py check-all
python3 scripts/06_blind.py --seed 20261106 && python3 scripts/07_report.py
```

## Rights and provenance

Corpus A is Library of Congress HABS material (`HABS ILL,16-CHIG,33-`, survey `hhh.il0039`). Every item's rights
advisory is recorded verbatim in `data/provenance_rights.csv`; the three photocopied 1911 published plates are
excluded ("images copied from other sources may be restricted"). Internal rehearsal use with attribution only.
Corpus B (Structured3D) was not used — see the run report.
