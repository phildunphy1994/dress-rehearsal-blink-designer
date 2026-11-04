#!/usr/bin/env python3
"""03_aggregate.py — prepare and validate the rule-library aggregation (PRD §3.2).

The synthesis itself is done IN-SESSION by the session model (Fable) using prompts/aggregate_v1.txt verbatim.

  --prepare            writes outputs/aggregate_prompt_v1.txt = aggregate_v1.txt with {extractions_json} = all
                       LEARNING-set extractions (and nothing else — leakage guard)
  --validate FILE      validates a rule library JSON: schema, 10–15 rules, ≥3 evidence sheets per rule, every cited
                       sheet id is a LEARNING-set sheet (iteration sheets allowed only for v2 counter-examples),
                       no rule rests on a photograph; prints a traceability table
  --render FILE        writes the one-page markdown next to FILE (rule_library_vN.md) and an anonymised copy
                       rule_library_vN.generation.md with the corpus / designer name removed (used in the generation
                       prompt so the learned arm is driven by the rules, not by name recall)
"""
import argparse, json, re, sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SPLITS = json.load(open(ROOT / "data" / "splits.json"))
SCHEMA = json.load(open(ROOT / "schema" / "rule_library_schema.json"))
LEARN = [s["sheet_id"] for s in SPLITS["learning"]]
ITER = [s["sheet_id"] for s in SPLITS["iteration"]]
TEST = [s["sheet_id"] for s in SPLITS["test"]]


def prepare():
    ex = []
    for sid in LEARN:
        f = ROOT / "data" / "extractions" / f"{sid}.json"
        if not f.exists():
            print("MISSING extraction for learning sheet", sid); sys.exit(1)
        ex.append(json.loads(f.read_text()))
    tmpl = open(ROOT / "prompts" / "aggregate_v1.txt").read()
    out = ROOT / "outputs" / "aggregate_prompt_v1.txt"
    out.write_text(tmpl.replace("{extractions_json}", json.dumps(ex, indent=1, ensure_ascii=False)))
    print(f"wrote {out} with {len(ex)} learning-set extractions ({sum(len(json.dumps(e)) for e in ex)} chars)")


def validate(path: Path, allow_iteration_counterexamples=False):
    lib = json.loads(path.read_text())
    jsonschema.validate(lib, SCHEMA)
    problems = []
    for r in lib["rules"]:
        ev = r["evidence_sheet_ids"]
        if len(set(ev)) < 3: problems.append(f"{r['id']}: fewer than 3 distinct evidence sheets")
        for s in ev:
            if s in TEST: problems.append(f"{r['id']}: cites TEST sheet {s} — LEAKAGE")
            elif s not in LEARN: problems.append(f"{r['id']}: evidence {s} is not a learning-set sheet")
            if ".photos." in s: problems.append(f"{r['id']}: rests on a photograph {s}")
        for s in r["counter_example_sheet_ids"]:
            if s in TEST: problems.append(f"{r['id']}: counter-example cites TEST sheet {s} — LEAKAGE")
            if s in ITER and not allow_iteration_counterexamples: problems.append(f"{r['id']}: counter-example from iteration set in v1")
    ids = [r["id"] for r in lib["rules"]]
    if ids != [f"R{i:02d}" for i in range(1, len(ids) + 1)]: problems.append("rule ids are not R01..Rnn in order")
    if lib["drawing_count"] != len(LEARN): problems.append(f"drawing_count {lib['drawing_count']} != {len(LEARN)} learning sheets")
    print(f"{path.name}: {len(lib['rules'])} rules; evidence per rule: " + ", ".join(f"{r['id']}={len(set(r['evidence_sheet_ids']))}" for r in lib["rules"]))
    for p in problems: print("  PROBLEM:", p)
    return not problems


def render(path: Path):
    lib = json.loads(path.read_text())
    lines = [f"# Rule library {path.stem.split('_')[-1]} — {lib['corpus']}", "",
             f"Learning set: {lib['drawing_count']} measured drawings. Each rule cites ≥3 learning-set sheets (ids are HABS sheet numbers).", "",
             "| id | rule | freq | evidence (n) |", "|---|---|---|---|"]
    for r in lib["rules"]:
        ev = ", ".join(s.split(".")[-1].lstrip("0") for s in r["evidence_sheet_ids"])
        lines.append(f"| {r['id']} | **{r['title']}** — {r['statement']} | {r['frequency']} | {len(r['evidence_sheet_ids'])}: sheets {ev} |")
    lines += ["", "## Do-not list", *[f"- {d}" for d in lib["do_not_list"]],
              "", "## Palette", f"- Dominant: {', '.join(lib['palette_summary']['dominant'])}", f"- Accent: {', '.join(lib['palette_summary']['accent'])}", f"- Temperature: {lib['palette_summary']['warm_or_cool']}",
              "", "## Materials", *[f"- {m}" for m in lib["material_summary"]],
              "", "## Proportions", *[f"- {p}" for p in lib["proportion_summary"]],
              "", "## Signature moves", *[f"{i+1}. {m}" for i, m in enumerate(lib["signature_moves"])],
              "", "## Generic rules removed (contrast pass)", *([f"- {g}" for g in lib["generic_rules_removed"]] or ["- (contrast pass not run: Corpus B skipped; library untested against a generic control)"])]
    md = "\n".join(lines) + "\n"
    (path.parent / f"{path.stem}.md").write_text(md)
    # anonymised copy for the generation prompt
    anon = md.replace(lib["corpus"], "Corpus A (one designer, one building; name withheld)")
    anon = re.sub(r"(?i)frank\s+lloyd\s+wright|wright|robie|prairie|habs|chicago", "[withheld]", anon)
    (path.parent / f"{path.stem}.generation.md").write_text(anon)
    print("wrote", path.parent / f"{path.stem}.md", "and", path.parent / f"{path.stem}.generation.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--validate", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--v2", action="store_true", help="allow iteration-set counter-examples (rule library v2)")
    a = ap.parse_args()
    if a.prepare: prepare()
    ok = True
    if a.validate: ok = validate(Path(a.validate), allow_iteration_counterexamples=a.v2)
    if a.render: render(Path(a.render))
    sys.exit(0 if ok else 1)
