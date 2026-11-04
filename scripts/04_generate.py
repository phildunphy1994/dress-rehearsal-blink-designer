#!/usr/bin/env python3
"""04_generate.py — prepare and validate the design-generation stage (PRD §2.2, §5.1).

Generation is done IN-SESSION by the session model (Fable): one fresh, isolated subagent per (brief, arm). The
baseline subagent receives prompts/generate_baseline_v1.txt; the learned subagent receives
prompts/generate_learned_v1.txt (identical except for the rules block, which embeds the frozen, anonymised
rule library). This script:

  --prepare --phase iteration|test [--library outputs/rule_library_v2.json]
        writes outputs/designs/<brief>/<arm>/prompt.txt for every brief in the phase and both arms
  --validate --phase iteration|test
        validates every spec.json against schema/spec_schema.json, checks brief_id/arm fields, computes rule
        traceability for the learned arm (share of major decisions citing ≥1 rule id; share of cited rule ids that
        exist in the library), and writes outputs/traceability.csv
"""
import argparse, csv, json, sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
BRIEFS = json.load(open(ROOT / "briefs" / "briefs.json"))["briefs"]
SCHEMA = json.load(open(ROOT / "schema" / "spec_schema.json"))


def prepare(phase, library):
    schema_txt = json.dumps(SCHEMA, indent=1)
    lib_md = Path(library).with_suffix("").with_suffix("")  # strip .json
    gen_md = Path(str(library)[:-5] + ".generation.md")
    if not gen_md.exists():
        print("missing anonymised library", gen_md); sys.exit(1)
    for bid, b in BRIEFS.items():
        if b["phase"] != phase: continue
        brief_txt = (ROOT / "briefs" / f"{bid}.md").read_text()
        for arm in ("baseline", "learned"):
            tmpl = (ROOT / "prompts" / f"generate_{arm}_v1.txt").read_text()
            txt = tmpl.replace("{brief}", brief_txt).replace("{schema}", schema_txt)
            txt = txt.replace("{rules_block}\n", "") if arm == "baseline" else txt.replace("{rule_library}", gen_md.read_text())
            d = ROOT / "outputs" / "designs" / bid / arm
            d.mkdir(parents=True, exist_ok=True)
            (d / "prompt.txt").write_text(txt)
            print("prepared", d / "prompt.txt", f"({len(txt)} chars)")


def validate(phase, library):
    lib = json.loads(Path(library).read_text()) if Path(library).exists() else None
    rule_ids = {r["id"] for r in lib["rules"]} if lib else set()
    rows = []; ok = True
    for bid, b in BRIEFS.items():
        if b["phase"] != phase: continue
        for arm in ("baseline", "learned"):
            d = ROOT / "outputs" / "designs" / bid / arm
            f = d / "spec.json"
            if not f.exists():
                print(f"{bid}/{arm}: spec.json MISSING"); ok = False; continue
            try:
                spec = json.loads(f.read_text()); jsonschema.validate(spec, SCHEMA)
                assert spec["brief_id"] == bid and spec["arm"] == arm, "brief_id/arm mismatch"
                status = "valid"
            except Exception as e:  # noqa
                status = f"INVALID: {str(e)[:160]}"; ok = False; spec = None
            if spec:
                major = [x for x in spec["decision_log"] if x["major"]]
                cited = [x for x in major if x["rule_ids"]]
                all_ids = [r for x in spec["decision_log"] for r in x["rule_ids"]] + [r for f_ in spec["furniture"] for r in f_.get("rule_ids", [])] + [r for o in spec["openings"] for r in o.get("rule_ids", [])] + [r for p in spec["palette"] for r in p.get("rule_ids", [])]
                real = [r for r in all_ids if r in rule_ids]
                rows.append({"brief": bid, "arm": arm, "status": status, "major_decisions": len(major), "major_citing_rule": len(cited),
                             "share_major_cited": round(len(cited) / len(major), 3) if major else None,
                             "rule_citations": len(all_ids), "citations_to_real_rules": len(real),
                             "share_citations_real": round(len(real) / len(all_ids), 3) if all_ids else None,
                             "spec_md": (d / "spec.md").exists(), "conflicts": len(spec["conflicts"])})
            else:
                rows.append({"brief": bid, "arm": arm, "status": status})
            print(f"{bid}/{arm}: {status}")
    out = ROOT / "outputs" / f"traceability_{phase}.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["brief", "arm", "status", "major_decisions", "major_citing_rule", "share_major_cited", "rule_citations", "citations_to_real_rules", "share_citations_real", "spec_md", "conflicts"])
        w.writeheader(); [w.writerow(r) for r in rows]
    print("wrote", out)
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["iteration", "test"], required=True)
    ap.add_argument("--library", default="outputs/rule_library_v2.json")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.prepare: prepare(a.phase, ROOT / a.library)
    if a.validate: sys.exit(0 if validate(a.phase, ROOT / a.library) else 1)
